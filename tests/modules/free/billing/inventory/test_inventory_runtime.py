"""Runtime contract tests for the generated Inventory service."""

from __future__ import annotations

import pytest


def test_upsert_and_adjust_stock(inventory_service, vendor_inventory_module) -> None:
    validation_error = vendor_inventory_module.InventoryValidationError
    inventory_service.upsert_item(sku="sku-1", name="Starter", quantity=10, price="12.50")

    updated = inventory_service.adjust_stock(sku="sku-1", delta=-3)
    assert updated.quantity == 7
    assert updated.available == 7

    with pytest.raises(validation_error):
        inventory_service.adjust_stock(sku="sku-1", delta=-100)


def test_reservation_commit_flow(inventory_service, vendor_inventory_module) -> None:
    inventory_service.upsert_item(sku="sku-2", name="Reservable", quantity=5, price="9.99")

    reservation = inventory_service.reserve_stock(sku="sku-2", quantity=2, reference="order-1")
    assert reservation.quantity == 2

    inventory_service.release_reservation("order-1", commit=True)
    item = inventory_service.get_item("sku-2")
    assert item.quantity == 3
    assert item.reserved == 0

    reservation_error = vendor_inventory_module.InventoryReservationError
    with pytest.raises(reservation_error):
        inventory_service.release_reservation("order-1")


def test_health_status_reflects_low_stock(inventory_service) -> None:
    inventory_service.upsert_item(sku="sku-3", name="Low", quantity=1, price="4.50")
    health = inventory_service.health_check()
    assert health["status"] == "degraded"
    assert health["metrics"]["low_stock_items"] >= 1
