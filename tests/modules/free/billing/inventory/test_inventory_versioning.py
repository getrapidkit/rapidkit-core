"""Versioning contract tests for Inventory."""

from __future__ import annotations

import shutil
from pathlib import Path

from modules.shared.versioning import ensure_version_consistency


def _clone_module_root(source: Path, destination: Path) -> Path:
    """Copy module contents to a scratch directory for isolation."""

    ignore_names = {"__pycache__", ".pytest_cache"}

    def _ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in ignore_names}

    shutil.copytree(source, destination, ignore=_ignore)
    return destination


def test_version_propagates_to_context(module_config, base_context) -> None:
    assert base_context["rapidkit_vendor_version"] == module_config["version"]


def test_version_consistency_check(module_generate, module_config, tmp_path) -> None:
    module_root = Path(module_generate.__file__).resolve().parent
    isolated_root = _clone_module_root(module_root, tmp_path / "inventory-module")

    config, updated = ensure_version_consistency(module_config, module_root=isolated_root)
    assert config["version"].count(".") == 2
    assert updated is False
