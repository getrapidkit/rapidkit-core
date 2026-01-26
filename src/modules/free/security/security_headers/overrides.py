"""Override contracts for Security Headers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from core.services.override_contracts import ConfigurableOverrideMixin


class SecurityHeadersOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Security Headers."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return dict(context)

    def apply_variant_context_pre(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        _ = variant_name
        return dict(context)

    def apply_variant_context_post(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        _ = variant_name
        return dict(context)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:
        _ = (variant_name, target_dir, enriched_context)
