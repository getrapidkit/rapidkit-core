"""Tests for module versioning."""

import yaml


def test_module_version(storage_module_path):
    """Test module has valid version."""
    module_yaml = storage_module_path / "module.yaml"
    with open(module_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    version = config.get("version")
    assert version is not None
    assert isinstance(version, str)
