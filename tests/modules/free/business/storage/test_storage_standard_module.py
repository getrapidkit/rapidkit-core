"""Tests for standard module compliance."""

import yaml


def test_module_yaml_valid(storage_module_path):
    """Test module.yaml is valid."""
    module_yaml = storage_module_path / "module.yaml"
    with open(module_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config.get("name") == "storage"
    assert config.get("status") in ("active", "stable")
    assert config.get("tier") == "free"
    assert "fastapi" in config.get("compatibility", {}).get("frameworks", [])
    assert "nestjs" in config.get("compatibility", {}).get("frameworks", [])


def test_module_has_dependencies(storage_module_path):
    """Test module declares dependencies."""
    module_yaml = storage_module_path / "module.yaml"
    with open(module_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    deps = config.get("dependencies", [])
    assert len(deps) > 0


def test_module_has_documentation(storage_module_path):
    """Test module has documentation."""
    module_yaml = storage_module_path / "module.yaml"
    with open(module_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    docs = config.get("documentation", {})
    assert docs.get("readme") is not None
