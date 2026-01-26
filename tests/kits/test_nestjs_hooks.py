"""Tests for NestJS standard kit hooks."""

from datetime import datetime as _real_datetime
from pathlib import Path

import pytest

from kits.nestjs.standard import hooks


class _FixedDateTime(_real_datetime):
    """Deterministic datetime replacement for tests."""

    @classmethod
    def now(cls) -> "_FixedDateTime":  # type: ignore[override]
        return cls(2025, 1, 2)


def test_pre_generate_sets_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hooks.getpass, "getuser", lambda: "ci-user")
    monkeypatch.setattr(hooks, "datetime", _FixedDateTime)

    variables = {
        "project_name": "rocket-app",
        "package_manager": "yarn",
    }

    hooks.pre_generate(variables)

    assert variables["author"] == "ci-user"
    assert variables["year"] == "2025"


@pytest.mark.parametrize(
    "variables",
    [
        {"project_name": "bad name!", "package_manager": "npm"},
        {"project_name": "rocket-app", "package_manager": "poetry"},
        {
            "project_name": "rocket-app",
            "package_manager": "npm",
            "database_type": "sqlite",
            "auth_type": "oauth2",
        },
    ],
)
def test_pre_generate_validation_errors(variables: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        hooks.pre_generate(dict(variables))


def test_post_generate_outputs_next_steps(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    variables = {
        "project_name": "galaxy",
        "package_manager": "pnpm",
        "auth_type": "jwt",
        "database_type": "mysql",
        "docker_support": True,
        "include_monitoring": True,
        "include_caching": True,
        "include_logging": True,
        "include_testing": True,
        "include_docs": True,
    }

    hooks.post_generate(output_path=tmp_path, variables=variables)

    captured = capsys.readouterr().out
    assert "galaxy" in captured
    assert "pnpm install" in captured
    assert "docker-compose up -d" in captured
    assert "✨ Features enabled" in captured
    assert str(tmp_path) in captured


def test_post_generate_handles_unknown_package_manager(
    capsys: pytest.CaptureFixture[str],
) -> None:
    variables = {
        "project_name": "nebula",
        "package_manager": "bun",
        "docker_support": False,
    }

    hooks.post_generate(output_path=None, variables=variables)

    captured = capsys.readouterr().out
    assert "nebula" in captured
    assert "npm install" in captured  # falls back to npm commands
    assert "docker-compose" not in captured
