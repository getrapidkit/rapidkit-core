"""Override scaffolding tests for Inventory."""

from __future__ import annotations

from pathlib import Path

from src.modules.free.billing.inventory.overrides import InventoryOverrides, resolve_override_state


def test_override_class_declared(module_root: Path) -> None:
    overrides_source = (module_root / "overrides.py").read_text(encoding="utf-8")
    assert "class InventoryOverrides" in overrides_source


def test_apply_base_context_respects_env(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDKIT_INVENTORY_DEFAULT_CURRENCY", "EUR")
    monkeypatch.setenv("RAPIDKIT_INVENTORY_LOW_STOCK_THRESHOLD", "2")
    overrides = InventoryOverrides()
    context = {
        "inventory_defaults": {
            "default_currency": "usd",
            "low_stock_threshold": 5,
        }
    }
    mutated = overrides.apply_base_context(context)
    assert mutated["inventory_defaults"]["default_currency"] == "eur"
    assert mutated["inventory_defaults"]["low_stock_threshold"] == 2


def test_json_overrides_merge(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDKIT_INVENTORY_WAREHOUSES", '{"satellite": {"location": "staging"}}')
    overrides = InventoryOverrides()
    context = {"inventory_warehouses": {"primary": {"location": "global"}}}
    mutated = overrides.apply_base_context(context)
    assert "satellite" in mutated["inventory_warehouses"]
    assert mutated["inventory_warehouses"]["primary"]["location"] == "global"


def test_resolve_override_state_handles_missing_path(tmp_path: Path) -> None:
    state = resolve_override_state(tmp_path)
    assert state.default_currency is None
