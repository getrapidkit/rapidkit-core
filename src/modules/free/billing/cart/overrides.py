"""Override contracts for the Cart module."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin


@dataclass(frozen=True)
class CartOverrideState:
    """Snapshot of environment-driven overrides for Cart defaults."""

    default_discount: Optional[str] = None
    max_unique_items: Optional[int] = None
    disable_tax: bool = False


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_int(name: str) -> Optional[int]:
    candidate = _get_env(name)
    if candidate is None:
        return None
    try:
        parsed = int(candidate)
    except ValueError:
        return None
    return max(parsed, 1)


def resolve_override_state(_: Path) -> CartOverrideState:
    return CartOverrideState(
        default_discount=_get_env("RAPIDKIT_CART_DEFAULT_DISCOUNT"),
        max_unique_items=_parse_int("RAPIDKIT_CART_MAX_UNIQUE_ITEMS"),
        disable_tax=_get_env("RAPIDKIT_CART_DISABLE_TAX") is not None,
    )


def _mutate_defaults(defaults: Mapping[str, Any], state: CartOverrideState) -> dict[str, Any]:
    mutated = dict(defaults)
    if state.default_discount:
        mutated["default_discount_code"] = state.default_discount
        mutated.setdefault("auto_apply_default_discount", True)
    if state.max_unique_items is not None:
        mutated["max_unique_items"] = state.max_unique_items
    if state.disable_tax:
        mutated["tax_rate"] = "0"
    return mutated


class CartOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Cart."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = context.get("cart_defaults", {})
        state = resolve_override_state(self.module_root)
        mutated["cart_defaults"] = _mutate_defaults(defaults, state)
        return mutated

    def apply_variant_context_pre(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def apply_variant_context_post(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:  # noqa: ARG002
        if variant_name == "fastapi":
            self._extend_src_namespace(target_dir)

    @staticmethod
    def _extend_src_namespace(target_dir: Path) -> None:
        package_root = target_dir / "src"
        if not package_root.exists():
            return

        src_module = sys.modules.get("src")
        if src_module is None:
            return

        package_path = str(package_root.resolve())
        module_path = getattr(src_module, "__path__", None)
        if module_path is None:
            return

        try:
            paths = list(module_path)
        except TypeError:
            return

        if package_path in paths:
            return

        append_path: Callable[[str], Any] | None = getattr(module_path, "append", None)
        if append_path is not None:
            append_path(package_path)
            return

        src_module.__path__ = paths + [package_path]


__all__ = [
    "CartOverrides",
    "CartOverrideState",
    "resolve_override_state",
]
