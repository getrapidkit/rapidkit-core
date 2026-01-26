from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from modules.shared import versioning


def test_bump_module_version_variants() -> None:
    assert versioning.bump_module_version("1.2.3", "patch") == "1.2.4"
    assert versioning.bump_module_version("1.2.3", "minor") == "1.3.0"
    assert versioning.bump_module_version("1.2.3", "major") == "2.0.0"


@pytest.mark.parametrize("version", ["not-a-version", "1..2.3", ""])
def test_bump_module_version_invalid_version(version: str) -> None:
    with pytest.raises(ValueError):
        versioning.bump_module_version(version)


def test_bump_module_version_invalid_type() -> None:
    with pytest.raises(ValueError):
        versioning.bump_module_version("1.2.3", "build")


@pytest.mark.parametrize(
    "candidate, expected",
    [
        ("1.0.0", True),
        ("0.0.1", True),
        ("1.0", True),
        ("foo", False),
        ("1..0", False),
        ("", False),
    ],
)
def test_validate_version_string(candidate: str, expected: bool) -> None:
    assert versioning.validate_version_string(candidate) is expected


def test_get_module_content_hash_detects_changes(tmp_path: Path) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    (module_root / "module.yaml").write_text("name: demo\nversion: 1.0.0\n", encoding="utf-8")
    (module_root / "README.md").write_text("hello", encoding="utf-8")

    first_hash = versioning.get_module_content_hash(module_root)
    (module_root / "README.md").write_text("hello world", encoding="utf-8")
    second_hash = versioning.get_module_content_hash(module_root)

    assert first_hash != second_hash


def test_ensure_version_consistency_passes_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    (module_root / "module.yaml").write_text(
        json.dumps({"name": "demo", "version": "1.0.0"}), encoding="utf-8"
    )

    received: dict[str, Any] = {}

    def _fake_ensure(
        root: Path,
        config: dict[str, Any],
        *,
        change_description: str,
        state_filename: str,
        excluded_dirs: Any,
        excluded_files: Any,
        changelog_metadata: Any,
        pending_changelog_filename: str | None,
        clear_pending_changelog: bool,
    ) -> tuple[dict[str, Any], bool]:
        received["root"] = root
        received["config"] = config
        received["change_description"] = change_description
        received["state_filename"] = state_filename
        received["excluded_dirs"] = tuple(sorted(excluded_dirs))
        received["excluded_files"] = tuple(sorted(excluded_files))
        received["changelog_metadata"] = changelog_metadata
        received["pending_changelog_filename"] = pending_changelog_filename
        received["clear_pending_changelog"] = clear_pending_changelog
        return config, True

    monkeypatch.setattr(versioning, "_ensure_version_consistency", _fake_ensure)

    config, bumped = versioning.ensure_version_consistency(
        {"name": "demo", "version": "1.0.0"},
        module_root=module_root,
        change_description="manual",
        state_filename="state.json",
        excluded_dirs=[".git"],
        excluded_files=["README.md"],
        changelog_metadata={"changes": ["added"]},
        pending_changelog_filename="pending.yaml",
        clear_pending_changelog=False,
    )

    assert bumped is True
    assert config == {"name": "demo", "version": "1.0.0"}
    assert received["root"] == module_root
    assert received["config"] == {"name": "demo", "version": "1.0.0"}
    assert received["change_description"] == "manual"
    assert received["state_filename"] == "state.json"
    assert received["excluded_dirs"] == (".git",)
    assert received["excluded_files"] == ("README.md",)
    assert received["changelog_metadata"] == {"changes": ["added"]}
    assert received["pending_changelog_filename"] == "pending.yaml"
    assert received["clear_pending_changelog"] is False
