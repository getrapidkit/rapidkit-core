from __future__ import annotations

import os
import re
import shutil
from collections.abc import Mapping as MappingABC
from pathlib import Path
from typing import Any, Callable, Mapping

from modules.shared.exceptions import ModuleGeneratorError

from . import DEFAULT_ENCODING, TemplateRenderer, write_file
from .snippets import apply_snippets, get_snippet_registry

PluginGetter = Callable[[str], Any]
PluginLister = Callable[[], Mapping[str, Any]]


class BaseModuleGenerator:
    """Shared orchestration for module generators."""

    def __init__(
        self,
        *,
        module_root: Path,
        templates_root: Path | None,
        project_root: Path | None,
        module_identifier: str,
        get_plugin: PluginGetter,
        list_plugins: PluginLister,
        error_cls: type[ModuleGeneratorError],
    ) -> None:
        self.module_root = module_root
        self.templates_root = templates_root or module_root
        self.project_root = project_root or self.detect_project_root(module_root)
        self.module_identifier = module_identifier
        self.get_plugin = get_plugin
        self.list_plugins = list_plugins
        self.error_cls = error_cls
        self.snippet_registry = get_snippet_registry()
        self._last_vendor_root: str | None = None

    @staticmethod
    def detect_project_root(start: Path) -> Path:
        resolved = start.resolve()
        for candidate in (resolved, *resolved.parents):
            if (candidate / "pyproject.toml").exists():
                return candidate
        return resolved

    def raise_error(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        error = self.error_cls(message, context=dict(context) if context else None)
        error.exit_code = exit_code  # type: ignore[attr-defined]
        raise error

    def load_module_config(self) -> Mapping[str, Any]:
        config_path = self.module_root / "module.yaml"
        with config_path.open(encoding=DEFAULT_ENCODING) as fh:
            data = yaml_safe_load(fh)
        if not isinstance(data, dict):  # pragma: no cover
            self.raise_error("module.yaml must resolve to a mapping")
        return data  # type: ignore[no-any-return]

    def create_renderer(self) -> TemplateRenderer:
        return TemplateRenderer(self.templates_root)

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def apply_base_context_overrides(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return dict(context)

    def apply_variant_context_pre(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:
        return dict(context)

    def apply_variant_context_post(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:
        return dict(context)

    def build_vendor_file_context(
        self,
        base_context: Mapping[str, Any],
        entry: Mapping[str, Any],
    ) -> dict[str, Any]:
        merged = dict(base_context)
        entry_context = entry.get("context")
        if isinstance(entry_context, MappingABC):
            merged.update(entry_context)
        return merged

    def resolve_template_path(self, template_reference: str | Path) -> Path:
        candidate = Path(template_reference)
        if candidate.is_absolute():
            return candidate
        return self.module_root / candidate

    def build_snippet_context(
        self,
        *,
        enriched_context: Mapping[str, Any],
        base_context: Mapping[str, Any],
        variant_name: str,
        logical_name: str,
        output_relative: str,
    ) -> dict[str, Any]:
        snippet_context = dict(enriched_context)
        snippet_context.setdefault("framework", variant_name)
        snippet_context.setdefault("logical_name", logical_name)
        snippet_context.setdefault("target_relative_path", output_relative)
        snippet_context.setdefault(
            "rapidkit_vendor_module",
            base_context.get("rapidkit_vendor_module", self.module_identifier),
        )
        return snippet_context

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:
        return None

    def generate_vendor_files(
        self,
        config: Mapping[str, Any],
        target_dir: Path,
        renderer: TemplateRenderer,
        context: Mapping[str, Any],
    ) -> None:
        vendor_cfg = config.get("generation", {}).get("vendor")
        if not vendor_cfg:
            return

        root = vendor_cfg.get("root", ".rapidkit/vendor")
        root_str = str(root)
        normalized_root = root_str.replace("\\", "/").lstrip("./")
        vendor_root_is_cache = normalized_root.startswith("rapidkit/vendor")
        self._last_vendor_root = root_str
        files = vendor_cfg.get("files", [])
        module_name = context.get("rapidkit_vendor_module", self.module_identifier)
        version = context.get("rapidkit_vendor_version", config.get("version", "0.0.0"))

        if isinstance(context, dict):
            context.setdefault("rapidkit_vendor_root", root_str)

        # Determine the host target type (Python vs Node).
        # Prefer explicit context hint (target_framework / framework) when present
        # — this is important when generation runs in a temporary directory
        # (e.g. during module install) before the real project files exist.
        host_framework = None
        if isinstance(context, MappingABC):
            host_framework = (
                context.get("target_framework")
                or context.get("framework")
                or context.get("variant")
            )

        if isinstance(host_framework, str):
            host_framework = host_framework.lower()

        # If explicit hint provided, use it; else fall back to file heuristics
        if isinstance(host_framework, str) and host_framework:
            host_is_node = "nestjs" in host_framework or "node" in host_framework
            host_is_python = "fastapi" in host_framework or "python" in host_framework
        else:
            host_is_node = (target_dir / "package.json").exists()
            host_is_python = (target_dir / "pyproject.toml").exists()

        def _infer_entry_framework(template_or_rel: str | Path) -> str:
            """Return 'node', 'python', or 'any' for the vendor entry.

            Heuristics used:
            - path contains 'nestjs' or endswith .ts/.js -> node
            - endswith .py -> python
            - otherwise -> any
            """
            val = str(template_or_rel).lower()
            if "nestjs" in val or val.endswith(".ts") or val.endswith(".js"):
                return "node"
            if val.endswith(".py"):
                return "python"
            return "any"

        for entry in files:
            template_rel = entry.get("template")
            if not template_rel:
                self.raise_error(
                    "Vendor file entry missing 'template' field. Update module.yaml",
                    context={"vendor_entry": entry},
                )
            template_path = self.resolve_template_path(template_rel)
            if not template_path.exists():
                self.raise_error(
                    f"Vendor template '{template_rel}' missing.",
                    context={
                        "template_path": str(template_path),
                        "module_root": str(self.module_root),
                    },
                )

            relative = entry.get("relative")
            if not isinstance(relative, str):
                self.raise_error(
                    "Vendor file entry missing 'relative' destination in module.yaml",
                    context={"vendor_entry": entry},
                )

            # Allow module authors to explicitly opt-in/opt-out vendor files for
            # particular frameworks using `framework` in the vendor entry. If not
            # provided, infer from template/relative path.
            entry_framework = None
            if isinstance(entry, MappingABC) and isinstance(entry.get("framework"), str):
                entry_framework = entry.get("framework")
            elif vendor_root_is_cache:
                entry_framework = "any"
            else:
                # infer from both relative destination and template path; prefer
                # the relative (output) when it provides a stronger hint.
                rel_hint = _infer_entry_framework(relative)
                tmpl_hint = _infer_entry_framework(template_rel)
                if rel_hint != "any":
                    entry_framework = rel_hint
                elif tmpl_hint != "any":
                    entry_framework = tmpl_hint
                else:
                    entry_framework = "any"

            # Filter vendor artifacts when the host project type is known to avoid
            # dropping Node assets into Python projects (and vice versa).
            if entry_framework != "any":
                if host_is_python and not host_is_node and entry_framework == "node":
                    continue
                if host_is_node and not host_is_python and entry_framework == "python":
                    continue

            file_context = self.build_vendor_file_context(context, entry)
            output = target_dir / root / module_name / version / relative
            rendered = renderer.render(template_path, file_context)
            write_file(output, rendered)

    def _resolve_plugin(self, variant_name: str) -> Any:
        def _is_missing(plugin: Any) -> bool:
            return plugin is None

        try:
            plugin = self.get_plugin(variant_name)
        except ValueError:
            plugin = None

        if not _is_missing(plugin):
            return plugin

        # Allow profiles/variants to use namespaced identifiers (e.g., "fastapi.standard")
        # by resolving the framework portion before surfacing an error.
        base_name = variant_name.split(".")[0]
        if base_name != variant_name:
            try:
                plugin = self.get_plugin(base_name)
            except ValueError:
                plugin = None
            if not _is_missing(plugin):
                return plugin

        available_plugins = self.list_plugins()
        available_names = list(available_plugins.keys())
        self.raise_error(
            f"Framework plugin '{variant_name}' not found. Available plugins: {', '.join(available_names)}",
            context={
                "requested_framework": variant_name,
                "available_plugins": available_names,
            },
        )

        raise RuntimeError("raise_error did not raise")  # pragma: no cover

    def _validate_requirements(self, plugin: Any, variant_name: str) -> None:
        try:
            validation_errors = plugin.validate_requirements()
        except (RuntimeError, ValueError, OSError) as exc:
            self.raise_error(
                f"Framework '{variant_name}' requirements not met: {exc}",
                context={"framework": variant_name, "error": str(exc)},
            )
        if validation_errors:
            self.raise_error(
                f"Framework '{variant_name}' requirements failed validation.",
                context={"framework": variant_name, "errors": validation_errors},
            )

    def generate_variant_files(
        self,
        variant_name: str,
        target_dir: Path,
        renderer: TemplateRenderer,
        context: Mapping[str, Any],
    ) -> None:
        plugin = self._resolve_plugin(variant_name)
        self._validate_requirements(plugin, variant_name)

        try:
            plugin.pre_generation_hook(target_dir)
        except (RuntimeError, OSError) as exc:
            self.raise_error(
                f"Pre-generation hook failed for framework '{variant_name}': {exc}",
                context={"framework": variant_name, "error": str(exc)},
            )

        template_mappings = plugin.get_template_mappings()
        output_paths = plugin.get_output_paths()

        plugin_context = self.apply_variant_context_pre(dict(context), variant_name=variant_name)
        enriched_context = plugin.get_context_enrichments(plugin_context)
        enriched_context = self.apply_variant_context_post(
            enriched_context, variant_name=variant_name
        )

        for logical_name, template_ref in template_mappings.items():
            template_full_path = self.resolve_template_path(template_ref)
            if not template_full_path.exists():
                self.raise_error(
                    f"Plugin template '{template_ref}' not found for framework '{variant_name}'.",
                    context={
                        "framework": variant_name,
                        "template_path": str(template_full_path),
                        "logical_name": logical_name,
                    },
                )

            output_relative = output_paths.get(logical_name)
            if not output_relative:
                self.raise_error(
                    f"Plugin '{variant_name}' missing output path for '{logical_name}'.",
                    context={"framework": variant_name, "logical_name": logical_name},
                )

            if logical_name == "ci" and not enriched_context.get("include_ci", True):
                continue

            output_path = target_dir / output_relative
            try:
                rendered = renderer.render(template_full_path, enriched_context)
                snippet_context = self.build_snippet_context(
                    enriched_context=enriched_context,
                    base_context=context,
                    variant_name=variant_name,
                    logical_name=logical_name,
                    output_relative=output_relative,
                )
                features = enriched_context.get("enabled_features")
                if features is None:
                    features = context.get("enabled_features")
                if features is None:
                    features = []
                rendered_snippets = self.snippet_registry.render_for_target(
                    project_root=self.project_root,
                    target=output_relative,
                    variant=variant_name,
                    context=snippet_context,
                    enabled_features=features,
                )
                if rendered_snippets:
                    rendered = apply_snippets(rendered, rendered_snippets)
                write_file(output_path, rendered)
            except (RuntimeError, OSError, ValueError, TypeError, ModuleGeneratorError) as exc:
                self.raise_error(
                    f"Failed to generate '{logical_name}' for framework '{variant_name}': {exc}",
                    context={
                        "framework": variant_name,
                        "logical_name": logical_name,
                        "template_path": str(template_full_path),
                        "output_path": str(output_path),
                    },
                )

        try:
            plugin.post_generation_hook(target_dir)
        except (RuntimeError, OSError) as exc:
            print(f"⚠️  Post-generation hook failed for '{variant_name}': {exc}")

        self._copy_vendor_configuration_if_needed(
            target_dir=target_dir,
            context=context,
            enriched_context=enriched_context,
        )

        self.post_variant_generation(
            variant_name=variant_name,
            target_dir=target_dir,
            enriched_context=enriched_context,
        )

        # Canonical health layout enforcement (FastAPI projects).
        # - Ensure vendor-backed health shim exists under `src/health/<name>.py`.
        # - Ensure health package scaffold exists under `src/health/`.
        # - Remove any module-local `src/modules/<slug>/health/**` outputs.
        base_variant = variant_name.split(".", 1)[0]
        if base_variant == "fastapi":
            try:
                from modules.shared.utils.health import (
                    ensure_health_package,
                    ensure_vendor_health_shim,
                )
                from modules.shared.utils.health_specs import build_standard_health_spec

                ensure_health_package(target_dir)
                spec = build_standard_health_spec(self.module_root)
                ensure_vendor_health_shim(target_dir, spec=spec)
            except (RuntimeError, OSError, ValueError, TypeError):  # pragma: no cover - best-effort
                spec = None

            # Only remove module-local health outputs when the canonical shim can be created.
            if spec is not None:
                parts = list(self.module_root.parts)
                module_parts: list[str] = []
                if "modules" in parts:
                    idx = parts.index("modules")
                    module_parts = parts[idx + 1 :]
                if module_parts:
                    module_base = target_dir / "src" / "modules" / Path(*module_parts)
                    module_health = module_base / "health"
                    if module_health.exists():
                        shutil.rmtree(module_health, ignore_errors=True)

        if base_variant == "nestjs":
            # NestJS canonical rules:
            # - No nested duplicate directory under the module base.
            # - No health artifacts under `src/modules/<slug>/**`.
            #   Move health TS artifacts to `src/health/**` and rewrite relative imports.

            parts = list(self.module_root.parts)
            nest_module_parts: list[str] = []
            if "modules" in parts:
                idx = parts.index("modules")
                nest_module_parts = parts[idx + 1 :]

            if nest_module_parts:
                module_base = target_dir / "src" / "modules" / Path(*nest_module_parts)
                if module_base.exists():
                    module_leaf = nest_module_parts[-1]
                    kebab_leaf = module_leaf.replace("_", "-")

                    nested_candidates = [
                        module_base / kebab_leaf,
                        module_base / module_leaf,
                    ]

                    # Flatten nested duplicates (e.g. ai_assistant/ai-assistant/*)
                    for nested in nested_candidates:
                        if not nested.exists() or not nested.is_dir():
                            continue
                        if nested.resolve() == module_base.resolve():
                            continue
                        try:
                            for child in list(nested.iterdir()):
                                destination = module_base / child.name
                                if destination.exists():
                                    continue
                                shutil.move(str(child), str(destination))
                        except OSError:
                            # Best-effort; leave as-is if filesystem operations fail.
                            continue
                        try:
                            # Remove only if empty after moving.
                            if not any(nested.iterdir()):
                                nested.rmdir()
                        except OSError:
                            pass

                    health_root = target_dir / "src" / "health"
                    health_root.mkdir(parents=True, exist_ok=True)

                    def _rewrite_relative_imports(*, old_path: Path, new_path: Path) -> None:
                        try:
                            content = new_path.read_text(encoding="utf-8")
                        except OSError:
                            return

                        def _replace_spec(match: re.Match[str]) -> str:
                            prefix = match.group(1)
                            spec = match.group(2)
                            suffix = match.group(3)
                            if not isinstance(spec, str) or not spec.startswith("."):
                                return match.group(0)

                            target_abs = (old_path.parent / spec).resolve(strict=False)
                            try:
                                new_spec = os.path.relpath(
                                    str(target_abs), start=str(new_path.parent)
                                )
                            except ValueError:
                                return match.group(0)
                            new_spec = new_spec.replace("\\\\", "/")
                            if not new_spec.startswith("."):
                                new_spec = "./" + new_spec
                            return f"{prefix}{new_spec}{suffix}"

                        # Handle both ES imports and require() calls.
                        pattern = re.compile(
                            r"(from\s+['\"])([^'\"]+)(['\"])|(require\(\s*['\"])([^'\"]+)(['\"]\s*\))"
                        )

                        def _repl(match: re.Match[str]) -> str:
                            if match.group(1) is not None:
                                return _replace_spec(match)
                            # require() variant
                            prefix = match.group(4)
                            spec = match.group(5)
                            suffix = match.group(6)
                            if not isinstance(spec, str) or not spec.startswith("."):
                                return match.group(0)
                            target_abs = (old_path.parent / spec).resolve(strict=False)
                            try:
                                new_spec = os.path.relpath(
                                    str(target_abs), start=str(new_path.parent)
                                )
                            except ValueError:
                                return match.group(0)
                            new_spec = new_spec.replace("\\\\", "/")
                            if not new_spec.startswith("."):
                                new_spec = "./" + new_spec
                            return f"{prefix}{new_spec}{suffix}"

                        updated = pattern.sub(_repl, content)
                        if updated != content:
                            try:
                                new_path.write_text(updated, encoding="utf-8")
                            except OSError:
                                return

                    def _move_health_file(path: Path) -> None:
                        dest = health_root / path.name
                        if dest.exists():
                            return
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            shutil.move(str(path), str(dest))
                        except OSError:
                            return
                        _rewrite_relative_imports(old_path=path, new_path=dest)

                    # Move NestJS health artifacts into src/health.
                    for candidate in sorted(module_base.glob("**/*.health.ts")):
                        if candidate.is_file():
                            _move_health_file(candidate)
                    for suffix in ("*-health.controller.ts", "*-health.module.ts"):
                        for candidate in sorted(module_base.glob(f"**/{suffix}")):
                            if candidate.is_file():
                                _move_health_file(candidate)

                    # Remove any module-local health directories (python shims or ts artifacts).
                    for health_dir in sorted(module_base.glob("**/health")):
                        if not health_dir.is_dir():
                            continue
                        shutil.rmtree(health_dir, ignore_errors=True)

    def _copy_vendor_configuration_if_needed(
        self,
        *,
        target_dir: Path,
        context: Mapping[str, Any],
        enriched_context: Mapping[str, Any],
    ) -> None:
        try:
            if target_dir.resolve() == self.module_root.resolve():
                return
        except FileNotFoundError:
            # If the target does not exist yet we let normal copying proceed.
            pass

        vendor_relative_candidate = enriched_context.get("vendor_configuration_relative")
        if not isinstance(vendor_relative_candidate, str) or not vendor_relative_candidate.strip():
            vendor_relative_candidate = context.get("rapidkit_vendor_configuration_relative")
        if not isinstance(vendor_relative_candidate, str) or not vendor_relative_candidate.strip():
            return

        vendor_relative = Path(vendor_relative_candidate)
        if vendor_relative.is_absolute():
            return

        vendor_module = context.get("rapidkit_vendor_module", self.module_identifier)
        if not isinstance(vendor_module, str) or not vendor_module.strip():
            vendor_module = self.module_identifier

        vendor_version = context.get("rapidkit_vendor_version")
        if not isinstance(vendor_version, str) or not vendor_version.strip():
            vendor_version = str(context.get("version", "0.0.0"))

        vendor_root = context.get("rapidkit_vendor_root")
        if not isinstance(vendor_root, str) or not vendor_root.strip():
            vendor_root = self._last_vendor_root or ".rapidkit/vendor"

        vendor_source_candidate = enriched_context.get("vendor_configuration_source_relative")
        if not isinstance(vendor_source_candidate, str) or not vendor_source_candidate.strip():
            vendor_source_candidate = context.get("rapidkit_vendor_configuration_source_relative")
        if not isinstance(vendor_source_candidate, str) or not vendor_source_candidate.strip():
            vendor_source_candidate = vendor_relative_candidate

        vendor_root_path = Path(vendor_root)
        source = (
            target_dir
            / vendor_root_path
            / vendor_module
            / vendor_version
            / Path(vendor_source_candidate)
        )
        if not source.exists():
            return

        destination = target_dir / vendor_relative
        if destination.exists() and destination.samefile(source):
            return

        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source, destination)
        except (OSError, shutil.SameFileError) as exc:
            self.raise_error(
                f"Failed to copy vendor configuration '{vendor_relative.as_posix()}'.",
                context={
                    "vendor_source": str(source),
                    "vendor_destination": str(destination),
                    "error": str(exc),
                },
            )


def yaml_safe_load(stream: Any) -> Any:
    import yaml  # Local import to avoid optional dependency at module load time

    return yaml.safe_load(stream)
