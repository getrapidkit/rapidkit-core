"""Error handling tests for the Cart runtime."""

from __future__ import annotations

import pytest


def test_remove_discount_not_applied_raises(generated_modules) -> None:
    runtime = generated_modules["runtime"]
    service = runtime.CartService()
    with pytest.raises(runtime.CartValidationError):
        service.remove_discount("cart", "WELCOME")


def test_unique_item_cap_enforced(generated_modules) -> None:
    runtime = generated_modules["runtime"]
    service = runtime.CartService(runtime.CartService().config)
    service.config.max_unique_items = 1
    service.add_item("cap", sku="A", name="A", quantity=1, unit_price="1.00")
    with pytest.raises(runtime.CartValidationError):
        service.add_item("cap", sku="B", name="B", quantity=1, unit_price="2.00")
