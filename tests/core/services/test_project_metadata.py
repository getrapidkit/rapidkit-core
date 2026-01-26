from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from core.services import project_metadata as pm


class FixedDateTime:
    @staticmethod
    def now(tz: timezone) -> datetime:
        assert tz is timezone.utc
        return datetime(2024, 10, 31, 12, 30, tzinfo=timezone.utc)


@pytest.fixture
def fixed_datetime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pm, "datetime", FixedDateTime)


def test_project_metadata_create_produces_expected_payload(fixed_datetime: None) -> None:
    _ = fixed_datetime
    metadata = pm.ProjectMetadata.create("kit", "profile", "1.2.3")

    assert metadata.kit_name == "kit"
    assert metadata.profile == "profile"
    assert metadata.rapidkit_version == "1.2.3"
    assert metadata.created_at == "2024-10-31T12:30:00+00:00"


def test_save_and_load_project_metadata_roundtrip(tmp_path, fixed_datetime: None) -> None:
    _ = fixed_datetime
    metadata = pm.ProjectMetadata.create("fastapi", "standard", "2.0.0")

    pm.save_project_metadata(tmp_path, metadata)
    loaded = pm.load_project_metadata(tmp_path)

    assert loaded == metadata


def test_load_project_metadata_handles_missing_and_invalid(tmp_path, fixed_datetime: None) -> None:
    _ = fixed_datetime
    assert pm.load_project_metadata(tmp_path) is None

    invalid_path = tmp_path / pm.DEFAULT_METADATA_RELATIVE_PATH
    invalid_path.parent.mkdir(parents=True, exist_ok=True)
    invalid_path.write_text(json.dumps({"kit_name": "kit"}), encoding="utf-8")

    assert pm.load_project_metadata(tmp_path) is None
