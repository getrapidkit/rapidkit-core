"""Tests for configuration management."""

import yaml

MAX_FILE_SIZE = 104857600


def test_base_config_valid(storage_module_path):
    """Test base.yaml is valid."""
    config_file = storage_module_path / "config/base.yaml"
    with open(config_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    storage_cfg = config.get("storage")
    assert storage_cfg is not None
    assert storage_cfg["local"]["max_file_size"] == MAX_FILE_SIZE


def test_snippets_config_valid(storage_module_path):
    """Test snippets.yaml is valid."""
    config_file = storage_module_path / "config/snippets.yaml"
    with open(config_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "snippets" in config
    assert any(snippet["id"] == "storage_env" for snippet in config["snippets"])
