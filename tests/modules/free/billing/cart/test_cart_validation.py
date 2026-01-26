"""Validation tests for Cart runtime and configuration."""

from __future__ import annotations

import pytest


def test_cart_config_from_mapping_merges_defaults(generated_modules) -> None:
    runtime = generated_modules["runtime"]
    config = runtime.CartConfig.from_mapping(
        {
            "defaults": {"currency": "eur", "tax_rate": "0.19", "max_unique_items": 5},
            "discount_rules": [{"code": "FALL", "percentage": "0.20"}],
        }
    )
    assert config.currency == "EUR"
    assert config.tax_rate.quantize(config.tax_rate) == config.tax_rate
    assert "FALL" in config.discount_rules


def test_add_item_with_invalid_quantity_raises(generated_modules) -> None:
    runtime = generated_modules["runtime"]
    service = runtime.CartService()
    with pytest.raises(runtime.CartValidationError):
        service.add_item("cart", sku="sku", name="name", quantity=0, unit_price="10.00")


def test_apply_unknown_discount_requires_force(generated_modules) -> None:
    runtime = generated_modules["runtime"]
    service = runtime.CartService()
    with pytest.raises(runtime.CartValidationError):
        service.apply_discount("cart", code="UNKNOWN")

    snapshot = service.apply_discount("cart", code="UNKNOWN", force=True)
    assert "UNKNOWN" in snapshot.discount_codes
