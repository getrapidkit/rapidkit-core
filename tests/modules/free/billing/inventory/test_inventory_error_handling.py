"""Error handling regression tests for the Inventory runtime."""

from __future__ import annotations

import pytest


def test_upsert_negative_quantity_disallowed(inventory_service, vendor_inventory_module) -> None:
    validation_error = vendor_inventory_module.InventoryValidationError
    with pytest.raises(validation_error):
        inventory_service.upsert_item(sku="sku-neg", name="Negative", quantity=-1, price="1.00")


def test_reservation_requires_existing_item(inventory_service, vendor_inventory_module) -> None:
    not_found_error = vendor_inventory_module.InventoryNotFoundError
    with pytest.raises(not_found_error):
        inventory_service.reserve_stock(sku="missing", quantity=1, reference="order-missing")
