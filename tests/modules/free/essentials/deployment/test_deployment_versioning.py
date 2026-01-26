"""Versioning check for deployment module."""

from pathlib import Path

import yaml

from modules.free.essentials.deployment import generate


def test_module_version_present() -> None:
    cfg_path = Path(generate.MODULE_ROOT) / "module.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    version = cfg.get("version")
    assert version and isinstance(version, str)
