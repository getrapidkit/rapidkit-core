"""Shared helpers for building health shim specifications."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from .health import HealthShimSpec


def load_module_config(module_root: Path) -> dict[str, Any]:
    """Load the module.yaml payload for a module root."""

    config_path = module_root / "module.yaml"
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(payload, Mapping):
        return {}
    return dict(payload)


def infer_vendor_relative(config: Mapping[str, Any], suffix: str) -> str:
    """Infer vendor relative path by matching template suffix."""

    vendor_cfg = config.get("generation", {}).get("vendor", {})
    files_cfg = vendor_cfg.get("files", [])
    for entry in files_cfg:
        if not isinstance(entry, Mapping):
            continue
        template_name = entry.get("template")
        relative = entry.get("relative")
        if not isinstance(relative, str):
            continue
        suffix_name = Path(suffix).name
        candidate_name = Path(relative).name
        if candidate_name == suffix_name:
            return relative
        if isinstance(template_name, str):
            template_basename = Path(template_name).name
            if template_basename.endswith(suffix_name) or template_basename == suffix_name:
                return relative
    return suffix


def build_vendor_health_spec(
    module_root: Path,
    *,
    vendor_template_basename: str,
    target_relative_path: str,
    # alias_relative_path removed — we emit canonical target only
    module_name_override: str | None = None,
    slug_override: str | None = None,
) -> HealthShimSpec:
    """Construct a HealthShimSpec for the given module."""

    config = load_module_config(module_root)
    raw_module_name = module_name_override or str(
        config.get("name") or module_root.name or "module"
    )
    vendor_version = str(config.get("version", "0.0.0") or "0.0.0")
    module_identifier = raw_module_name.split("/")[-1].replace("-", "_") or raw_module_name
    slug = slug_override or module_identifier.replace("_", "-")
    vendor_relative_path = infer_vendor_relative(config, vendor_template_basename)

    return HealthShimSpec(
        module_name=module_identifier,
        vendor_module=raw_module_name,
        vendor_version=vendor_version,
        vendor_relative_path=vendor_relative_path,
        target_relative_path=target_relative_path,
        # legacy alias removed; keep canonical only
        slug=slug,
    )


def _normalise_identifier(value: str) -> str:
    slug = value.split("/")[-1].strip()
    if not slug:
        return "module"
    return slug.replace("-", "_")


def build_standard_health_spec(
    module_root: Path,
    *,
    module_name_override: str | None = None,
    slug_override: str | None = None,
) -> HealthShimSpec:
    """Construct a HealthShimSpec using conventional targets derived from module metadata.

    Notes
    -----
    Modules historically used different naming conventions for their health templates
    (e.g. `core_health.py.j2` instead of `<module>_health.py.j2`). To keep the
    vendor-backed shim reliable, we infer the vendor health runtime by:

    1) Looking for an explicit `vendor_health_relative` in any variant context.
    2) Falling back to vendor `generation.vendor.files` entries containing `/health/`.
    3) Falling back to the old template-basename heuristic.

    The shim is always generated under `src/health/<health_module>.py`, where
    `<health_module>` is derived from the inferred vendor health runtime filename.
    """

    config = load_module_config(module_root)
    raw_name = module_name_override or str(config.get("name") or module_root.name or "module")

    inferred_vendor_relative: str | None = None

    variants = config.get("generation", {}).get("variants", {})
    if isinstance(variants, Mapping):
        for _variant, variant_cfg in variants.items():
            if not isinstance(variant_cfg, Mapping):
                continue
            context = variant_cfg.get("context")
            if not isinstance(context, Mapping):
                continue
            candidate = context.get("vendor_health_relative")
            if isinstance(candidate, str) and candidate.strip():
                inferred_vendor_relative = candidate.strip()
                break

    if not inferred_vendor_relative:
        vendor_cfg = config.get("generation", {}).get("vendor", {})
        files_cfg = vendor_cfg.get("files", [])
        candidates: list[str] = []
        for entry in files_cfg:
            if not isinstance(entry, Mapping):
                continue
            rel = entry.get("relative")
            if not isinstance(rel, str):
                continue
            rel_norm = rel.replace("\\", "/")
            if "/health/" not in rel_norm:
                continue
            if not rel_norm.endswith(".py"):
                continue
            if rel_norm.endswith("/__init__.py"):
                continue
            candidates.append(rel_norm)
        if len(candidates) == 1:
            inferred_vendor_relative = candidates[0]
        elif candidates:
            # Prefer a candidate that includes the module slug, otherwise pick the shortest.
            module_hint = _normalise_identifier(raw_name)
            preferred = [c for c in candidates if f"/{module_hint}/" in c]
            inferred_vendor_relative = sorted(preferred or candidates, key=lambda v: (len(v), v))[0]

    if not inferred_vendor_relative:
        # Final fallback: legacy template name convention.
        module_identifier = _normalise_identifier(raw_name)
        vendor_template_basename = f"{module_identifier}_health.py.j2"
        inferred_vendor_relative = infer_vendor_relative(config, vendor_template_basename)

    health_module = Path(inferred_vendor_relative).name
    health_identifier = _normalise_identifier(Path(health_module).stem)

    # Some legacy modules ship a vendor health runtime named `<module>_health.py`
    # outside of a `/health/` directory (e.g. `runtime/.../notifications_health.py`).
    # Canonical public shims should live at `src/health/<module>.py` and expose
    # `register_<module>_health` (not `register_<module>_health_health`).
    if health_identifier.endswith("_health") and health_identifier != "health":
        health_identifier = health_identifier[: -len("_health")]
    slug = slug_override or health_identifier.replace("_", "-")

    return HealthShimSpec(
        module_name=health_identifier,
        vendor_module=str(config.get("name") or raw_name),
        vendor_version=str(config.get("version", "0.0.0") or "0.0.0"),
        vendor_relative_path=inferred_vendor_relative,
        target_relative_path=f"src/health/{health_identifier}.py",
        slug=slug,
    )


__all__ = [
    "build_standard_health_spec",
    "build_vendor_health_spec",
    "infer_vendor_relative",
    "load_module_config",
]
