"""Health helper tests for Inventory."""

from __future__ import annotations

import importlib


def test_health_payload_adapts_status(inventory_service, vendor_import_path) -> None:
    health_module = importlib.import_module("src.health.inventory")
    inventory_service.upsert_item(sku="sku-health", name="Health", quantity=1, price="2.00")
    payload = health_module.build_health_payload(service=inventory_service)
    assert payload["module"] == "inventory"
    assert payload["status"] == "degraded"


def test_health_helper_includes_metadata(inventory_service, vendor_import_path) -> None:
    health_module = importlib.import_module("src.health.inventory")
    inventory_service.config.enabled = False
    payload = health_module.build_health_payload(service=inventory_service)
    assert payload["status"] == "disabled"
    assert "checked_at" in payload
