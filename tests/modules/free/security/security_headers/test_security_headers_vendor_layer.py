"""Vendor layer coverage for Security Headers."""

from __future__ import annotations


def test_vendor_generation_configuration(module_config: dict[str, object]) -> None:
    vendor = module_config.get("generation", {}).get("vendor", {})  # type: ignore[assignment]
    assert isinstance(vendor, dict)
    assert vendor.get("root")
    files = vendor.get("files", [])
    assert isinstance(files, list) and files, "vendor files must be declared"
