from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from kits.fastapi.standard import hooks


@pytest.fixture()
def fresh_variables() -> dict[str, Any]:
    return {
        "project_name": "demo",
    }


def test_pre_generate_injects_defaults(
    fresh_variables: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(hooks.getpass, "getuser", lambda: "ci-user")

    original_datetime = hooks.datetime
    monkeypatch.setattr(
        hooks,
        "datetime",
        type("_FrozenDT", (), {"now": staticmethod(lambda: original_datetime(2025, 5, 17))}),
    )

    hooks.pre_generate(fresh_variables)

    assert fresh_variables["author"] == "ci-user"
    assert fresh_variables["app_version"] == "0.1.0"
    assert fresh_variables["description"].startswith("FastAPI service")
    assert fresh_variables["year"] == "2025"


def test_pre_generate_preserves_existing_values(fresh_variables: dict[str, Any]) -> None:
    fresh_variables.update(
        author="existing",
        app_version="9.9.9",
        description="custom",
        year="2042",
    )

    hooks.pre_generate(fresh_variables)

    assert fresh_variables["author"] == "existing"
    assert fresh_variables["app_version"] == "9.9.9"
    assert fresh_variables["description"] == "custom"
    assert fresh_variables["year"] == "2042"


def test_post_generate_prints_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "generated"
    target.mkdir()

    hooks.post_generate(target, {"project_name": "demo-app"})

    captured = capsys.readouterr().out
    assert "FastAPI Standard project scaffolded" in captured
    assert "demo-app" in captured
    assert str(target) in captured


def test_post_generate_returns_quickly_without_output_path() -> None:
    hooks.post_generate(None, {"project_name": "useless"})
    hooks.post_generate(None, None)


@pytest.mark.parametrize("variables", [None, {}, {"project_name": "custom"}])
def test_post_generate_falls_back_to_default_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], variables: dict[str, Any] | None
) -> None:
    target = tmp_path / "another"
    target.mkdir()

    hooks.post_generate(target, variables)

    captured = capsys.readouterr().out
    expected = (variables or {}).get("project_name", "fastapi-service")
    assert expected in captured
