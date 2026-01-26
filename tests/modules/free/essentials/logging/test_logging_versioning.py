"""Versioning check for logging module."""

from pathlib import Path

import yaml

from modules.free.essentials.logging import generate


def test_module_version_present() -> None:
    config_path = Path(generate.MODULE_ROOT) / "module.yaml"
    config = yaml.safe_load(config_path.read_text())
    version = config.get("version")
    assert version and isinstance(version, str)
