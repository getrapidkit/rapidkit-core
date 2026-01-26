from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from core.services import module_versioning as mv


def test_merge_changelog_metadata_combines_sources() -> None:
    pending = {
        "changes": ["doc update"],
        "breaking_changes": ["api"],
        "description": "pending description",
    }
    inline = {
        "changes": [{"type": "feat", "description": "new feature", "tickets": ["JIRA-1"]}],
        "deprecations": {"items": ["old-api"]},
        "description": "inline overrides",
        "metadata": {"owner": "team"},
    }

    merged = mv._merge_changelog_metadata(pending, inline)

    assert merged["changes"][0] == "doc update"
    assert merged["changes"][1]["type"] == "feat"
    assert merged["changes"][1]["tickets"] == ["JIRA-1"]
    assert merged["breaking_changes"] == ["api"]
    assert merged["deprecations"] == [{"items": ["old-api"]}]
    assert merged["metadata"] == {"owner": "team"}


def test_resolve_change_description_prefers_metadata() -> None:
    metadata = {"description": "  important release  "}

    description = mv._resolve_change_description(metadata, "fallback")

    assert description == "important release"
    assert "description" not in metadata


def test_normalize_changes_handles_multiple_input_shapes() -> None:
    result = mv._normalize_changes(
        "default",
        [
            "textual entry",
            {"type": "fix", "description": "bug fix", "ticket": "BUG-1"},
            {"details": "missing type"},
        ],
    )

    assert result[0]["description"] == "textual entry"
    assert result[1]["type"] == "fix"
    assert result[1]["ticket"] == "BUG-1"
    assert result[2]["type"] == "chore"
    assert result[2]["description"] == "default"


def test_normalize_changes_falls_back_to_default_description() -> None:
    assert mv._normalize_changes("fallback", []) == [{"type": "chore", "description": "fallback"}]


def test_normalize_string_sequence_and_to_list_helpers() -> None:
    sequence_result = mv._normalize_string_sequence({"one", None, 2})
    assert set(sequence_result) == {"one", "2"}
    assert mv._to_list((1, 2)) == [1, 2]
    assert set(mv._to_list({3})) == {3}
    assert mv._to_list("solo") == ["solo"]


def test_prepare_changelog_entry_incorporates_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    class FixedDate(date):
        @classmethod
        def today(cls) -> date:
            return cls(2024, 1, 2)

    monkeypatch.setattr(mv, "date", FixedDate)

    entry = mv._prepare_changelog_entry(
        "1.2.3",
        "summary",
        {
            "changes": ["Alpha"],
            "breaking_changes": ["Removal"],
            "deprecations": ["Legacy"],
            "extra": {"approved": True},
        },
    )

    assert entry["version"] == "1.2.3"
    assert entry["date"] == "2024-01-02"
    assert entry["changes"][0]["description"] == "Alpha"
    assert entry["breaking_changes"] == ["Removal"]
    assert entry["deprecations"] == ["Legacy"]
    assert entry["extra"] == {"approved": True}


def test_build_changelog_entry_renders_expected_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    class FixedDate(date):
        @classmethod
        def today(cls) -> date:
            return cls(2023, 3, 4)

    monkeypatch.setattr(mv, "date", FixedDate)

    changelog = mv._build_changelog_entry(
        "2.0.0",
        "Automated bump",
        {
            "changes": [
                {"type": "feat", "description": "New thing"},
                {"description": "Implicit chore", "custom": {"flag": True}},
            ],
            "breaking_changes": ["Breaking"],
            "metadata": {"owner": "team"},
        },
    )

    assert 'version: "2.0.0"' in changelog
    assert "New thing" in changelog
    assert "flag" in changelog
    assert "Breaking" in changelog


def test_render_helpers_handle_nested_structures() -> None:
    rendered = mv._render_key_value(
        "root",
        {
            "child": [
                {"grandchild": True},
                "scalar",
            ]
        },
        indent=2,
    )

    assert "root:" in rendered[0]
    assert any("grandchild" in line for line in rendered)
    assert any('- "scalar"' in line for line in rendered)


def test_format_scalar_handles_types() -> None:
    assert mv._format_scalar(True) == "true"
    assert mv._format_scalar(False) == "false"
    assert mv._format_scalar(None) == "null"
    assert mv._format_scalar(3.14) == "3.14"
    assert mv._format_scalar('quoted"value') == '"quoted\\"value"'


def test_load_pending_changelog_supports_various_payloads(tmp_path: Path) -> None:
    mapping_file = tmp_path / "pending.yaml"
    mapping_file.write_text("description: Ready\nchanges:\n  - desc\n", encoding="utf-8")
    list_file = tmp_path / "pending_list.yaml"
    list_file.write_text("- first\n- second\n", encoding="utf-8")
    text_file = tmp_path / "pending_text.yaml"
    text_file.write_text("Just text", encoding="utf-8")

    mapping_result = mv._load_pending_changelog(tmp_path, "pending.yaml")
    list_result = mv._load_pending_changelog(tmp_path, "pending_list.yaml")
    text_result = mv._load_pending_changelog(tmp_path, "pending_text.yaml")

    assert mapping_result == {"description": "Ready", "changes": ["desc"]}
    assert list_result == {"changes": ["first", "second"]}
    assert text_result == {"description": "Just text"}


def test_load_pending_changelog_handles_missing_or_invalid(tmp_path: Path) -> None:
    assert mv._load_pending_changelog(tmp_path, "not_there.yaml") is None

    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("list: [1, 2", encoding="utf-8")

    assert mv._load_pending_changelog(tmp_path, "bad.yaml") is None
