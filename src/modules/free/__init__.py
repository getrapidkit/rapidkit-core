"""
Free Modules Registry
Handles loading and management of free modules from the centralized registry.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import yaml


class FreeModulesRegistry:
    """Registry for managing free modules."""

    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            # Default path relative to this file
            current_dir = Path(__file__).parent
            registry_path = str(current_dir / "modules.yaml")

        self.registry_path = Path(registry_path)
        self.templates_path = self.registry_path.parent
        self._modules: Optional[Dict[str, Any]] = None
        self._categories: Optional[Dict[str, Any]] = None
        self._priorities: Optional[Dict[str, Any]] = None
        self._kit_support: Optional[Dict[str, Dict[str, str]]] = None

    def load_registry(self) -> Dict[str, Any]:
        """Load the modules registry from YAML file."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Modules registry not found: {self.registry_path}")

        with open(self.registry_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if raw is None:
            raw = {}

        if not isinstance(raw, dict):
            raise TypeError(
                f"Invalid modules registry format: expected a mapping at top level, got {type(raw).__name__}"
            )

        data = cast(Dict[str, Any], raw)

        self._modules = data.get("modules", {})
        self._categories = data.get("categories", {})
        self._priorities = data.get("priorities", {})
        kit_support_raw = data.get("kit_support", {}) or {}
        if not isinstance(kit_support_raw, dict):
            kit_support_raw = {}
        # ensure nested dictionaries of strings
        normalized_support: Dict[str, Dict[str, str]] = {}
        for module_name, support_map in kit_support_raw.items():
            if isinstance(support_map, dict):
                normalized_support[module_name] = {str(k): str(v) for k, v in support_map.items()}
        self._kit_support = normalized_support

        return data

    @property
    def modules(self) -> Dict[str, Any]:
        """Get all modules."""
        if self._modules is None:
            self.load_registry()
        return self._modules or {}

    @property
    def categories(self) -> Dict[str, Any]:
        """Get all categories."""
        if self._categories is None:
            self.load_registry()
        return self._categories or {}

    @property
    def priorities(self) -> Dict[str, Any]:
        """Get all priorities."""
        if self._priorities is None:
            self.load_registry()
        return self._priorities or {}

    @property
    def kit_support(self) -> Dict[str, Dict[str, str]]:
        """Get module kit compatibility mapping."""
        if self._kit_support is None:
            self.load_registry()
        return self._kit_support or {}

    def get_module(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific module by name."""
        return self.modules.get(name)

    def get_modules_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all modules in a specific category."""
        return [module for module in self.modules.values() if module.get("category") == category]

    def get_modules_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """Get all modules with a specific priority."""
        return [module for module in self.modules.values() if module.get("priority") == priority]

    def get_kit_support(self, module_name: str) -> Dict[str, str]:
        """Return kit compatibility info for a module (may be empty)."""
        support = self.kit_support.get(module_name, {})
        return dict(support)

    def get_kit_status(self, module_name: str, profile: str) -> Optional[str]:
        """Return compatibility status string for module/profile if available."""
        support = self.get_kit_support(module_name)
        if not support:
            return None
        # Accept profile variants like fastapi.standard -> fastapi/standard
        normalized_keys = {k.replace("/", "."): v for k, v in support.items()}
        if profile in support:
            return str(support[profile])
        if profile in normalized_keys:
            return str(normalized_keys[profile])
        dotted = profile.replace("/", ".")
        slashed = profile.replace(".", "/")
        if dotted in normalized_keys:
            return str(normalized_keys[dotted])
        if slashed in support:
            return str(support[slashed])
        return None

    def get_essential_modules(self) -> List[Dict[str, Any]]:
        """Get all essential modules that should be installed by default."""
        return self.get_modules_by_priority("essential")

    def get_template_path(self, module_name: str, template_file: str) -> Optional[Path]:
        """Get the full path to a module template file."""
        module = self.get_module(module_name)
        if not module:
            return None

        templates_path = module.get("templates_path", "")
        if templates_path:
            template_path = self.templates_path / templates_path / "templates" / template_file
        else:
            template_path = self.templates_path / "templates" / template_file

        return template_path if template_path.exists() else None

    def validate_module_dependencies(self, module_names: List[str]) -> List[str]:
        """Validate that all manifest dependencies for the given modules are satisfied.

        Source-of-truth is `module.yaml` (manifest `depends_on` using canonical slugs).
        """

        from core.services.module_manifest import (  # local import to avoid import-time side-effects
            DependencyCycleError,
            DependencyResolutionError,
            compute_install_order,
            load_all_manifests,
        )

        modules_root = self.templates_path.parent
        manifests = load_all_manifests(modules_root)

        selected_slugs: set[str] = set()
        missing: list[str] = []

        for name in module_names:
            resolved = self._resolve_module_slug(name, manifests)
            if not resolved:
                missing.append(f"Module '{name}' not found")
                continue
            selected_slugs.add(resolved)

        # For each selected module, ensure all transitive deps are selected
        for slug in sorted(selected_slugs):
            try:
                ordered = compute_install_order([slug], manifests)
            except (DependencyResolutionError, DependencyCycleError) as exc:
                missing.append(str(exc))
                continue
            deps = [m.slug for m in ordered if m.slug and m.slug != slug]
            for dep_slug in deps:
                if dep_slug not in selected_slugs:
                    missing.append(f"Module '{slug}' requires '{dep_slug}'")

        return missing

    def get_install_order(self, module_names: List[str]) -> List[str]:
        """Get the correct installation order considering manifest dependencies.

        Returns canonical slugs suitable for `rapidkit add module <slug>`.
        """

        from core.services.module_manifest import (  # local import to avoid import-time side-effects
            DependencyCycleError,
            DependencyResolutionError,
            compute_install_order,
            load_all_manifests,
        )

        modules_root = self.templates_path.parent
        manifests = load_all_manifests(modules_root)

        targets: list[str] = []
        for name in module_names:
            resolved = self._resolve_module_slug(name, manifests)
            if resolved:
                targets.append(resolved)

        if not targets:
            return []

        try:
            ordered = compute_install_order(targets, manifests)
        except (DependencyResolutionError, DependencyCycleError):
            # If the dependency graph is broken, fall back to deterministic target order.
            # (Caller can surface details via validate_module_dependencies.)
            return targets

        return [m.slug for m in ordered if m.slug]

    def _resolve_module_slug(self, name: str, manifests: Dict[str, Any]) -> Optional[str]:
        """Resolve a registry name or slug into a canonical manifest slug."""

        candidate = str(name).strip("/")
        if "/" in candidate and candidate in manifests:
            return candidate

        # Prefer registry templates_path mapping when available (free/<templates_path>)
        module = self.get_module(candidate)
        if isinstance(module, dict):
            templates_path = module.get("templates_path")
            if isinstance(templates_path, str) and templates_path.strip():
                slug = f"free/{templates_path.strip().strip('/')}"
                if slug in manifests:
                    return slug

        # Finally, try matching manifest.name == candidate (only if unique)
        matched = [slug for slug, m in manifests.items() if getattr(m, "name", None) == candidate]
        if len(matched) == 1:
            return matched[0]

        return None


# Global registry instance
registry = FreeModulesRegistry()


def get_registry() -> FreeModulesRegistry:
    """Get the global modules registry instance."""
    return registry


def list_available_modules() -> List[str]:
    """Get list of all available module names."""
    return list(registry.modules.keys())


def get_module_info(name: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific module."""
    return registry.get_module(name)
