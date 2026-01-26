"""Configuration defaults sanity checks for Security Headers."""

from __future__ import annotations

import yaml


def test_base_config_defaults(module_root) -> None:
    config_path = module_root / "config/base.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})
    assert defaults.get("enabled") is True
    hsts = defaults.get("strict_transport_security", {})
    expected_max_age = 63072000
    assert hsts.get("max_age") == expected_max_age
    assert defaults.get("x_frame_options") == "DENY"
    assert defaults.get("x_content_type_options") == "nosniff"
