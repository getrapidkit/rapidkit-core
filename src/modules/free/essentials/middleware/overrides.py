"""Override contracts for Middleware module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from core.services.override_contracts import ConfigurableOverrideMixin


class MiddlewareOverrides(ConfigurableOverrideMixin):
    """
    Extend or customize generated behaviour for Middleware module.

    This class allows projects to override default context values,
    add custom template processing, or inject additional middleware logic.
    """

    def __init__(self, module_root: Path) -> None:
        super().__init__()
        self.module_root = module_root

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        """
        Override or extend base context for all variants.

        Example:
            Add custom middleware configurations or feature flags.
        """
        return dict(context)

    def apply_variant_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        """
        Override or extend context for specific framework variants.

        Example:
            Add framework-specific middleware configurations.
        """
        return dict(context)
