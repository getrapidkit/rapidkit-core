"""Versioning check for observability_core module."""

from pathlib import Path

import yaml

from modules.free.observability.core import generate


def test_module_version_present() -> None:
    cfg = yaml.safe_load((Path(generate.MODULE_ROOT) / "module.yaml").read_text())
    version = cfg.get("version")
    assert version and isinstance(version, str)
