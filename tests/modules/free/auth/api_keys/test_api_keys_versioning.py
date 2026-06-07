"""Versioning tests for Api Keys."""

from __future__ import annotations

import json

import yaml


def test_api_keys_version_state_and_changelog_are_aligned(module_root) -> None:  # type: ignore[no-untyped-def]
    module_yaml = yaml.safe_load((module_root / "module.yaml").read_text(encoding="utf-8"))
    module_state = json.loads((module_root / ".module_state.json").read_text(encoding="utf-8"))
    changelog = (module_root / "docs/changelog.md").read_text(encoding="utf-8")

    assert str(module_yaml["version"]) == module_state["version"]
    assert module_state["hash"]
    assert f"## {module_state['version']}" in changelog
