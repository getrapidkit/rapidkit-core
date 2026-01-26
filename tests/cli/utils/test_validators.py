from __future__ import annotations

from pathlib import Path

import pytest

from cli.utils.validators import validate_output_path, validate_project_name
from core.exceptions import ValidationError


@pytest.mark.parametrize("name", ["myapp", "MyApp_123", "app-1"])
def test_validate_project_name_accepts_valid_inputs(name: str) -> None:
    validate_project_name(name)


@pytest.mark.parametrize(
    "name",
    ["", "1bad", "bad space", "a", "b" * 51],
)
def test_validate_project_name_rejects_invalid_inputs(name: str) -> None:
    with pytest.raises(ValidationError):
        validate_project_name(name)


def test_validate_output_path_success(tmp_path: Path) -> None:
    target = tmp_path / "project" / "main.py"
    target.parent.mkdir(parents=True)
    resolved = validate_output_path(str(target))
    assert resolved == target.resolve()


def test_validate_output_path_missing_parent(tmp_path: Path) -> None:
    missing_parent = tmp_path / "missing" / "file.py"
    with pytest.raises(ValidationError) as exc:
        validate_output_path(str(missing_parent))
    assert "Parent directory does not exist" in str(exc.value)


def test_validate_output_path_parent_not_directory(tmp_path: Path) -> None:
    marker = tmp_path / "marker.txt"
    marker.write_text("data", encoding="utf-8")
    bad_target = marker / "file.py"
    with pytest.raises(ValidationError) as exc:
        validate_output_path(str(bad_target))
    assert "Parent path is not a directory" in str(exc.value)
