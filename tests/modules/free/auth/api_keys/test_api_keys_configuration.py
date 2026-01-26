"""Configuration defaults sanity checks for Api Keys."""

from __future__ import annotations

import yaml


def test_base_config_defaults(module_root) -> None:
    config_path = module_root / "config/base.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert data.get("defaults", {}).get("enabled") is True
    assert "retry_attempts" in data.get("defaults", {})
