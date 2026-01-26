"""Configuration defaults sanity checks for Cart."""

from __future__ import annotations

import yaml


def test_base_config_defaults(module_root) -> None:
    config_path = module_root / "config/base.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})
    assert defaults.get("currency") == "USD"
    assert defaults.get("tax_rate") == "0.0700"
    assert defaults.get("auto_apply_default_discount") is True

    rules = data.get("discount_rules", [])
    codes = {rule.get("code") for rule in rules}
    assert {"WELCOME10", "FREESHIP"}.issubset(codes)
