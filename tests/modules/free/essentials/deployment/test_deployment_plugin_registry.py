"""Coverage for deployment framework plugin registry utilities."""

import importlib.util

import pytest

from modules.free.essentials.deployment import frameworks


def test_plugin_registry_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    frameworks.refresh_plugin_registry(auto_discover=False)

    assert frameworks.is_plugin_available("fastapi")
    assert frameworks.is_plugin_available("nestjs")

    plugin = frameworks.get_plugin("fastapi")
    assert plugin.name == "fastapi"

    available = frameworks.list_available_plugins()
    assert "fastapi" in available and "nestjs" in available

    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())
    validation = frameworks.validate_all_plugins()
    assert all(isinstance(errors, list) for errors in validation.values())

    info = frameworks.get_plugin_info("fastapi")
    assert info is not None and info["name"] == "fastapi"
