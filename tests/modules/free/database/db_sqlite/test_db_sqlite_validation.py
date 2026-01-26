"""Module configuration validation for Db Sqlite."""

from __future__ import annotations


def test_module_marked_stable(module_config: dict[str, object]) -> None:
    assert module_config.get("status") == "stable"
    assert module_config.get("version", "").count(".") == 2


def test_capabilities_list_non_empty(module_config: dict[str, object]) -> None:
    capabilities = module_config.get("capabilities", [])  # type: ignore[assignment]
    assert isinstance(capabilities, list) and capabilities, "capabilities must be defined"
