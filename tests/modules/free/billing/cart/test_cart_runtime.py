"""Runtime tests for the Cart service."""

from __future__ import annotations

from decimal import Decimal

import pytest


@pytest.fixture()
def cart_service(generated_modules):
    runtime = generated_modules["runtime"]
    config = runtime.CartConfig.from_mapping(
        {
            "defaults": {
                "currency": "USD",
                "tax_rate": "0.10",
                "default_discount_code": "WELCOME10",
                "auto_apply_default_discount": True,
                "metadata": {"owner": "tests"},
            },
            "discount_rules": [
                {"code": "WELCOME10", "percentage": "0.10", "description": "Welcome"},
                {"code": "VIP", "amount": "15.00", "description": "VIP credit"},
            ],
        }
    )
    return runtime.CartService(config)


def test_add_item_accumulates_totals(cart_service) -> None:
    snapshot = cart_service.add_item(
        "cart-1",
        sku="widget",
        name="Widget",
        quantity=2,
        unit_price="10.00",
        currency="usd",
    )
    assert snapshot.totals.subtotal == Decimal("20.00")
    assert snapshot.totals.item_count == 2
    assert snapshot.discount_codes == ["WELCOME10"]

    snapshot = cart_service.apply_discount("cart-1", "VIP", force=False)
    assert sorted(snapshot.discount_codes) == ["VIP", "WELCOME10"]
    assert snapshot.totals.discount_total > 0


def test_update_and_remove_item(cart_service, generated_modules) -> None:
    cart_service.add_item("cart-2", sku="alpha", name="Alpha", quantity=1, unit_price="5.00")
    cart_service.add_item("cart-2", sku="beta", name="Beta", quantity=3, unit_price="7.00")
    snapshot = cart_service.update_item("cart-2", sku="beta", quantity=2, unit_price="8.00")
    assert snapshot.totals.item_count == 3
    assert any(item.sku == "beta" and item.quantity == 2 for item in snapshot.items)

    snapshot = cart_service.remove_item("cart-2", sku="alpha")
    assert all(item.sku != "alpha" for item in snapshot.items)


def test_replace_items_validates(cart_service, generated_modules) -> None:
    runtime = generated_modules["runtime"]
    types = generated_modules["types"]
    with pytest.raises(runtime.CartValidationError):
        cart_service.replace_items(
            "cart-3",
            items=[
                types.CartItem(
                    sku="neg",
                    name="Negative",
                    quantity=-1,
                    unit_price=Decimal("1.00"),
                    currency="USD",
                ),
            ],
        )


def test_remove_missing_item_raises(cart_service, generated_modules) -> None:
    runtime = generated_modules["runtime"]
    with pytest.raises(runtime.CartItemNotFoundError):
        cart_service.remove_item("unknown", sku="ghost")
