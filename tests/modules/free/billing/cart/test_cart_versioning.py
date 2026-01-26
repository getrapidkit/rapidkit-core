"""Versioning guarantees for the Cart module."""

from __future__ import annotations

import shutil
from pathlib import Path

from modules.shared.versioning import ensure_version_consistency


def _clone_module_root(source: Path, destination: Path) -> Path:
    """Copy the module directory to an isolated location for mutation-safe tests."""

    ignore_names = {"__pycache__", ".pytest_cache"}

    def _ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in ignore_names}

    shutil.copytree(source, destination, ignore=_ignore)
    return destination


def test_module_version_semver(module_config) -> None:
    version = module_config.get("version")
    assert isinstance(version, str)
    parts = version.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_version_consistency_no_bump(module_generate, module_config, tmp_path) -> None:
    module_root = Path(module_generate.__file__).resolve().parent
    isolated_root = _clone_module_root(module_root, tmp_path / "cart-module")

    updated_config, bumped = ensure_version_consistency(module_config, module_root=isolated_root)

    assert bumped is False
    assert updated_config["version"] == module_config["version"]
