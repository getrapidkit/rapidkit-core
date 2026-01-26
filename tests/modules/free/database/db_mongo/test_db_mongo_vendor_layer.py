"""Vendor layer coverage for Db Mongo."""

from __future__ import annotations


def test_vendor_generation_configuration(module_config: dict[str, object]) -> None:
    vendor = module_config.get("generation", {}).get("vendor", {})  # type: ignore[assignment]
    assert isinstance(vendor, dict)
    assert vendor.get("root")
    files = vendor.get("files", [])
    assert isinstance(files, list) and files, "vendor files must be declared"


def test_snippet_configuration_enabled(module_config: dict[str, object]) -> None:
    snippets_cfg = module_config.get("generation", {}).get("snippets", {})  # type: ignore[assignment]
    assert isinstance(snippets_cfg, dict)
    assert snippets_cfg.get("enabled") is True
    assert snippets_cfg.get("config") == "config/snippets.yaml"
