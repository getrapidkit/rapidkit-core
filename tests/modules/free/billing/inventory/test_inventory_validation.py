"""Configuration validation tests for Inventory."""

from __future__ import annotations


def test_config_factory_coerces_values(vendor_inventory_module) -> None:
    Config = vendor_inventory_module.InventoryServiceConfig
    config = Config.from_mapping(
        {
            "defaults": {
                "default_currency": "EUR",
                "allow_backorders": "true",
                "low_stock_threshold": "4",
            }
        }
    )
    assert config.default_currency == "EUR"
    assert config.allow_backorders is True
    assert config.low_stock_threshold == 4


def test_configuration_export(inventory_service) -> None:
    inventory_service.upsert_item(sku="sku-cfg", name="Cfg", quantity=2, price="1.00")
    config = inventory_service.configuration()
    assert config["default_currency"] == inventory_service.config.default_currency
    assert "warehouses" in config
