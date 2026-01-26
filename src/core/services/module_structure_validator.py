"""Utilities for validating module directory structures against the canonical spec."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, cast

import yaml

MODULES_ROOT = Path(__file__).resolve().parents[2] / "modules"
SPEC_PATH = MODULES_ROOT / "STRUCTURE.yaml"
DEFAULT_VERIFICATION_FILE = "module.verify.json"
SKIP_VERIFICATION_ENV = "RAPIDKIT_SKIP_VERIFICATION_WRITE"
VENDOR_HEALTH_MIN_SPEC_VERSION = 4


class ModuleStructureError(RuntimeError):
    """Raised when a module directory fails structure validation."""


@dataclass
class ValidationResult:
    module: str
    module_path: Path
    valid: bool
    spec_version: int
    missing_files: List[str]
    missing_directories: List[str]
    extra_files: List[str]
    extra_directories: List[str]
    verification_file: Optional[str]
    tree_hash: Optional[str]
    messages: List[str]

    def summary(self) -> str:
        if self.valid:
            return f"✔ {self.module} matches spec v{self.spec_version}"
        return f"✖ {self.module} is not compliant with spec v{self.spec_version}"


@dataclass
class StructureBlueprint:
    spec_version: int
    description: str
    verification_file: str
    allow_extra_entries: bool
    ignore_patterns: Tuple[str, ...]
    required_files: Tuple[str, ...]
    required_directories: Tuple[str, ...]
    flexible_subtrees: Tuple[str, ...]


@dataclass
class ModuleSpec:
    name: str
    spec_version: int
    description: str
    verification_file: str
    allow_extra_entries: bool
    ignore_patterns: Tuple[str, ...]
    required_files: Tuple[str, ...]
    required_directories: Tuple[str, ...]
    flexible_subtrees: Tuple[str, ...]


def _parse_spec_payload(
    payload: dict,
    spec_version: int,
    default_description: str,
    default_file: str,
    default_allow_extra: bool,
    default_ignore: Sequence[str],
    default_required_files: Sequence[str],
    default_required_dirs: Sequence[str],
    default_flexible: Sequence[str],
) -> ModuleSpec:
    description = str(payload.get("description", default_description))
    verification_file = str(payload.get("verification_file", default_file))
    allow_extra = bool(payload.get("allow_extra_entries", default_allow_extra))
    ignore_patterns = tuple(str(p) for p in payload.get("ignore_patterns", default_ignore))
    required_files = tuple(str(p) for p in payload.get("required_files", default_required_files))
    required_directories = tuple(
        str(p) for p in payload.get("required_directories", default_required_dirs)
    )
    flexible_subtrees = tuple(
        str(p).rstrip("/") for p in payload.get("flexible_subtrees", default_flexible)
    )

    return ModuleSpec(
        name="",
        spec_version=spec_version,
        description=description,
        verification_file=verification_file,
        allow_extra_entries=allow_extra,
        ignore_patterns=ignore_patterns,
        required_files=required_files,
        required_directories=required_directories,
        flexible_subtrees=flexible_subtrees,
    )


@lru_cache(maxsize=1)
def load_structure_spec(
    path: Path = SPEC_PATH,
) -> Tuple[int, StructureBlueprint, Dict[str, ModuleSpec]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Module structure spec not found at '{path}'. Please add {path.name}."
        )

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Module structure spec at '{path}' must be a mapping.")

    spec_version = int(raw.get("spec_version", 1))
    blueprint_payload = raw.get("blueprint")
    if not isinstance(blueprint_payload, dict):
        raise ValueError("'blueprint' key in structure spec must be a mapping.")

    base_spec = _parse_spec_payload(
        payload=blueprint_payload,
        spec_version=spec_version,
        default_description="",
        default_file=DEFAULT_VERIFICATION_FILE,
        default_allow_extra=False,
        default_ignore=(),
        default_required_files=(),
        default_required_dirs=(),
        default_flexible=(),
    )

    blueprint = StructureBlueprint(
        spec_version=spec_version,
        description=base_spec.description,
        verification_file=base_spec.verification_file,
        allow_extra_entries=base_spec.allow_extra_entries,
        ignore_patterns=base_spec.ignore_patterns,
        required_files=base_spec.required_files,
        required_directories=base_spec.required_directories,
        flexible_subtrees=base_spec.flexible_subtrees,
    )

    modules_map_raw = raw.get("modules", {})
    if modules_map_raw is None:
        modules_map_raw = {}
    if not isinstance(modules_map_raw, dict):
        raise ValueError("'modules' key in structure spec must be a mapping if provided.")

    parsed: Dict[str, ModuleSpec] = {}
    for module_name, spec_payload in modules_map_raw.items():
        if not isinstance(spec_payload, dict):
            raise ValueError(f"Module entry '{module_name}' must be a mapping.")
        module_spec = _parse_spec_payload(
            payload=spec_payload,
            spec_version=spec_version,
            default_description=blueprint.description,
            default_file=blueprint.verification_file,
            default_allow_extra=blueprint.allow_extra_entries,
            default_ignore=blueprint.ignore_patterns,
            default_required_files=blueprint.required_files,
            default_required_dirs=blueprint.required_directories,
            default_flexible=blueprint.flexible_subtrees,
        )
        parsed[module_name] = replace(module_spec, name=module_name)

    return spec_version, blueprint, parsed


def _matches_ignore(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _collect_directory_state(module_path: Path, spec: ModuleSpec) -> Tuple[Set[str], Set[str]]:
    files: Set[str] = set()
    directories: Set[str] = set()
    ignore_patterns = spec.ignore_patterns

    for entry in module_path.rglob("*"):
        if entry == module_path:
            continue
        relative = entry.relative_to(module_path).as_posix()
        if _matches_ignore(relative, ignore_patterns):
            if entry.is_dir():
                # Skip traversing ignored directories but don't record them
                continue
            continue
        if entry.is_dir():
            directories.add(relative)
        else:
            files.add(relative)

    return files, directories


def _module_spec_from_blueprint(module_name: str, blueprint: StructureBlueprint) -> ModuleSpec:
    base_spec = ModuleSpec(
        name=module_name,
        spec_version=blueprint.spec_version,
        description=blueprint.description,
        verification_file=blueprint.verification_file,
        allow_extra_entries=blueprint.allow_extra_entries,
        ignore_patterns=blueprint.ignore_patterns,
        required_files=blueprint.required_files,
        required_directories=blueprint.required_directories,
        flexible_subtrees=blueprint.flexible_subtrees,
    )
    return _render_module_spec(base_spec, module_name)


def _is_within_flexible(path: str, prefixes: Sequence[str]) -> bool:
    for prefix in prefixes:
        if not prefix:
            continue
        if path == prefix or path.startswith(f"{prefix}/"):
            return True
    return False


def _compute_tree_hash(files: Iterable[str], directories: Iterable[str]) -> str:
    digest = hashlib.sha256()
    ordered = [f"D:{d}" for d in sorted(directories)] + [f"F:{f}" for f in sorted(files)]
    for item in ordered:
        digest.update(item.encode("utf-8"))
    return digest.hexdigest()


def _write_verification_file(module_path: Path, spec: ModuleSpec, result: ValidationResult) -> None:
    if os.getenv(SKIP_VERIFICATION_ENV):
        return

    # Skip writing verification files during tests to prevent modifying tracked files
    try:
        with open("/proc/self/cmdline", "rb") as f:
            cmdline = f.read().decode("utf-8", errors="ignore")
            if "pytest" in cmdline:
                return
    except (OSError, FileNotFoundError):
        pass

    target = module_path / spec.verification_file
    existing_payload: Optional[Dict[str, Any]] = None

    if target.exists():
        try:
            existing_text = target.read_text(encoding="utf-8")
            loaded = json.loads(existing_text)
            if isinstance(loaded, dict):
                existing_payload = cast(Dict[str, Any], loaded)
        except (OSError, json.JSONDecodeError):
            existing_payload = None

    parity_valid = False
    parity_snapshot: Optional[Dict[str, Any]] = None
    parity_notes: Optional[Iterable[str]] = None
    parity_checked_at: Optional[str] = None

    if existing_payload is not None:
        parity_valid = bool(existing_payload.get("parity_valid"))
        parity_snapshot = (
            existing_payload.get("parity")
            if isinstance(existing_payload.get("parity"), dict)
            else None
        )
        notes_value = existing_payload.get("parity_notes")
        parity_notes = notes_value if isinstance(notes_value, list) else None
        checked_value = existing_payload.get("parity_checked_at")
        parity_checked_at = checked_value if isinstance(checked_value, str) else None

    structure_tree_hash = result.tree_hash if result.valid else None

    payload = {
        "module": result.module,
        "spec_version": result.spec_version,
        "description": spec.description,
        "missing_files": result.missing_files,
        "missing_directories": result.missing_directories,
        "extra_files": result.extra_files,
        "extra_directories": result.extra_directories,
        "structure_valid": result.valid,
        "structure_tree_hash": structure_tree_hash,
        "parity_valid": parity_valid,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    if parity_snapshot is not None:
        payload["parity"] = parity_snapshot
    if parity_notes is not None:
        payload["parity_notes"] = list(parity_notes)
    if parity_checked_at is not None:
        payload["parity_checked_at"] = parity_checked_at

    payload["valid"] = payload["structure_valid"] and payload["parity_valid"]
    payload["tree_hash"] = payload["structure_tree_hash"] if payload["valid"] else None

    if existing_payload is not None:
        current_snapshot = dict(existing_payload)
        new_snapshot = dict(payload)
        current_snapshot.pop("checked_at", None)
        new_snapshot.pop("checked_at", None)

        if current_snapshot == new_snapshot:
            payload["checked_at"] = str(existing_payload.get("checked_at", payload["checked_at"]))
            serialized = json.dumps(payload, indent=2, sort_keys=True)
            if existing_text is not None and existing_text == serialized:
                return
            target.write_text(serialized, encoding="utf-8")
            return

    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _build_result(
    module_name: str,
    module_path: Path,
    spec_version: int,
    spec: ModuleSpec,
    files: Set[str],
    directories: Set[str],
) -> ValidationResult:
    expected_files = set(spec.required_files)
    expected_directories = set(spec.required_directories)

    missing_files = sorted(expected_files - files)
    missing_directories = sorted(expected_directories - directories)

    extras_files_raw = sorted(files - expected_files)
    extras_directories_raw = sorted(directories - expected_directories)

    flexible_prefixes = spec.flexible_subtrees
    extras_files = [p for p in extras_files_raw if not _is_within_flexible(p, flexible_prefixes)]
    extras_directories = [
        p for p in extras_directories_raw if not _is_within_flexible(p, flexible_prefixes)
    ]

    messages: List[str] = []
    if missing_files:
        messages.append(f"Missing files: {', '.join(missing_files)}")
    if missing_directories:
        messages.append(f"Missing directories: {', '.join(missing_directories)}")
    if (extras_files or extras_directories) and spec.allow_extra_entries:
        messages.append("Extra entries detected but allowed by spec.")

    is_valid = not missing_files and not missing_directories
    if not spec.allow_extra_entries:
        if extras_files:
            messages.append(f"Extra files present: {', '.join(extras_files)}")
            is_valid = False
        if extras_directories:
            messages.append(f"Extra directories present: {', '.join(extras_directories)}")
            is_valid = False

    tree_hash = _compute_tree_hash(files, directories) if is_valid else None

    return ValidationResult(
        module=module_name,
        module_path=module_path,
        valid=is_valid,
        spec_version=spec_version,
        missing_files=missing_files,
        missing_directories=missing_directories,
        extra_files=extras_files,
        extra_directories=extras_directories,
        verification_file=spec.verification_file,
        tree_hash=tree_hash,
        messages=messages,
    )


def _has_health_shim_candidate(module_path: Path, basename: str) -> bool:
    """Return True if module appears to provide a health shim by either:
    - including a conventional health template (templates/base or templates/variants),
    - providing a frameworks/_config.py helper that typically exposes HEALTH_SHIM_SPEC, or
    - declaring a vendor health payload in module.yaml (generation.vendor.files -> relative contains 'health').
    """

    # 1) Templates
    candidates = (
        f"templates/base/{basename}_health.py.j2",
        f"templates/variants/fastapi/{basename}_health.py.j2",
    )
    for cand in candidates:
        if (module_path / cand).exists():
            return True

    # 2) frameworks/_config.py presence (commonly used by migrated modules)
    cfg = module_path / "frameworks" / "_config.py"
    if cfg.exists():
        try:
            body = cfg.read_text(encoding="utf-8")
        except OSError:
            body = ""
        if (
            "HEALTH_SHIM_SPEC" in body
            or "HealthShimSpec" in body
            or "ensure_vendor_health_shim" in body
        ):
            return True

    # 3) module.yaml vendor generation entries
    module_yaml = module_path / "module.yaml"
    if module_yaml.exists():
        try:
            parsed = yaml.safe_load(module_yaml.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError):
            parsed = {}
        gen = parsed.get("generation", {}) if isinstance(parsed, dict) else {}
        vendor = gen.get("vendor", {}) if isinstance(gen, dict) else {}
        files = vendor.get("files", []) if isinstance(vendor, dict) else []
        for entry in files:
            if not isinstance(entry, dict):
                continue
            rel = entry.get("relative")
            if isinstance(rel, str) and "health" in rel:
                return True

    return False


def _module_declares_vendor_health(module_path: Path) -> bool:
    """Return True if module.yaml declares vendor-backed health artefacts."""
    module_yaml = module_path / "module.yaml"
    if not module_yaml.exists():
        return False
    try:
        parsed = yaml.safe_load(module_yaml.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError):
        parsed = {}
    gen = parsed.get("generation", {}) if isinstance(parsed, dict) else {}
    vendor = gen.get("vendor", {}) if isinstance(gen, dict) else {}
    files = vendor.get("files", []) if isinstance(vendor, dict) else []
    for entry in files:
        if not isinstance(entry, dict):
            continue
        rel = entry.get("relative")
        if isinstance(rel, str) and "health" in rel.lower():
            return True
    return False


def _module_generates_legacy_health_targets(module_path: Path) -> list[str]:
    """Return a list of generation targets found in module.yaml that explicitly
    target legacy 'src/core/health' locations or other 'src/core/*_health' patterns.

    This is used by validation commands to enforce the canonical-only layout
    (generated modules must target `src/health/*` rather than `src/core/*_health`).
    """
    offenders: list[str] = []
    module_yaml = module_path / "module.yaml"
    if not module_yaml.exists():
        return offenders
    try:
        parsed = yaml.safe_load(module_yaml.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError):
        # Parsing issues shouldn't silence raw text-based detection below.
        parsed = {}

    gen = parsed.get("generation", {}) if isinstance(parsed, dict) else {}

    # Vendor 'relative' entries
    vendor = gen.get("vendor", {}) if isinstance(gen, dict) else {}
    files = vendor.get("files", []) if isinstance(vendor, dict) else []
    for entry in files:
        if not isinstance(entry, dict):
            continue
        rel = entry.get("relative")
        if isinstance(rel, str) and rel.startswith("src/core/") and "health" in rel.lower():
            offenders.append(rel)

    # Variant outputs
    variants = gen.get("variants", {}) if isinstance(gen, dict) else {}
    for variant in variants.values():
        files = variant.get("files", []) or []
        for entry in files:
            if not isinstance(entry, dict):
                continue
            output = entry.get("output") or entry.get("relative")
            if (
                isinstance(output, str)
                and output.startswith("src/core/")
                and "health" in output.lower()
            ):
                offenders.append(output)

    # Fallback: raw text scan for legacy paths in non-standard YAML structures
    if not offenders:
        try:
            raw_text = module_yaml.read_text(encoding="utf-8")
        except OSError:
            raw_text = ""
        # A simple regex-like search to capture 'src/core/health' or 'src/core/<name>_health'
        if "src/core/health" in raw_text or "src/core/" in raw_text and "_health" in raw_text:
            # extract lines containing 'src/core'
            for line in raw_text.splitlines():
                if "src/core/" in line and "health" in line:
                    offenders.append(line.strip())

    return offenders


def _frameworks_call_vendor_shim(module_path: Path) -> bool:
    """Return True if any framework or generation helpers call ensure_vendor_health_shim.

    This checks common plugin files (frameworks/*.py, generate.py) for the presence
    of the invocation token so validators can verify the author wired the shim.
    """
    candidates = [
        module_path / "frameworks" / "fastapi.py",
        module_path / "frameworks" / "nestjs.py",
        module_path / "frameworks" / "_config.py",
        module_path / "generate.py",
    ]
    for p in candidates:
        if not p.exists():
            continue
        try:
            body = p.read_text(encoding="utf-8")
        except OSError:
            continue
        if "ensure_vendor_health_shim" in body:
            return True
    return False


def _render_module_spec(spec: ModuleSpec, module_name: str) -> ModuleSpec:
    slug = module_name
    basename = module_name.split("/")[-1]
    replacements = {
        "{{module_slug}}": slug,
        "{{module_basename}}": basename,
    }

    def render(value: str) -> str:
        for token, replacement in replacements.items():
            value = value.replace(token, replacement)
        return value

    def render_seq(values: Sequence[str]) -> Tuple[str, ...]:
        return tuple(render(v) for v in values)

    return ModuleSpec(
        name=module_name,
        spec_version=spec.spec_version,
        description=render(spec.description),
        verification_file=render(spec.verification_file),
        allow_extra_entries=spec.allow_extra_entries,
        ignore_patterns=render_seq(spec.ignore_patterns),
        required_files=render_seq(spec.required_files),
        required_directories=render_seq(spec.required_directories),
        flexible_subtrees=render_seq(spec.flexible_subtrees),
    )


def validate_module_structure(
    module_name: str, modules_root: Path = MODULES_ROOT
) -> ValidationResult:
    spec_version, blueprint, module_overrides = load_structure_spec()
    module_spec_template = module_overrides.get(module_name)
    if module_spec_template is None:
        module_spec = _module_spec_from_blueprint(module_name, blueprint)
    else:
        module_spec = _render_module_spec(module_spec_template, module_name)

    module_path = modules_root / module_name

    if not module_path.exists():
        result = ValidationResult(
            module=module_name,
            module_path=module_path,
            valid=False,
            spec_version=spec_version,
            missing_files=sorted(module_spec.required_files),
            missing_directories=sorted(module_spec.required_directories),
            extra_files=[],
            extra_directories=[],
            verification_file=module_spec.verification_file,
            tree_hash=None,
            messages=[f"Module directory '{module_path}' does not exist."],
        )
        return result

    files, directories = _collect_directory_state(module_path, module_spec)
    result = _build_result(module_name, module_path, spec_version, module_spec, files, directories)
    # For spec_version >= 4 we now require modules to either provide a template-based
    # health shim OR supply shim metadata / helpers (frameworks/_config.py or module.yaml vendor entry)
    if spec_version >= VENDOR_HEALTH_MIN_SPEC_VERSION:
        basename = module_name.split("/")[-1]
        if not _has_health_shim_candidate(module_path, basename):
            # Add a specific missing entry and message to guide the author
            missing_msg = (
                "module health shim missing: add templates/base/{basename}_health.py.j2 "
                "or templates/variants/fastapi/{basename}_health.py.j2, or provide frameworks/_config.py "
                "with HEALTH_SHIM_SPEC or declare vendor health in module.yaml"
            ).format(basename=basename)
            result.missing_files.append(missing_msg)
            result.messages.append(missing_msg)
            result.valid = False
        # If module declares a vendor-backed health runtime or exposes a
        # HEALTH_SHIM_SPEC, require that plugin/generator code actually
        # attempts to materialise the shim at generation time by calling
        # ensure_vendor_health_shim somewhere in the framework helpers.
        elif _module_declares_vendor_health(module_path) or (
            (module_path / "frameworks" / "_config.py").exists()
            and (module_path / "frameworks" / "_config.py")
            .read_text(encoding="utf-8")
            .find("HEALTH_SHIM_SPEC")
            >= 0
        ):
            if not _frameworks_call_vendor_shim(module_path):
                missing_msg = (
                    "vendor-backed health declared but framework plugins do not call "
                    "ensure_vendor_health_shim (add invocation in frameworks/fastapi.py, frameworks/nestjs.py, or generate.py)"
                )
                result.missing_files.append(missing_msg)
                result.messages.append(missing_msg)
                result.valid = False

    # Explicitly disallow generator targets that place health shims under
    # legacy `src/core/health` or other `src/core/*_health` patterns.
    # This validator enforces the canonical public path `src/health/*`.
    legacy_targets = _module_generates_legacy_health_targets(module_path)
    if legacy_targets:
        for t in legacy_targets:
            msg = f"generation target uses legacy path: {t} — migrate to src/health/*"
            result.messages.append(msg)
            result.missing_files.append(msg)
        result.valid = False
    _write_verification_file(module_path, module_spec, result)
    return result


def _discover_modules(modules_root: Path) -> List[str]:
    discovered = []
    for module_file in modules_root.glob("**/module.yaml"):
        try:
            slug = module_file.parent.relative_to(modules_root).as_posix()
        except ValueError:
            continue
        discovered.append(slug)
    return sorted(set(discovered))


def validate_modules(
    modules: Optional[Sequence[str]] = None,
    modules_root: Path = MODULES_ROOT,
) -> List[ValidationResult]:
    _, _blueprint, module_overrides = load_structure_spec()
    target_modules: Sequence[str]
    if modules:
        target_modules = modules
    elif module_overrides:
        target_modules = tuple(module_overrides.keys())
    else:
        target_modules = tuple(_discover_modules(modules_root))

    results = [
        validate_module_structure(name, modules_root=modules_root) for name in target_modules
    ]
    return results


def ensure_module_structure(module_name: str, modules_root: Path = MODULES_ROOT) -> None:
    result = validate_module_structure(module_name, modules_root=modules_root)
    if result.valid:
        return

    summary = result.summary()
    details = "\n".join(result.messages)
    raise ModuleStructureError(f"{summary}\n{details}")


__all__ = [
    "ValidationResult",
    "ModuleStructureError",
    "validate_module_structure",
    "validate_modules",
    "ensure_module_structure",
    "load_structure_spec",
]
