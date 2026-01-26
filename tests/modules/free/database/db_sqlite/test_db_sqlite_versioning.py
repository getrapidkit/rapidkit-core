"""Version metadata expectations for Db Sqlite."""

from __future__ import annotations

import re

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def test_version_is_semantic(module_config: dict[str, object]) -> None:
    version = module_config.get("version", "")
    assert SEMVER_PATTERN.match(
        str(version)
    ), f"Module version '{version}' must follow semantic versioning"
