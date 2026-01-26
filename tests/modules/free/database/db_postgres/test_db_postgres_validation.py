"""Module metadata validation for Db Postgres."""

from __future__ import annotations


def test_module_marked_active(module_config: dict[str, object]) -> None:
    assert module_config.get("status") in {"active", "stable"}
    assert module_config.get("access") == "free"


def test_capabilities_non_empty(module_config: dict[str, object]) -> None:
    capabilities = module_config.get("capabilities", [])  # type: ignore[assignment]
    assert isinstance(capabilities, list) and capabilities, "capabilities must be defined"


def test_testing_matrix_declares_integration(module_config: dict[str, object]) -> None:
    testing = module_config.get("testing", {})  # type: ignore[assignment]
    assert testing.get("integration_tests") is True
    assert testing.get("coverage_min", 0) >= 70
