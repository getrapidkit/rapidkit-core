"""Validation tests for Db Mongo framework plugins."""

from __future__ import annotations

from modules.free.database.db_mongo.frameworks import (
    list_available_plugins,
    validate_all_plugins,
)


def test_framework_plugins_registered() -> None:
    available = list_available_plugins()
    assert "fastapi" in available
    assert "nestjs" in available


def test_framework_plugin_validation_passes() -> None:
    results = validate_all_plugins()
    for name, errors in results.items():
        assert errors == [], f"Plugin {name} reported validation errors: {errors}"
