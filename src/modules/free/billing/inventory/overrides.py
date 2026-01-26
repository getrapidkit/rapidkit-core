"""Environment-aware overrides for the Inventory module."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin


@dataclass(frozen=True)
class InventoryOverrideState:
    """Snapshot of environment overrides driving Inventory defaults."""

    default_currency: Optional[str] = None
    allow_backorders: Optional[bool] = None
    allow_negative_inventory: Optional[bool] = None
    low_stock_threshold: Optional[int] = None
    reservation_expiry: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None
    warehouses: Optional[dict[str, Any]] = None
    notifications: Optional[dict[str, Any]] = None


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_bool(name: str) -> Optional[bool]:
    raw = _get_env(name)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return None


def _parse_int(name: str) -> Optional[int]:
    raw = _get_env(name)
    if raw is None:
        return None
    try:
        parsed = int(raw)
    except ValueError:
        return None
    return parsed


def _parse_json(name: str) -> Optional[dict[str, Any]]:
    raw = _get_env(name)
    if raw is None:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def resolve_override_state(_: Path) -> InventoryOverrideState:
    return InventoryOverrideState(
        default_currency=_get_env("RAPIDKIT_INVENTORY_DEFAULT_CURRENCY"),
        allow_backorders=_parse_bool("RAPIDKIT_INVENTORY_ALLOW_BACKORDERS"),
        allow_negative_inventory=_parse_bool("RAPIDKIT_INVENTORY_ALLOW_NEGATIVE"),
        low_stock_threshold=_parse_int("RAPIDKIT_INVENTORY_LOW_STOCK_THRESHOLD"),
        reservation_expiry=_parse_int("RAPIDKIT_INVENTORY_RESERVATION_TTL"),
        metadata=_parse_json("RAPIDKIT_INVENTORY_METADATA"),
        warehouses=_parse_json("RAPIDKIT_INVENTORY_WAREHOUSES"),
        notifications=_parse_json("RAPIDKIT_INVENTORY_NOTIFICATIONS"),
    )


class InventoryOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Inventory."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        state = resolve_override_state(self.module_root)
        mutated = dict(context)

        defaults = dict(mutated.get("inventory_defaults", {}))
        if state.default_currency:
            defaults["default_currency"] = state.default_currency.lower()
        if state.allow_backorders is not None:
            defaults["allow_backorders"] = state.allow_backorders
        if state.allow_negative_inventory is not None:
            defaults["allow_negative_inventory"] = state.allow_negative_inventory
        if state.low_stock_threshold is not None:
            defaults["low_stock_threshold"] = max(state.low_stock_threshold, 0)
        if state.reservation_expiry is not None:
            defaults["reservation_expiry_minutes"] = max(state.reservation_expiry, 0)
        if state.metadata:
            metadata = dict(defaults.get("metadata", {}))
            metadata.update(state.metadata)
            defaults["metadata"] = metadata
        mutated["inventory_defaults"] = defaults

        if state.warehouses:
            warehouses = dict(mutated.get("inventory_warehouses", {}))
            warehouses.update(state.warehouses)
            mutated["inventory_warehouses"] = warehouses

        if state.notifications:
            notifications = dict(mutated.get("inventory_notifications", {}))
            notifications.update(state.notifications)
            mutated["inventory_notifications"] = notifications

        mutated["inventory_env_overrides"] = {
            "default_currency": state.default_currency,
            "allow_backorders": state.allow_backorders,
            "allow_negative_inventory": state.allow_negative_inventory,
            "low_stock_threshold": state.low_stock_threshold,
            "reservation_expiry": state.reservation_expiry,
        }
        return mutated

    def apply_variant_context_pre(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def apply_variant_context_post(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
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
            self._ensure_packages(target_dir)
            self._extend_src_namespace(target_dir)

    @staticmethod
    def _ensure_packages(target_dir: Path) -> None:
        src_root = target_dir / "src"
        package_paths = [
            src_root,
            src_root / "billing",
            src_root / "health",
            src_root / "routers",
            src_root / "types",
        ]
        for pkg in package_paths:
            pkg.mkdir(parents=True, exist_ok=True)
            init_file = pkg / "__init__.py"
            if not init_file.exists():
                init_file.write_text(
                    '"""Generated package scaffold for Inventory module."""\n',
                    encoding="utf-8",
                )

    @staticmethod
    def _extend_src_namespace(target_dir: Path) -> None:
        package_root = target_dir / "src"
        if not package_root.exists():
            return

        src_module = sys.modules.get("src")
        if src_module is None:
            return

        module_path = getattr(src_module, "__path__", None)
        if module_path is None:
            return

        try:
            paths = list(module_path)
        except TypeError:  # pragma: no cover - defensive
            return

        package_path = str(package_root.resolve())
        if package_path in paths:
            return

        append_path: Callable[[str], Any] | None = getattr(module_path, "append", None)
        if append_path is not None:
            append_path(package_path)
            return

        src_module.__path__ = paths + [package_path]


__all__ = [
    "InventoryOverrides",
    "InventoryOverrideState",
    "resolve_override_state",
]
