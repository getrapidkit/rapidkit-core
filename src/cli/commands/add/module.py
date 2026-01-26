# src / cli / commands / add / module.py
import importlib.util
import inspect
import json
import os
import re
import shutil
import sys
import tempfile
import time
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast

import typer
import yaml
from typer.models import OptionInfo

from core.engine.dependency_installer import install_module_dependencies
from core.hooks.framework_handlers import (
    handle_fastapi_router,
    handle_nestjs_module,
)
from core.rendering.template_renderer import render_template
from core.services.config_loader import load_module_config
from core.services.extras_copier import copy_extra_files, ensure_init_files
from core.services.file_hash_registry import (
    _sha256,
    file_was_modified,
    load_hashes,
    record_file_hash,
    save_hashes,
)
from core.services.import_organizer import organize_imports
from core.services.module_manifest import (
    ModuleManifest,
    compute_install_order,
    load_all_manifests,
    load_manifest_or_none,
)
from core.services.module_path_resolver import resolve_module_directory
from core.services.module_structure_validator import (
    ModuleStructureError,
    ensure_module_structure,
)
from core.services.profile_utils import resolve_profile_chain
from core.services.project_metadata import load_project_metadata
from core.services.snippet_injector import (
    inject_snippet_enterprise,
    reconcile_pending_snippets_scoped,
    remove_inject_anchors,
)
from core.services.summary import build_minimal_config_summary
from core.services.translation_utils import process_translations
from core.services.vendor_store import store_vendor_file
from modules.free import get_registry

from ...ui.printer import (
    console as _console,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from ...utils.filesystem import create_file, find_project_root, resolve_project_path
from ...utils.pathing import (
    resolve_modules_path,
    resolve_registry_path,
    resolve_repo_root,
    resolve_src_root,
)
from ...utils.registry import update_registry
from ...utils.variables_prompt import prompt_for_variables
from ..module_gating import enforce_module_gating


def _load_installed_module_slugs(project_root: Path) -> set[str]:
    """Return installed module slugs from registry.json.

    We treat registry.json as the source of truth for which RapidKit modules
    have been installed into the project.
    """

    registry_path = project_root / "registry.json"
    if not registry_path.exists():
        return set()
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    installed_raw = payload.get("installed_modules", []) if isinstance(payload, dict) else []
    slugs: set[str] = set()
    if not isinstance(installed_raw, list):
        return slugs
    for entry in installed_raw:
        if isinstance(entry, str) and entry.strip():
            slugs.add(entry.strip())
        elif isinstance(entry, dict):
            slug = entry.get("slug") or entry.get("module") or entry.get("name")
            if isinstance(slug, str) and slug.strip():
                slugs.add(slug.strip())
    return slugs


_STATUS_BLOCKLIST = {"planned", "placeholder"}
_STATUS_CAUTION = {"experimental", "beta"}
_STATUS_WARN = {"draft", "deprecated"}

# Resolve repo paths so the CLI works both from source and installed packages
REPO_ROOT = resolve_repo_root(Path(__file__).resolve())
MODULES_PATH = resolve_modules_path()
REGISTRY_PATH = resolve_registry_path()

FastapiHandler = Callable[[str, Path], None]
NestHandler = Callable[[Path, str, str], None]
FrameworkHandler = Union[FastapiHandler, NestHandler]
FRAMEWORK_HANDLERS: Dict[str, FrameworkHandler] = {
    "fastapi": handle_fastapi_router,
    "nestjs": handle_nestjs_module,
}


def _inject_module_imports(
    project_root: Path, module_slug: str, anchor: str = "# <<<inject:module-init>>>"
) -> None:
    """Inject explicit imports for a module into src/modules/__init__.py.

    This is used to surface installed modules to end-users, matching the
    documented pattern ``from src.modules.<tier>.<category>.<module> import ...``.
    It discovers
    the module's primary python file, loads its ``__all__`` symbols, and writes
    a single import line above the module-init anchor. Idempotent: skips when
    line already present or when __all__ is empty.
    """

    modules_init = project_root / "src" / "modules" / "__init__.py"
    if not modules_init.exists():
        return

    slug = module_slug.strip().strip("/")
    segments = [part for part in slug.split("/") if part]

    # Prefer new layout: src/modules/<tier>/<category>/<slug>
    modules_pkg = project_root / "src" / "modules"
    pkg_path = modules_pkg.joinpath(*segments) if segments else None

    candidates: list[tuple[str, Path]] = []
    if pkg_path is not None:
        # In kit projects, `src` is a Python package (sys.path includes project root),
        # so module code is importable as `src.modules.<tier>.<category>.<slug>`.
        dotted = "src.modules." + ".".join(segments)
        candidates.extend(
            [
                (dotted, pkg_path / "__init__.py"),
                (dotted, pkg_path / f"{segments[-1]}.py"),
            ]
        )

    module_path: Path | None = None
    module_import: str | None = None
    for dotted, path in candidates:
        if path.exists():
            module_path = path
            module_import = dotted
            break

    if module_path is None or module_import is None:
        return

    symbols_list: list[str] = []

    # Preferred: import module and read __all__
    try:
        spec = importlib.util.spec_from_file_location(module_import, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            symbols = getattr(module, "__all__", None)
            if symbols:
                symbols_list = [s for s in symbols if isinstance(s, str) and s.strip()]
    except (ImportError, OSError, AttributeError, ValueError, SyntaxError):
        symbols_list = []

    # Fallback: static parse __all__ assignment without executing module
    if not symbols_list:
        try:
            import ast

            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "__all__":
                            value = ast.literal_eval(node.value)
                            if isinstance(value, (list, tuple)):
                                symbols_list = [
                                    s for s in value if isinstance(s, str) and s.strip()
                                ]
                            break
                if symbols_list:
                    break
        except (OSError, SyntaxError, ValueError):
            symbols_list = []

    import_line: str
    if symbols_list:
        MAX_INLINE_IMPORTS = 3
        sorted_symbols = sorted(dict.fromkeys(symbols_list))
        if len(sorted_symbols) <= MAX_INLINE_IMPORTS:
            import_line = f"from {module_import} import {', '.join(sorted_symbols)}"
        else:
            joined = ",\n    ".join(sorted_symbols)
            import_line = f"from {module_import} import (\n    {joined},\n)"
    else:
        # Fall back to a plain import when __all__ is unavailable
        import_line = f"import {module_import}"

    try:
        content = modules_init.read_text(encoding="utf-8")
    except OSError:
        return

    if import_line in content:
        return

    if anchor not in content:
        return

    updated = content.replace(anchor, import_line + "\n" + anchor, 1)
    try:
        modules_init.write_text(updated, encoding="utf-8")
    except OSError:
        return


@lru_cache(maxsize=None)
def _discover_module_slugs(raw_name: str) -> List[str]:
    normalized = raw_name.strip().strip("/")
    if not normalized:
        return []

    direct_path = MODULES_PATH / normalized
    if direct_path.is_dir() and (direct_path / "module.yaml").exists():
        try:
            return [direct_path.relative_to(MODULES_PATH).as_posix()]
        except ValueError:
            return []

    matches: Set[str] = set()
    pattern = f"**/{normalized}/module.yaml"
    for manifest_path in MODULES_PATH.glob(pattern):
        parent = manifest_path.parent
        if not parent.is_dir():
            continue
        try:
            rel = parent.relative_to(MODULES_PATH).as_posix()
        except ValueError:
            continue
        matches.add(rel)

    return sorted(matches)


def _load_module_generator(module_dir: Path) -> ModuleType:
    """Dynamically import a module generator script."""

    try:
        relative_name = module_dir.relative_to(MODULES_PATH).as_posix().replace("/", ".")
    except ValueError:
        relative_name = None

    if relative_name:
        module_name = f"modules.{relative_name}.generate"
        try:
            return import_module(module_name)
        except ImportError:
            relative_name = None

    generator_path = module_dir / "generate.py"
    if not generator_path.exists():
        raise RuntimeError("Module declares generation config but was missing generate.py")

    src_root = resolve_src_root()
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    spec = importlib.util.spec_from_file_location(
        f"_rapidkit_module_generator_{abs(hash(str(generator_path)))}",
        generator_path,
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"Unable to load generator at {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _collect_generated_health_entries(
    tmp_path: Path,
    existing_entries: List[Any],
) -> List[Dict[str, str]]:
    """Detect health scaffolding artifacts emitted during generation.

    Module generators write health registries and vendor-backed shims via helper
    utilities that operate directly on the temporary output directory. Because
    these files are not declared explicitly in ``module.yaml`` they would be
    skipped by the standard variant file loop, leaving a project without the
    expected ``src/health/<module>.py`` shims. To keep copy + hashing logic
    consistent we discover every canonical ``src/health`` artifact and return
    synthetic entries so the normal pipeline copies them just like declared
    files.
    """

    outputs: Set[str] = set()
    for entry in existing_entries:
        if not isinstance(entry, dict):
            continue
        output = entry.get("output")
        if isinstance(output, str):
            outputs.add(output)

    discovered: List[Dict[str, str]] = []

    def _record_candidate(path: Path) -> None:
        rel_path = path.relative_to(tmp_path).as_posix()
        if rel_path in outputs:
            return
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return
        if not content.strip():
            return
        discovered.append({"output": rel_path, "_health_scaffold": "1"})

    health_root = tmp_path / "src" / "health"
    if health_root.exists():
        for candidate in sorted(health_root.rglob("*.py")):
            if "__pycache__" in candidate.parts or not candidate.is_file():
                continue
            _record_candidate(candidate)

    src_root = tmp_path / "src"
    if src_root.exists():
        for pattern in ("*.health.ts", "*.health.js", "*.health.jsx", "*.health.tsx"):
            for candidate in sorted(src_root.rglob(pattern)):
                if not candidate.is_file():
                    continue
                if "node_modules" in candidate.parts:
                    continue
                _record_candidate(candidate)

    return discovered


def _apply_generated_module(
    module_dir: Path,
    project_root: Path,
    generation_cfg: Dict[str, Any],
    variant_key: str,
    variables: Dict[str, Any],
    plan: bool,
    force: bool,
    update: bool,
    manifest: Optional[ModuleManifest],
    vendor_module_name: str,
    vendor_module_version: str,
    hash_registry: Dict[str, Any],
    created_files: List[str],
    overwritten_files: List[str],
    skipped_files: List[str],
    modified_conflicts: List[str],
    hard_failures: List[str],
) -> None:
    try:
        generator_module = _load_module_generator(module_dir)
    except Exception as exc:
        raise RuntimeError(f"Unable to load generator: {exc}") from exc

    variants_cfg = generation_cfg.get("variants") or {}
    if variant_key not in variants_cfg:
        available = ", ".join(sorted(variants_cfg)) or "<none>"
        raise RuntimeError(
            f"Variant '{variant_key}' not defined in module.yaml (available: {available})"
        )
    variant_cfg = variants_cfg[variant_key]

    vendor_cfg = generation_cfg.get("vendor") or {}

    if "project_name" not in variables or not variables["project_name"]:
        variables["project_name"] = project_root.name

    with tempfile.TemporaryDirectory(prefix="rapidkit-module-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_data = generator_module.load_module_config()
        base_context = generator_module.build_base_context(config_data)
        base_context.setdefault("project_name", variables["project_name"])
        for key, value in variables.items():
            base_context.setdefault(key, value)

        vendor_runtime_hint = base_context.get(
            "rapidkit_vendor_runtime_relative"
        ) or base_context.get("rapidkit_vendor_relative_path")
        if vendor_runtime_hint:
            base_context.setdefault("vendor_runtime_relative", vendor_runtime_hint)

        renderer_factory = getattr(generator_module, "TemplateRenderer", None)
        if renderer_factory is None:
            raise RuntimeError("Generator missing TemplateRenderer helper")
        try:
            renderer = renderer_factory(module_dir)
        except TypeError:
            # Backwards compatibility with modules that still expose zero-arg initialiser
            renderer = renderer_factory()

        # Inform the generator which target framework we're installing into
        # so vendor generation can be filtered appropriately even though the
        # work happens inside a temporary directory.
        base_context.setdefault("target_framework", variant_key)
        generator_module.generate_vendor_files(config_data, tmp_path, renderer, base_context)

        variant_callable = getattr(generator_module, "generate_variant_files", None)
        if variant_callable is None:
            raise RuntimeError("Generator missing generate_variant_files helper")

        try:
            signature = inspect.signature(variant_callable)
        except (TypeError, ValueError):
            signature = None

        positional_config_names = {"config", "module_config", "module_cfg"}
        if signature is not None:
            params = list(signature.parameters.values())
            if (
                params
                and params[0].kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
                and params[0].name in positional_config_names
            ):
                variant_callable(config_data, variant_key, tmp_path, renderer, base_context)
            else:
                variant_callable(variant_key, tmp_path, renderer, base_context)
        else:  # pragma: no cover - defensive fallback when signature introspection fails
            try:
                variant_callable(variant_key, tmp_path, renderer, base_context)
            except TypeError as exc:
                if "required positional argument" not in str(exc):
                    raise
                variant_callable(config_data, variant_key, tmp_path, renderer, base_context)

        vendor_module = str(base_context.get("rapidkit_vendor_module", vendor_module_name))
        vendor_version = str(base_context.get("rapidkit_vendor_version", vendor_module_version))

        framework = variant_key.split(".", 1)[0].strip().lower()
        try:
            module_slug = module_dir.relative_to(MODULES_PATH).as_posix().strip().strip("/")
        except ValueError:
            module_slug = vendor_module_name.strip().strip("/")

        def _canonicalize_health_outputs(*, tmp_root: Path, slug: str, framework_name: str) -> None:
            if not slug:
                return

            module_base = tmp_root / "src" / "modules" / Path(*slug.split("/"))
            if not module_base.exists():
                return

            if framework_name == "fastapi":
                # Canonical FastAPI rule: module health artifacts must not live
                # under `src/modules/<slug>/health/**`.
                try:
                    from modules.shared.utils.health import (
                        ensure_health_package,
                        ensure_vendor_health_shim,
                    )
                    from modules.shared.utils.health_specs import build_standard_health_spec

                    ensure_health_package(tmp_root)
                    spec = build_standard_health_spec(module_dir)
                    ensure_vendor_health_shim(tmp_root, spec=spec)
                except Exception:  # noqa: BLE001
                    # Best-effort: shim creation should not break installs.
                    pass

                health_dir = module_base / "health"
                if health_dir.exists() and health_dir.is_dir():
                    shutil.rmtree(health_dir, ignore_errors=True)
                return

            if framework_name == "nestjs":
                # Canonical NestJS rule: health artifacts must not live under
                # `src/modules/<slug>/**`.
                health_root = tmp_root / "src" / "health"
                health_root.mkdir(parents=True, exist_ok=True)

                def _rewrite_relative_imports(*, old_path: Path, new_path: Path) -> None:
                    try:
                        content = new_path.read_text(encoding="utf-8")
                    except OSError:
                        return

                    def _swap(spec: str) -> str:
                        if not spec.startswith("."):
                            return spec
                        target_abs = (old_path.parent / spec).resolve(strict=False)
                        try:
                            new_spec = os.path.relpath(str(target_abs), start=str(new_path.parent))
                        except ValueError:
                            return spec
                        new_spec = new_spec.replace("\\\\", "/")
                        if not new_spec.startswith("."):
                            new_spec = "./" + new_spec
                        return new_spec

                    pattern = re.compile(
                        r"(from\s+['\"])([^'\"]+)(['\"])|(require\(\s*['\"])([^'\"]+)(['\"]\s*\))"
                    )

                    def _repl(match: Any) -> str:
                        if match.group(1) is not None:
                            return f"{match.group(1)}{_swap(match.group(2))}{match.group(3)}"
                        return f"{match.group(4)}{_swap(match.group(5))}{match.group(6)}"

                    updated = pattern.sub(_repl, content)
                    if updated != content:
                        try:
                            new_path.write_text(updated, encoding="utf-8")
                        except OSError:
                            return

                def _move_or_delete(path: Path) -> None:
                    dest = health_root / path.name
                    if dest.exists():
                        try:
                            path.unlink()
                        except OSError:
                            return
                        return
                    try:
                        shutil.move(str(path), str(dest))
                    except OSError:
                        return
                    _rewrite_relative_imports(old_path=path, new_path=dest)

                for candidate in sorted(module_base.glob("**/*.health.ts")):
                    if candidate.is_file():
                        _move_or_delete(candidate)
                for suffix in ("*-health.controller.ts", "*-health.module.ts"):
                    for candidate in sorted(module_base.glob(f"**/{suffix}")):
                        if candidate.is_file():
                            _move_or_delete(candidate)

                for health_dir in sorted(module_base.glob("**/health")):
                    if health_dir.is_dir():
                        shutil.rmtree(health_dir, ignore_errors=True)

        _canonicalize_health_outputs(tmp_root=tmp_path, slug=module_slug, framework_name=framework)

        vendor_bytes_map: Dict[str, bytes] = {}
        vendor_root = Path(vendor_cfg.get("root", ".rapidkit/vendor"))
        for entry in vendor_cfg.get("files", []):
            rel_path = entry.get("relative")
            if not isinstance(rel_path, str) or not rel_path:
                continue
            vendor_path = tmp_path / vendor_root / vendor_module / vendor_version / rel_path
            if not vendor_path.exists():
                print_warning(f"⚠️ Generated vendor file missing: {vendor_path}")
                continue
            try:
                data = vendor_path.read_bytes()
            except OSError as exc:  # pragma: no cover - defensive
                print_warning(f"⚠️ Unable to read vendor artifact {vendor_path}: {exc}")
                continue
            vendor_bytes_map[rel_path] = data
            vendor_bytes_map[Path(rel_path).as_posix()] = data

        variant_root = Path(variant_cfg.get("root", "."))
        variant_files_raw = variant_cfg.get("files", []) or []
        variant_files = list(variant_files_raw)

        # Discover canonical health outputs under `src/health/**` after
        # canonicalization so they are copied like normal variant outputs.
        variant_files.extend(_collect_generated_health_entries(tmp_path, variant_files))

        # Enforce canonical health layout at copy-time by removing any entries
        # that still target module-local health paths.
        if module_slug:
            module_prefix = f"src/modules/{module_slug}/"

            def _is_forbidden_health_output(output_rel: str) -> bool:
                norm = output_rel.replace("\\", "/")
                if not norm.startswith(module_prefix):
                    return False
                if "/health/" in norm:
                    return True
                if norm.endswith(".health.ts"):
                    return True
                return False

            variant_files = [
                entry
                for entry in variant_files
                if not (
                    isinstance(entry, dict)
                    and isinstance(entry.get("output"), str)
                    and _is_forbidden_health_output(entry["output"])
                )
            ]
        for entry in variant_files:
            output_rel = entry.get("output") if isinstance(entry, dict) else None
            if not isinstance(output_rel, str) or not output_rel:
                continue

            generated_path = tmp_path / variant_root / output_rel
            if not generated_path.exists():
                # Some module generators assume parent dirs exist when writing outputs.
                # Fail-closed, but attempt one deterministic recovery by rendering the
                # template directly into the temp workspace.
                if isinstance(entry, dict):
                    template_rel = entry.get("template")
                    if isinstance(template_rel, str) and template_rel:
                        template_exceptions: tuple[type[BaseException], ...] = (
                            OSError,
                            ValueError,
                            TypeError,
                            AttributeError,
                            ImportError,
                            UnicodeError,
                        )
                        try:
                            from jinja2.exceptions import TemplateError as _JinjaTemplateError

                            template_exceptions = (*template_exceptions, _JinjaTemplateError)
                        except ImportError:  # pragma: no cover
                            pass

                        try:
                            generated_path.parent.mkdir(parents=True, exist_ok=True)
                            rendered = renderer.render(Path(template_rel), base_context)
                            generated_path.write_text(rendered, encoding="utf-8")
                        except template_exceptions:
                            pass
            if not generated_path.exists():
                print_error(f"❌ Generated variant file missing: {generated_path}")
                hard_failures.append(f"missing generated artifact: {output_rel}")
                continue

            try:
                new_text = generated_path.read_text(encoding="utf-8")
            except OSError as exc:
                print_error(f"❌ Failed to read generated artifact {generated_path}: {exc}")
                hard_failures.append(f"failed to read generated artifact: {output_rel}")
                continue
            new_bytes = new_text.encode("utf-8")

            destination_path = project_root / variant_root / output_rel
            rel_record_path = str(destination_path.relative_to(project_root))
            normalized_rel_key = rel_record_path.replace(os.sep, "/")

            existed_before = destination_path.exists()
            existing_bytes = b""
            if existed_before:
                try:
                    existing_bytes = destination_path.read_bytes()
                except OSError:
                    existing_bytes = b""

            entry_meta = hash_registry.get("files", {}).get(rel_record_path)
            tracked_hash = entry_meta.get("hash") if isinstance(entry_meta, dict) else None
            was_tracked = isinstance(entry_meta, dict)
            locally_modified = bool(
                existed_before and file_was_modified(hash_registry, rel_record_path, existing_bytes)
            )
            template_changed = True if not tracked_hash else tracked_hash != _sha256(new_bytes)

            previous_hash: Optional[str] = None
            if force:
                if tracked_hash:
                    previous_hash = tracked_hash
                elif existed_before and existing_bytes:
                    previous_hash = _sha256(existing_bytes)
            elif update:
                if locally_modified:
                    print_warning(
                        f"✋ Local changes detected, skipping (update mode): {rel_record_path}"
                    )
                    modified_conflicts.append(rel_record_path)
                    continue
                if not template_changed:
                    print_info(f"⏭ Up-to-date: {rel_record_path}")
                    skipped_files.append(rel_record_path)
                    continue
            elif locally_modified:
                print_warning(f"✋ Local changes detected, skipping overwrite: {rel_record_path}")
                modified_conflicts.append(rel_record_path)
                continue

            if plan:
                action = "overwrite" if existed_before else "create"
                print_info(
                    f"[cyan]{action.upper():9}[/cyan] {rel_record_path}  [dim]generator[/dim]"
                )
                continue

            try:
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                ensure_init_files(destination_path, project_root)
                create_file(destination_path, new_text)
            except OSError as exc:
                print_error(f"❌ Failed to write {destination_path}: {exc}")
                hard_failures.append(f"failed to write generated output: {output_rel}")
                continue

            record_file_hash(
                hash_registry,
                rel_record_path,
                vendor_module,
                vendor_version,
                new_bytes,
                previous_hash=previous_hash,
                snapshot=True,
                project_root=project_root,
            )

            vendor_payload = (
                vendor_bytes_map.get(rel_record_path)
                or vendor_bytes_map.get(normalized_rel_key)
                or new_bytes
            )
            if manifest and manifest.version:
                try:
                    store_vendor_file(
                        project_root,
                        vendor_module,
                        vendor_version,
                        normalized_rel_key,
                        vendor_payload,
                    )
                except OSError as exc:
                    print_warning(f"⚠️ Failed to write vendor snapshot {normalized_rel_key}: {exc}")

            if was_tracked:
                overwritten_files.append(rel_record_path)
                print_success(f"♻️  Overwritten: {rel_record_path}")
            else:
                created_files.append(rel_record_path)
                print_success(f"✅ Created: {rel_record_path}")

        if plan or not vendor_cfg:
            return

        stored_paths: Set[str] = set()
        for rel_path in created_files + overwritten_files:
            stored_paths.add(rel_path.replace(os.sep, "/"))

        for rel_path, payload in vendor_bytes_map.items():
            rel_key = rel_path.replace(os.sep, "/")
            if rel_key in stored_paths:
                continue
            try:
                store_vendor_file(
                    project_root,
                    vendor_module,
                    vendor_version,
                    rel_key,
                    payload,
                )
            except OSError as exc:
                print_warning(f"⚠️ Failed to cache vendor artifact {rel_key}: {exc}")


@lru_cache(maxsize=None)
def _registry_getters() -> Dict[str, Callable[[], Any]]:
    getters: Dict[str, Callable[[], Any]] = {"free": get_registry}
    for tier_dir in MODULES_PATH.iterdir():
        if not tier_dir.is_dir():
            continue
        tier_name = tier_dir.name
        if tier_name in getters or tier_name.startswith("."):
            continue
        module_name = f"modules.{tier_name}"
        try:
            module = import_module(module_name)
        except ImportError:
            continue
        getter = getattr(module, "get_registry", None)
        if callable(getter):
            getters[tier_name] = getter
    return getters


def _get_registry_for_tier(tier: str) -> Optional[Any]:
    getter = _registry_getters().get(tier)
    if getter is None:
        return None
    try:
        return getter()
    except (RuntimeError, TypeError, ValueError):  # pragma: no cover - defensive
        return None


def _resolve_full_module_name(raw_name: str) -> str:
    normalized = raw_name.strip()
    if not normalized:
        raise typer.BadParameter("Module name cannot be empty")

    direct_candidate = MODULES_PATH / normalized
    if direct_candidate.is_dir() and (direct_candidate / "module.yaml").exists():
        try:
            return direct_candidate.relative_to(MODULES_PATH).as_posix()
        except ValueError:
            pass

    if "/" in normalized:
        tier, _, remainder = normalized.partition("/")
        if tier in _registry_getters():
            return normalized

    matches: List[str] = []
    for tier, getter in _registry_getters().items():
        try:
            registry = getter()
        except (RuntimeError, TypeError, ValueError):  # pragma: no cover - defensive
            continue
        if not registry:
            continue
        if registry.get_module(normalized):
            matches.append(f"{tier}/{normalized}")
            continue
        if "/" in normalized:
            remainder = normalized.split("/", 1)[-1]
            if registry.get_module(remainder):
                matches.append(f"{tier}/{remainder}")

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        tiers = ", ".join(sorted(matches))
        raise typer.BadParameter(
            f"Module '{raw_name}' exists in multiple tiers ({tiers}). Please specify a fully qualified name."
        )

    filesystem_matches = _discover_module_slugs(normalized)
    if len(filesystem_matches) == 1:
        return filesystem_matches[0]
    if len(filesystem_matches) > 1:
        options = ", ".join(filesystem_matches)
        raise typer.BadParameter(
            f"Module '{raw_name}' matched multiple modules: {options}. Provide a more specific identifier."
        )

    raise typer.BadParameter(
        f"Module '{raw_name}' not found. Verify the name or include the tier/category prefix."
    )


def _infer_profile(project_root: Path) -> Optional[str]:
    metadata = load_project_metadata(project_root)
    if metadata and metadata.profile:
        return metadata.profile

    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        try:
            contents = pyproject.read_text(encoding="utf-8")
        except OSError:
            contents = ""
        if "fastapi" in contents:
            return "fastapi/standard"

    package_json = project_root / "package.json"
    if package_json.exists():
        try:
            payload = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        dependencies = payload.get("dependencies")
        if isinstance(dependencies, dict) and any(
            key in dependencies for key in ("@nestjs/core", "@nestjs/common")
        ):
            return "nestjs/standard"

    return None


def _get_target_modules(modules: List[str]) -> List[str]:
    if not modules:
        raise typer.BadParameter("No module specified. Provide at least one module name.")

    resolved: List[str] = []
    for raw_module in modules:
        resolved.append(_resolve_full_module_name(raw_module))
    return resolved


def detect_framework_from_profile(profile: str) -> str:
    """Extract framework name from profile (e.g., 'fastapi' from 'fastapi/standard')."""
    return profile.split("/")[0]


def add_module(
    name: str,
    profile: Optional[str] = typer.Option(
        None,
        "--profile",
        "-p",
        help="Target profile (defaults to project metadata or 'fastapi/standard').",
        show_default=False,
    ),
    project: str = typer.Option(None, help="Project name inside boilerplates"),
    final: bool = typer.Option(
        False,
        "--final",
        help="Remove inject anchors for production",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force overwrite even if locally modified (stores previous_hash)",
    ),
    update: bool = typer.Option(
        False,
        "--update",
        help="Update mode: only overwrite if template changed and file NOT locally modified",
    ),
    plan: bool = typer.Option(
        False,
        "--plan",
        help="Plan (dry-run) mode: show what would happen (files, snippets) without writing",
    ),
    with_deps: bool = typer.Option(
        False,
        "--with-deps",
        help="Automatically install module dependencies first (from module.yaml depends_on graph)",
    ),
    no_deps: bool = typer.Option(
        False,
        "--no-deps",
        help="Fail if module dependencies are missing (do not auto-install)",
    ),
    reconcile: bool = typer.Option(
        True,
        "--reconcile/--no-reconcile",
        help="After install, reconcile pending snippet injections related to this module (producer/owner).",
    ),
) -> None:
    """
    Add a module to the project with the specified profile.
    """

    logo_path = Path(__file__).parent.parent.parent / "assets" / "logo.txt"
    logo = None
    if logo_path.exists():
        try:
            logo = logo_path.read_text(encoding="utf-8")
        except OSError:
            logo = None
    if logo:
        # Only print the logo, no extra text before/after
        print_info(logo)
    print_info("[bold white]" + "═" * 60 + "[/bold white]")
    start_time = time.time()
    step_times = {}

    def step(
        _label: str,
    ) -> float:  # records elapsed seconds since start (label unused)
        return time.time() - start_time

    profile_obj: object = profile
    if isinstance(profile_obj, OptionInfo):
        default = profile_obj.default if profile_obj.default is not ... else None
        profile = cast(Optional[str], default)

    project_obj: object = project
    if isinstance(project_obj, OptionInfo):
        default = project_obj.default if project_obj.default is not ... else None
        project = cast(str, default)

    final_obj: object = final
    if isinstance(final_obj, OptionInfo):
        default = final_obj.default if final_obj.default is not ... else False
        final = cast(bool, default)

    force_obj: object = force
    if isinstance(force_obj, OptionInfo):
        default = force_obj.default if force_obj.default is not ... else False
        force = cast(bool, default)

    update_obj: object = update
    if isinstance(update_obj, OptionInfo):
        default = update_obj.default if update_obj.default is not ... else False
        update = cast(bool, default)

    plan_obj: object = plan
    if isinstance(plan_obj, OptionInfo):
        default = plan_obj.default if plan_obj.default is not ... else False
        plan = cast(bool, default)

    with_deps_obj: object = with_deps
    if isinstance(with_deps_obj, OptionInfo):
        default = with_deps_obj.default if with_deps_obj.default is not ... else False
        with_deps = cast(bool, default)

    no_deps_obj: object = no_deps
    if isinstance(no_deps_obj, OptionInfo):
        default = no_deps_obj.default if no_deps_obj.default is not ... else False
        no_deps = cast(bool, default)

    reconcile_obj: object = reconcile
    if isinstance(reconcile_obj, OptionInfo):
        default = reconcile_obj.default if reconcile_obj.default is not ... else True
        reconcile = cast(bool, default)

    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    if with_deps and no_deps:
        raise typer.BadParameter("Use only one of --with-deps or --no-deps")

    resolved_modules = _get_target_modules([name])
    name = resolved_modules[0]

    tier, _, module_slug = name.partition("/")
    registry_status: Optional[str] = None
    registry_obj = _get_registry_for_tier(tier) if tier else None
    if registry_obj is not None and module_slug:
        try:
            module_meta = registry_obj.get_module(module_slug)
            if not module_meta and "/" in module_slug:
                module_meta = registry_obj.get_module(module_slug.split("/")[-1])
        except (AttributeError, TypeError, ValueError):  # pragma: no cover - defensive
            module_meta = None
        if isinstance(module_meta, dict):
            raw_status = module_meta.get("status")
            if isinstance(raw_status, str):
                registry_status = raw_status.strip().lower()
                if registry_status in _STATUS_BLOCKLIST:
                    print_error(
                        f"⛔ Module '{name}' is marked as '{registry_status}' and is not available for installation yet."
                    )
                    raise typer.Exit(code=2)
                if registry_status in _STATUS_WARN:
                    print_warning(
                        f"⚠️ Module '{name}' is marked as '{registry_status}'. Proceed with caution."
                    )
                elif registry_status in _STATUS_CAUTION:
                    print_warning(
                        f"⚠️ Module '{name}' is marked as '{registry_status}'. Expect limited stability."
                    )

    inferred_profile = _infer_profile(project_root)
    if profile:
        effective_profile = profile
    elif inferred_profile:
        effective_profile = inferred_profile
        print_info(
            f"[dim]Detected project profile from metadata: [yellow]{inferred_profile}[/yellow][/dim]"
        )
    else:
        effective_profile = "fastapi/standard"
        print_info(
            "[dim]Profile not provided; defaulting to [yellow]fastapi/standard[/yellow][/dim]"
        )
    profile = effective_profile

    module_dir = resolve_module_directory(MODULES_PATH, name)
    module_templates_dir = module_dir / "templates"

    # Compute canonical slug relative to modules root for registry bookkeeping
    try:
        effective_slug = module_dir.relative_to(MODULES_PATH).as_posix()
    except ValueError:
        effective_slug = name

    should_validate_structure = module_dir.exists() and (module_dir / "module.yaml").exists()

    if should_validate_structure:
        try:
            structure_slug = module_dir.relative_to(MODULES_PATH).as_posix()
        except ValueError:
            structure_slug = name

        try:
            ensure_module_structure(structure_slug)
        except ModuleStructureError as exc:
            print_error("⛔ Module structure validation failed:\n" f"{exc}")
            raise typer.Exit(code=1) from exc

    print_info(
        f"\n Installing module: [bold cyan]{name}[/bold cyan]   [dim]| Profile:[/dim] [yellow]{profile}[/yellow]"
    )

    # --- ENFORCE LICENSE GATING ---
    if enforce_module_gating is not None:
        try:
            enforce_module_gating(name)
        except RuntimeError as e:
            print_error(f"⛔ License restriction: {e}")
            raise typer.Exit(code=3) from e

    # Load optional manifest and resolve dependencies if present
    manifest = load_manifest_or_none(MODULES_PATH, name)
    if manifest:
        print_info(
            f"[bold green]Manifest:[/bold green] {manifest.effective_name} v{manifest.version} [dim]status={manifest.status}[/dim]"
        )

        manifest_status = manifest.status.strip().lower()
        if manifest_status in _STATUS_BLOCKLIST:
            print_error(
                f"⛔ Module '{manifest.name}' is marked as '{manifest_status}' in its manifest and cannot be installed yet."
            )
            raise typer.Exit(code=2)
        if manifest_status in _STATUS_WARN and manifest_status != registry_status:
            print_warning(
                f"⚠️ Module '{manifest.name}' is marked as '{manifest_status}'. Consider upgrading when a stable release is available."
            )
        elif manifest_status in _STATUS_CAUTION and manifest_status != registry_status:
            print_warning(
                f"⚠️ Module '{manifest.name}' is marked as '{manifest_status}'. Features may change without notice."
            )

        # Dependency resolution (only if manifests available for graph)
        try:
            all_manifests = load_all_manifests(MODULES_PATH)
            # Ensure target manifest participates even if not discoverable via rglob.
            manifest_slug = getattr(manifest, "slug", "") or ""
            if manifest_slug and manifest_slug not in all_manifests:
                all_manifests[manifest_slug] = manifest
            target = manifest_slug or name
            install_order = compute_install_order([target], all_manifests)
            if len(install_order) > 1:
                dep_chain = " -> ".join([m.slug or m.name for m in install_order])
                print_info(f"[bold blue]Dependency chain:[/bold blue] {dep_chain} (target last)")

                installed_slugs = _load_installed_module_slugs(project_root)
                preceding = [m for m in install_order if (m.slug or m.name) != target]
                missing = [m for m in preceding if (m.slug or m.name) not in installed_slugs]
                if missing:
                    missing_names = ", ".join((m.slug or m.name) for m in missing)
                    if plan:
                        print_warning(
                            f"[dim]Plan:[/dim] missing dependencies detected: {missing_names} (no installs will run)"
                        )
                    elif no_deps:
                        print_error(
                            "⛔ Missing required module dependencies: "
                            f"{missing_names}. Install them first or re-run with --with-deps."
                        )
                        raise typer.Exit(code=1)
                    else:
                        should_install = with_deps
                        if not with_deps and sys.stdin.isatty() and sys.stdout.isatty():
                            should_install = bool(
                                typer.confirm(
                                    f"This module requires: {missing_names}. Install dependencies now?",
                                    default=True,
                                )
                            )
                        if should_install:
                            for dep_manifest in missing:
                                print_info(
                                    f"\n[bold blue]Installing dependency:[/bold blue] {dep_manifest.slug or dep_manifest.name}"
                                )
                                add_module(
                                    dep_manifest.slug or dep_manifest.name,
                                    profile=profile,
                                    project=project,
                                    final=final,
                                    force=force,
                                    update=update,
                                    plan=False,
                                    with_deps=True,
                                    no_deps=False,
                                )
                        else:
                            print_warning(
                                "Dependencies should be installed first; continuing without installing them."
                            )
            else:
                print_info("[dim]No dependencies detected[/dim]")
        except typer.Exit:
            raise
        except (OSError, ValueError, RuntimeError) as e:
            print_warning(f"⚠️ Dependency resolution skipped: {e}")
    else:
        print_warning("⚠️ No module.yaml manifest found (falling back to legacy config only)")

    try:
        config = load_module_config(name, profile)
    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(code=1) from None

    # --- Pretty merged config summary ---

    # Render minimal enterprise summary once
    _console.print(build_minimal_config_summary(config, profile))

    # In plan mode skip dependency installation & prompting (use defaults)
    variables_config = config.get("variables", {})
    if not plan:
        # Install dependencies (handles prod/dev + requirements/poetry correctly)
        install_module_dependencies(config, profile, project, final)
        variables = prompt_for_variables(variables_config)
    else:
        variables = {
            k: (v.get("default") if isinstance(v, dict) else None)
            for k, v in variables_config.items()
        }

    vendor_module_name = name
    vendor_module_version = "0.0.0"
    if manifest:
        vendor_module_name = manifest.name or name
        vendor_module_version = manifest.version or vendor_module_version

    variables.setdefault("rapidkit_vendor_module", vendor_module_name)
    variables.setdefault("rapidkit_vendor_version", vendor_module_version)

    # Resolve profile inheritance chain
    profile_chain = resolve_profile_chain(profile, config)
    framework = detect_framework_from_profile(profile)

    # Collect all files
    all_files: List[Tuple[str, Dict[str, Any]]] = []
    override_dict = config.get("files", {}).get("overrides", {})
    seen_paths = set()
    for p in profile_chain:
        entries = override_dict.get(p, [])
        for entry in entries:
            path = entry.get("path") if isinstance(entry, dict) else entry
            if path and path not in seen_paths:
                all_files.append((p, entry if isinstance(entry, dict) else {"path": entry}))
                seen_paths.add(path)

    # Feature-specific files
    active_features: List[str] = []
    raw_features = config.get("features", {})
    if isinstance(raw_features, dict):
        for feature_name, meta in raw_features.items():
            # Backwards-compatible: `features: {foo: true}` means enabled for all profiles.
            if meta is True:
                active_features.append(str(feature_name))
                continue
            if meta is False or meta is None:
                continue
            if isinstance(meta, dict):
                profiles = meta.get("profiles", [])
                if isinstance(profiles, list) and profile in profiles:
                    active_features.append(str(feature_name))

    # Snippet configs frequently gate on the module manifest name (module.yaml `name`).
    # Ensure it's always considered active when the module is installed.
    if manifest and manifest.name and manifest.name not in active_features:
        active_features.append(str(manifest.name))
    print_info(
        "\n[bold blue]Active features:[/bold blue] "
        + ", ".join([f"[green]{f}[/green]" for f in active_features])
    )
    for feature in active_features:
        feature_files = config.get("features_files", {}).get(feature, [])
        for entry in feature_files:
            path = entry.get("path") if isinstance(entry, dict) else entry
            if path and path not in seen_paths:
                all_files.append((profile, entry if isinstance(entry, dict) else {"path": entry}))
                seen_paths.add(path)

    # Test files
    for section in ["unit_tests", "e2e_tests", "security_tests", "performance_tests"]:
        for feature in active_features:
            test_files = config.get(section, {}).get(feature, [])
            for entry in test_files:
                path = entry.get("path") if isinstance(entry, dict) else entry
                if path and path not in seen_paths:
                    all_files.append(
                        (profile, entry if isinstance(entry, dict) else {"path": entry})
                    )
                    seen_paths.add(path)

    # CI/CD files
    ci_cd_files = config.get("ci_cd", {})
    if isinstance(ci_cd_files, dict):
        for sub_section in ci_cd_files.values():
            for entry in sub_section:
                path = (
                    entry.get("path") or entry.get("template") if isinstance(entry, dict) else entry
                )
                if path and path not in seen_paths:
                    all_files.append(
                        (profile, entry if isinstance(entry, dict) else {"path": entry})
                    )
                    seen_paths.add(path)
    else:
        for entry in ci_cd_files:
            path = entry.get("path") if isinstance(entry, dict) else entry
            if path and path not in seen_paths:
                all_files.append((profile, entry if isinstance(entry, dict) else {"path": entry}))
                seen_paths.add(path)

    skipped_files: List[str] = []
    created_files: List[str] = []
    overwritten_files: List[str] = []
    modified_conflicts: List[str] = []
    hard_failures: List[str] = []
    hash_registry = load_hashes(project_root)
    root_path = config.get("root_path", "")

    # --- Step 1: Create files ---
    step_times["file_creation"] = step("file_creation")
    print_info("\n[bold magenta]--- File Creation ---[/bold magenta]")
    if plan:
        print_info("[dim]Planning only (no files will be written)[/dim]")

    generation_cfg_obj = config.get("generation") if isinstance(config, dict) else {}
    generation_cfg: Dict[str, Any] = (
        generation_cfg_obj if isinstance(generation_cfg_obj, dict) else {}
    )
    manifest_payload = getattr(manifest, "raw", None)
    if not generation_cfg and manifest and isinstance(manifest_payload, dict):
        raw_generation = manifest_payload.get("generation")
        if isinstance(raw_generation, dict):
            generation_cfg = raw_generation

    use_generation_pipeline = bool(generation_cfg.get("variants"))
    if use_generation_pipeline:
        try:
            _apply_generated_module(
                module_dir,
                project_root,
                generation_cfg,
                framework,
                variables,
                plan,
                force,
                update,
                manifest,
                vendor_module_name,
                vendor_module_version,
                hash_registry,
                created_files,
                overwritten_files,
                skipped_files,
                modified_conflicts,
                hard_failures,
            )
        except RuntimeError as exc:
            print_error(f"❌ {exc}")
            raise typer.Exit(code=1) from exc
    else:
        for context, file_entry in all_files:
            relative_path = (
                file_entry.get("path") or file_entry.get("template")
                if isinstance(file_entry, dict)
                else file_entry
            )
            if not relative_path:
                print_warning(f"⚠️ Skipping file entry with no path or template: {file_entry}")
                continue
            # removed unused replace_if_only_anchor flag

            template_file = file_entry.get("template") if isinstance(file_entry, dict) else None
            vendor_template_path = None
            if template_file:
                template_path = module_dir / template_file
            else:
                template_path = (
                    module_templates_dir
                    / ("base" if context == "base" else f"overrides/{context}")
                    / f"{relative_path}.j2"
                )
                vendor_template_path = (
                    module_templates_dir
                    / "vendor"
                    / ("base" if context == "base" else f"overrides/{context}")
                    / f"{relative_path}.j2"
                )

            destination_path = resolve_project_path(project_root, root_path, relative_path)

            if not template_path.exists():
                print_warning(f"❌ Template not found: {template_path}")
                continue

            rel_record_path = str(destination_path.relative_to(project_root))
            try:
                new_content = render_template(template_path, variables)
            except (OSError, ValueError, RuntimeError) as e:
                print_error(f"⚠️ Failed to render {template_path}: {e}")
                continue
            new_bytes = new_content.encode("utf-8")
            previous_hash = None
            if destination_path.exists():
                try:
                    existing_bytes = destination_path.read_bytes()
                except OSError:
                    existing_bytes = b""
                entry = hash_registry.get("files", {}).get(rel_record_path)
                tracked_hash = entry.get("hash") if entry else None
                locally_modified = file_was_modified(hash_registry, rel_record_path, existing_bytes)
                template_changed = True if not tracked_hash else tracked_hash != _sha256(new_bytes)
                if force:
                    previous_hash = tracked_hash or (
                        _sha256(existing_bytes) if existing_bytes else None
                    )
                elif update:
                    if locally_modified:
                        print_warning(
                            f"✋ Local changes detected, skipping (update mode): {rel_record_path}"
                        )
                        modified_conflicts.append(rel_record_path)
                        continue
                    if not template_changed:
                        print_info(f"⏭ Up-to-date: {rel_record_path}")
                        skipped_files.append(rel_record_path)
                        continue
                elif locally_modified:
                    print_warning(
                        f"✋ Local changes detected, skipping overwrite: {rel_record_path}"
                    )
                    modified_conflicts.append(rel_record_path)
                    continue
            # write file
            if plan:
                action = "overwrite" if destination_path.exists() else "create"
                print_info(
                    f"[cyan]{action.upper():9}[/cyan] {rel_record_path}  [dim]template={template_path.name}[/dim]"
                )
                continue
            try:
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                ensure_init_files(destination_path, project_root)
                create_file(destination_path, new_content)
                existed_before = rel_record_path in hash_registry.get("files", {})
                if manifest:
                    module_identifier = vendor_module_name
                    vendor_bytes = new_bytes
                    if vendor_template_path and vendor_template_path.exists():
                        try:
                            vendor_render = render_template(vendor_template_path, variables)
                        except (OSError, ValueError, RuntimeError) as e:
                            print_warning(
                                f"⚠️ Failed to render vendor template {vendor_template_path}: {e}"
                            )
                        else:
                            vendor_bytes = vendor_render.encode("utf-8")
                    record_file_hash(
                        hash_registry,
                        rel_record_path,
                        module_identifier,
                        manifest.version,
                        new_bytes,
                        previous_hash=previous_hash,
                        snapshot=True,
                        project_root=project_root,
                    )
                    if manifest.version:
                        store_vendor_file(
                            project_root,
                            module_identifier,
                            manifest.version,
                            rel_record_path,
                            vendor_bytes,
                        )
                if existed_before:
                    overwritten_files.append(rel_record_path)
                    print_success(f"♻️  Overwritten: {rel_record_path}")
                else:
                    created_files.append(rel_record_path)
                    print_success(f"✅ Created: {rel_record_path}")
            except OSError as e:
                print_error(f"⚠️ Failed to write {template_path}: {e}")

    # --- Step 2: Copy extras ---
    step_times["extras"] = step("extras")
    print_info("\n[bold magenta]--- Extra Files (migrations, docs, ci_cd) ---[/bold magenta]")
    if plan:
        print_info("[dim]Skipping extras (plan mode)[/dim]")
    else:
        for section in ["migrations", "docs", "ci_cd"]:
            copy_extra_files(
                section, config, project_root, root_path, name, MODULES_PATH, variables
            )

    # --- Step 3: Update registry ---
    step_times["registry"] = step("registry")
    print_info("\n[bold magenta]--- Registry Update ---[/bold magenta]")
    if not plan:
        registry_version: Optional[str] = None
        if manifest and manifest.version:
            registry_version = manifest.version
        else:
            cfg_version = config.get("version") if isinstance(config, dict) else None
            if isinstance(cfg_version, str) and cfg_version.strip():
                registry_version = cfg_version.strip()

        display_name = manifest.effective_name if manifest else None

        update_registry(
            effective_slug,
            project_root,
            version=registry_version,
            display_name=display_name,
        )
    else:
        print_info("[dim]Skipping registry update (plan mode)[/dim]")

    # --- Step 4: Auto-mount ---
    step_times["automount"] = step("automount")
    print_info("\n[bold magenta]--- Auto-mount ---[/bold magenta]")
    framework = detect_framework_from_profile(profile)
    auto_mount_config = config.get("auto_mount", {})
    mount_target = auto_mount_config.get(profile)

    if mount_target and not plan:
        mount_path = resolve_project_path(project_root, root_path, mount_target)
        if framework == "fastapi":
            for f in created_files:
                if f.endswith((".py",)):
                    rel_path = str(Path(f).relative_to(root_path))
                    try:
                        handle_fastapi_router(rel_path, mount_path)
                    except (OSError, RuntimeError, ValueError) as e:
                        print_warning(f"⚠️ Failed to auto-mount {rel_path}: {e}")
        elif framework == "nestjs":
            root_path_str = str(root_path)
            for f in created_files:
                if f.endswith((".ts",)):
                    rel_path = str(Path(f).relative_to(root_path))
                    try:
                        handle_nestjs_module(project_root, rel_path, root_path_str)
                    except (OSError, RuntimeError, ValueError) as e:
                        print_warning(f"⚠️ Failed to auto-mount {rel_path}: {e}")

    # --- Step 5: Inject snippets (after file creation) ---
    raw_snippets_cfg = config.get("snippets", [])
    snippet_entries: List[Dict[str, Any]] = []
    invalid_snippet_types: Set[str] = set()
    invalid_snippet_count = 0
    seen_snippet_signatures: Set[str] = set()
    loaded_snippet_paths: Set[Path] = set()

    def _register_snippet_entries(entries: Any) -> None:
        nonlocal invalid_snippet_count
        if not isinstance(entries, list):
            return
        for entry in entries:
            if isinstance(entry, dict):
                signature = json.dumps(entry, sort_keys=True, default=str)
                if signature in seen_snippet_signatures:
                    continue
                seen_snippet_signatures.add(signature)
                snippet_entries.append(entry)
            else:
                invalid_snippet_count += 1
                invalid_snippet_types.add(type(entry).__name__)

    def _collect_snippets_from_source(payload: Any) -> None:
        nonlocal invalid_snippet_count
        if payload is None:
            return

        if isinstance(payload, list):
            _register_snippet_entries(payload)
        elif isinstance(payload, dict):
            if any(key in payload for key in ("target", "anchor", "template")):
                _register_snippet_entries([payload])
            else:
                for key in ("entries", "items", "snippets", "default", "values"):
                    maybe_list = payload.get(key)
                    if isinstance(maybe_list, list):
                        _register_snippet_entries(maybe_list)
                        break
                else:
                    config_ref = payload.get("config")
                    if isinstance(config_ref, str):
                        snippet_config_path = Path(config_ref)
                        if not snippet_config_path.is_absolute():
                            snippet_config_path = module_dir / snippet_config_path
                        snippet_config_path = snippet_config_path.resolve()
                        already_loaded = snippet_config_path in loaded_snippet_paths
                        loaded_snippet_paths.add(snippet_config_path)
                        if already_loaded:
                            return
                        if not snippet_config_path.exists():
                            print_warning(
                                f"⚠️ Snippet config referenced at '{config_ref}' not found for module {name}"
                            )
                        else:
                            try:
                                file_payload = yaml.safe_load(
                                    snippet_config_path.read_text(encoding="utf-8")
                                )
                            except (OSError, yaml.YAMLError) as exc:
                                print_warning(
                                    f"⚠️ Failed to load snippet config '{config_ref}': {exc}"
                                )
                            else:
                                _collect_snippets_from_source(file_payload)
        else:
            invalid_snippet_count += 1
            invalid_snippet_types.add(type(payload).__name__)

    _collect_snippets_from_source(raw_snippets_cfg)

    manifest_snippets_cfg = (
        generation_cfg.get("snippets") if isinstance(generation_cfg, dict) else None
    )
    if manifest_snippets_cfg:
        _collect_snippets_from_source(manifest_snippets_cfg)

    if invalid_snippet_count:
        type_summary = ", ".join(sorted(invalid_snippet_types)) or "unknown"
        print_warning(
            f"⚠️ Ignored {invalid_snippet_count} snippet definition(s) with unsupported type(s): {type_summary}"
        )

    step_times["snippets"] = step("snippets")
    print_info("\n[bold magenta]--- Snippet Injection ---[/bold magenta]")
    print_info(f"🔍 Found [bold]{len(snippet_entries)}[/bold] snippets.")
    if plan:
        for snippet in snippet_entries:
            tgt = snippet.get("target") if isinstance(snippet, dict) else None
            desc = snippet.get("description", "") if isinstance(snippet, dict) else ""
            print_info(f"[cyan]SNIPPET[/cyan] target={tgt} desc={desc}")
        print_info("[dim]Skipping actual injection (plan mode)[/dim]")
        snippets = []
    else:
        snippets = snippet_entries
    injected_targets = set()

    # trackers for summary
    injected_list = []
    blocked_list = []
    warned_list = []
    injected_seen: set[str] = set()

    for snippet in snippets:
        target_val = snippet.get("target")
        anchor_val = snippet.get("anchor")
        if not target_val or not anchor_val:
            print_warning(
                f"⚠️ Snippet skipped: missing target or anchor in {snippet.get('id', 'unknown')}"
            )
            continue
        print_info(
            f"🔍 Processing snippet for target: {target_val} (ID: {snippet.get('id', 'unknown')})"
        )
        allowed_profiles = snippet.get("profiles", [])
        allowed_features = snippet.get("features", [])

        def _profile_aliases(value: str) -> set[str]:
            cleaned = value.strip()
            if not cleaned:
                return set()
            aliases = {cleaned, cleaned.replace(".", "/"), cleaned.replace("/", ".")}
            return {a for a in aliases if a}

        normalized_profile_chain: set[str] = set()
        for chain_profile in profile_chain:
            if isinstance(chain_profile, str):
                normalized_profile_chain.update(_profile_aliases(chain_profile))

        normalized_allowed_profiles: List[str] = []
        if isinstance(allowed_profiles, list):
            normalized_allowed_profiles = [str(p) for p in allowed_profiles if str(p).strip()]
        elif isinstance(allowed_profiles, str):
            normalized_allowed_profiles = [
                p.strip() for p in allowed_profiles.split(",") if p.strip()
            ]

        if normalized_allowed_profiles:
            allowed_match = False
            for allowed in normalized_allowed_profiles:
                if _profile_aliases(allowed) & normalized_profile_chain:
                    allowed_match = True
                    break
            if not allowed_match:
                print_warning(
                    f"⚠️ Snippet skipped: profile {profile} not in {normalized_allowed_profiles}"
                )
                continue
        if allowed_features and not any(f in active_features for f in allowed_features):
            print_warning(f"⚠️ Snippet skipped: feature not in {active_features}")
            continue

        # Robust parsing for targets/anchors (accepts list, "{a,b}", or plain string)
        def _normalize_to_list(val: object) -> List[str]:
            if val is None:
                return []
            if isinstance(val, list):
                items = val
            elif isinstance(val, str):
                v = val.strip()
                if v.startswith("{") and v.endswith("}"):
                    v = v[1:-1]
                items = [s.strip() for s in v.split(",")] if v else []
            else:
                items = [str(val).strip()]
            # filter out empty/None-like values
            return [s for s in items if isinstance(s, str) and s.strip()]

        targets = _normalize_to_list(target_val)
        anchors = _normalize_to_list(anchor_val)

        if not targets:
            print_warning(
                f"⚠️ Snippet skipped: no valid targets parsed in {snippet.get('id', 'unknown')}"
            )
            continue
        if not anchors:
            print_warning(
                f"⚠️ Snippet skipped: no valid anchors parsed in {snippet.get('id', 'unknown')}"
            )
            continue

        template_path = module_templates_dir / "snippets" / snippet.get("template", "")

        if not template_path.exists():
            print_warning(f"⚠️ Snippet template not found: {template_path}")
            continue

        # Iterate all targets; if only one anchor is provided, reuse it for all
        for idx, target in enumerate(targets):
            anchor = anchors[idx] if idx < len(anchors) else anchors[0]
            if not isinstance(anchor, str) or not anchor.strip():
                print_warning(
                    f"⚠️ Snippet skipped for target {target}: invalid anchor value: {anchor}"
                )
                continue
            # For dot-prefixed files (e.g., .env*), inject at project root; otherwise under root_path
            if target.startswith("."):
                destination_path = project_root / target
            else:
                destination_path = resolve_project_path(project_root, root_path, target)
            try:
                # decide leniency: dev-like profiles or explicit env override
                env_lenient = os.environ.get("RAPIDKIT_ENV_LENIENT")
                profile_lenient = any(p in profile.lower() for p in ("dev", "local"))
                lenient_flag = (
                    bool(env_lenient and env_lenient.lower() in ("1", "true", "yes"))
                    or profile_lenient
                )
                snippet_meta = dict(snippet)
                snippet_meta.setdefault(
                    "module_slug", (manifest.slug if manifest else None) or name
                )
                snippet_meta.setdefault("profile", profile)
                snippet_meta.setdefault("target", target_val)
                result = inject_snippet_enterprise(
                    destination_path,
                    template_path,
                    anchor,
                    variables,
                    snippet_metadata=snippet_meta,
                    project_root=project_root,
                    lenient=lenient_flag,
                )
                # result is a dict: {injected, blocked, warnings, errors}
                if isinstance(result, dict):
                    injected_flag = bool(result.get("injected"))
                    blocked_flag = bool(result.get("blocked"))
                    warnings_list = result.get("warnings") or []
                    if injected_flag:
                        dest_str = str(destination_path)
                        if dest_str not in injected_seen:
                            injected_seen.add(dest_str)
                            injected_list.append(dest_str)
                        if destination_path.suffix == ".py":
                            try:
                                organize_imports(destination_path)
                            except (OSError, RuntimeError) as oe:
                                print_warning(
                                    f"⚠️ Imports not organized for {destination_path}: {oe}"
                                )
                        if isinstance(target, str) and target and not target.startswith("."):
                            injected_targets.add(target)
                    if blocked_flag:
                        blocked_list.append(
                            {
                                "target": str(destination_path),
                                "errors": result.get("errors", []),
                            }
                        )
                    if warnings_list:
                        warned_list.append(
                            {
                                "target": str(destination_path),
                                "warnings": warnings_list,
                            }
                        )
            except (OSError, RuntimeError, ValueError) as e:
                print_warning(f"⚠️ Failed to inject snippet into {target}: {e}")

    # --- Step 6: Remove anchors if final ---
    # --- Optional: Scoped reconcile before anchor removal ---
    if reconcile and not plan:
        try:
            verbose_reconcile = os.environ.get(
                "RAPIDKIT_RECONCILE_VERBOSE", ""
            ).strip().lower() in (
                "1",
                "true",
                "yes",
            )
            stats = reconcile_pending_snippets_scoped(
                project_root,
                scope_slugs={effective_slug},
                modules_root=MODULES_PATH,
                return_details=verbose_reconcile,
            )
            if stats.get("pending_before", 0):
                print_info(
                    f"\n[bold magenta]--- Reconcile (scoped) ---[/bold magenta]\n"
                    f"Applied={stats.get('applied', 0)} Pending={stats.get('pending_after', 0)} Skipped={stats.get('skipped', 0)} Failed={stats.get('failed', 0)}"
                )
                if verbose_reconcile:
                    applied_keys = stats.get("applied_keys") or []
                    if isinstance(applied_keys, list) and applied_keys:
                        print_info("[dim]Applied keys:[/dim]")
                        for k in applied_keys:
                            if isinstance(k, str) and k.strip():
                                print_info(f"  - {k}")
        except (OSError, ValueError, RuntimeError) as e:
            print_warning(f"⚠️ Scoped reconcile skipped: {e}")

    if final and not plan:
        for target in injected_targets:
            destination_path = resolve_project_path(project_root, root_path, target)
            try:
                remove_inject_anchors(destination_path)
            except (OSError, RuntimeError) as e:
                print_warning(f"⚠️ Failed to remove anchors from {target}: {e}")

    # --- Step 7: Process translations ---
    locale_dir = resolve_project_path(project_root, root_path, "shared/i18n/locales")
    if not plan:
        try:
            process_translations(locale_dir, final, config)
        except (OSError, RuntimeError, ValueError) as e:
            print_warning(f"⚠️ Failed to process translations: {e}")
    else:
        print_info("[dim]Skipping translations (plan mode)[/dim]")

    if skipped_files:
        print_info(f"⚠️ {len(skipped_files)} files skipped (already existed):")

    # Summary report
    # --- Summary Table ---
    print_info("\n[bold green]=== Summary ===[/bold green]")
    total_overwritten = len(overwritten_files)
    total_snippets = len(snippets)
    total_injected = len(injected_list)
    total_blocked = len(blocked_list)
    total_warned = len(warned_list)
    total_skipped = len(skipped_files)
    print_info(
        f"[bold]Files created:[/bold] [green]{len(created_files)}[/green]   [bold]Overwritten:[/bold] [yellow]{total_overwritten}[/yellow]   [bold]Snippets:[/bold] [cyan]{total_snippets}[/cyan]   [bold]Injected:[/bold] [green]{total_injected}[/green]   [bold]Blocked:[/bold] [red]{total_blocked}[/red]   [bold]Warnings:[/bold] [yellow]{total_warned}[/yellow]   [bold]Skipped:[/bold] [magenta]{total_skipped}[/magenta]"
    )
    if created_files:
        print_info("\n[bold]Created Files:[/bold]")
        for f in created_files:
            print_info(f"   [green]•[/green] {f}")
    if overwritten_files:
        print_info("\n[bold]Overwritten Files:[/bold]")
        for f in overwritten_files:
            print_info(f"   [yellow]•[/yellow] {f}")
    if injected_list:
        print_info("\n[bold]Injected Snippet Targets:[/bold]")
        for p in injected_list:
            print_info(f"   [cyan]•[/cyan] {p}")
    if blocked_list:
        print_info("\n[bold red]Blocked Snippet Targets:[/bold red]")
        for b in blocked_list:
            print_info(f"   [red]•[/red] {b['target']}")
    if warned_list:
        print_info("\n[bold yellow]Warnings:[/bold yellow]")
        for w in warned_list:
            print_info(f"   [yellow]•[/yellow] {w['target']}")
    if skipped_files:
        print_info("\n[bold magenta]Skipped Files:[/bold magenta]")
        for f in sorted(set(skipped_files)):
            print_info(f"   [magenta]- {f}[/magenta]")
    # persist hashes regardless of create vs overwrite
    if not plan and (created_files or overwritten_files) and manifest:
        try:
            save_hashes(project_root, hash_registry)
        except OSError as e:
            print_error(f"❌ Failed to save hash registry: {e}")
            hard_failures.append("failed to persist hash registry")

    # Inject explicit module imports into src/modules/__init__.py (idempotent)
    if not plan:
        try:
            _inject_module_imports(project_root, effective_slug)
        except Exception as exc:  # pragma: no cover - defensive  # noqa: BLE001
            print_warning(f"⚠️ Failed to inject module imports into modules/__init__.py: {exc}")

    elapsed = time.time() - start_time
    print_info("\n[bold white]" + "═" * 60 + "[/bold white]")

    if hard_failures:
        print_error("❌ Module installation failed due to non-recoverable errors:")
        for failure in sorted(set(hard_failures)):
            print_error(f"  - {failure}")
        raise typer.Exit(code=1)

    if plan:
        print_success(
            f"📝 [bold green]Plan complete for module '{name}' (no changes made).[/bold green]"
        )
    else:
        print_success(f"🎉 [bold green]Module '{name}' installed successfully![/bold green]")
    print_info(f"[dim]Total time: {elapsed:.2f} seconds[/dim]")
    print_info("[bold white]" + "═" * 60 + "\n[/bold white]")
    if modified_conflicts:
        print_warning(
            f"⚠️ {len(modified_conflicts)} locally modified files were left untouched (enable force flag in future to override)"
        )
    print_info(
        "[bold blue]Next steps:[/bold blue]  [dim]cd {project or '<project>'}  |  Edit settings, run tests, or start the app[/dim]"
    )
