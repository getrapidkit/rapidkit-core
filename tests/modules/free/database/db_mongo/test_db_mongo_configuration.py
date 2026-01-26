"""Configuration defaults sanity checks for Db Mongo."""

from __future__ import annotations

import yaml


def test_base_config_defaults(module_root) -> None:
    config_path = module_root / "config/base.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})
    assert defaults.get("enabled") is True
    connection = defaults.get("connection", {})
    assert connection.get("primary_uri") == "mongodb://localhost:27017"
    assert connection.get("database") == "rapidkit"
    pool = defaults.get("pool", {})
    assert pool.get("max_pool_size") == 20
