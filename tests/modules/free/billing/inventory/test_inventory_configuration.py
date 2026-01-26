"""Configuration defaults sanity checks for Inventory."""

from __future__ import annotations

import yaml


def test_base_config_defaults(module_root) -> None:
    config_path = module_root / "config/base.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})
    assert defaults.get("enabled") is True
    assert defaults.get("default_currency") == "usd"
    assert defaults.get("low_stock_threshold") == 5
    assert data.get("warehouses", {}).get("primary") is not None


def test_snippet_catalog_contains_recipes(module_root) -> None:
    snippets_path = module_root / "config/snippets.yaml"
    data = yaml.safe_load(snippets_path.read_text(encoding="utf-8"))
    snippets = data.get("snippets", [])
    names = {entry.get("name") for entry in snippets}
    assert "restock-webhook" in names
    assert "multi-warehouse" in names


def test_base_context_merges_defaults(base_context) -> None:
    defaults = base_context["inventory_defaults"]
    notifications = base_context["inventory_notifications"]
    assert defaults["reservation_expiry_minutes"] >= 0
    assert notifications["enabled"] is True
