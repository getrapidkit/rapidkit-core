"""Utilities for resolving module directories in the modules tree.

This helper understands tiered module names (e.g. ``free/settings``)
and maps them to the actual directory on disk, taking into account the
registry metadata (such as ``templates_path``) used by individual tiers.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

RegistryType = Any


@lru_cache(maxsize=None)
def _get_registry_for_tier(tier: str) -> Optional[RegistryType]:
    """Return the registry instance for the requested tier, if available."""

    if tier == "free":
        try:
            from modules.free import get_registry  # Imported lazily to avoid cycles
        except ImportError:
            return None
        return get_registry()
    return None


def resolve_module_directory(modules_root: Path, module_name: str) -> Path:
    """Resolve a module name to its on-disk directory.

    The default resolution simply appends the module name to ``modules_root``.
    When the module is defined in a tier registry (e.g. ``free/settings``), we
    consult the registry metadata to map the logical name to the physical
    directory (``templates_path``).
    """

    candidate = modules_root / module_name
    if candidate.exists():
        return candidate

    tier, sep, remainder = module_name.partition("/")
    if not sep:
        # No tier prefix; nothing else to try.
        return candidate

    registry = _get_registry_for_tier(tier)
    module_slug = remainder
    templates_path: Optional[str] = None

    if registry is not None:
        module_info = registry.get_module(module_slug)
        if module_info is None and "/" in module_slug:
            parts = module_slug.split("/")
            # Prefer the most specific leaf segment first, then fallback to root for legacy cases
            for candidate_slug in (parts[-1], parts[0]):
                if candidate_slug and candidate_slug != module_slug:
                    module_info = registry.get_module(candidate_slug)
                    if module_info is not None:
                        break
        # Legacy: map essentials/* to former core registry entry when present
        if module_info is None and module_slug.startswith("essentials/"):
            module_info = registry.get_module("core")
        if module_info is not None:
            templates_path = module_info.get("templates_path")

    if templates_path:
        # Support legacy registry entries that still point to the former "core" bucket
        # by probing the canonicalized path (e.g., core -> essentials, core/ -> essentials/).
        candidates = [templates_path]
        if templates_path == "core":
            candidates.append("essentials")
        if templates_path.startswith("core/"):
            candidates.append(templates_path.replace("core/", "essentials/", 1))

        for rel in candidates:
            registry_candidate = modules_root / tier / rel
            if registry_candidate.exists():
                return registry_candidate

    # Fallback: best-effort search within the tier directory following any
    # nested path segments provided after the tier.
    tier_dir = modules_root / tier
    if tier_dir.exists():
        probe = tier_dir
        for segment in module_slug.split("/"):
            probe = probe / segment
        if probe.exists():
            return probe

    return candidate
