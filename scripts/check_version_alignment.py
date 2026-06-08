#!/usr/bin/env python3
"""Ensure project version metadata stays in sync across tooling."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

try:  # Python >=3.11
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - CPython <3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
MANIFEST_FILES = [
    ROOT / ".release-please-manifest.json",
    ROOT / "release-please-manifest.json",
]
VERSION_MODULE = ROOT / "src" / "core" / "config" / "version.py"
MODULES_LOCK_YAML = ROOT / ".rapidkit" / "modules.lock.yaml"


def read_pyproject_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["tool"]["poetry"]["version"]


def read_manifest_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for path in MANIFEST_FILES:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
        versions[str(path.name)] = data.get(".", "")
    return versions


def read_module_constant() -> str:
    pattern = re.compile(r"^CURRENT_VERSION\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
    match = pattern.search(VERSION_MODULE.read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError("Could not find CURRENT_VERSION assignment in version.py")
    return match.group(1)


def read_modules_lock_core_version() -> str:
    if not MODULES_LOCK_YAML.exists():
        return ""
    data = yaml.safe_load(MODULES_LOCK_YAML.read_text(encoding="utf-8") or "{}")
    if not isinstance(data, dict):
        return ""
    return str(data.get("core_version") or "")


def main() -> int:
    pyproject_version = read_pyproject_version()
    manifest_versions = read_manifest_versions()
    module_version = read_module_constant()
    modules_lock_core_version = read_modules_lock_core_version()

    mismatches: list[str] = []

    for manifest_name, manifest_version in manifest_versions.items():
        if pyproject_version != manifest_version:
            mismatches.append(
                f"{manifest_name} uses {manifest_version}, expected {pyproject_version}"
            )

    if pyproject_version != module_version:
        mismatches.append(
            f"core/config/version.py CURRENT_VERSION is {module_version}, expected {pyproject_version}"
        )

    if modules_lock_core_version and pyproject_version != modules_lock_core_version:
        mismatches.append(
            f".rapidkit/modules.lock.yaml core_version is {modules_lock_core_version}, expected {pyproject_version}"
        )

    if mismatches:
        for issue in mismatches:
            print(f"❌ {issue}")
        print(
            "💡 Run `poetry run python scripts/update_release_artifacts.py --stage` to sync "
            "pyproject.toml, release-please manifest(s), core/config/version.py, and .rapidkit/modules.lock.yaml."
        )
        return 1

    print(f"✅ Version metadata aligned at {pyproject_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
