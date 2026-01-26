"""Version metadata expectations for Db Postgres."""

from __future__ import annotations

import re

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def test_version_is_semantic(module_config: dict[str, object]) -> None:
    version = str(module_config.get("version", ""))
    assert SEMVER_PATTERN.match(
        version
    ), f"Module version '{version}' must follow semantic versioning"
