from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from modules.free.essentials.settings import overrides


class _Carrier:
    """Provides baseline sources matching the signature expected by the override."""

    @staticmethod
    def _original_settings_customise_sources(
        *_: Any,
    ) -> tuple[str, str, str, str]:
        return ("init", "env", "dotenv", "secrets")


class _DummySettings:
    pass


def _call_override(monkeypatch: pytest.MonkeyPatch, **env: str) -> tuple[Any, ...]:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return overrides._append_extra_dotenv_sources(  # noqa: SLF001
        _Carrier,
        _DummySettings,
        object(),
        object(),
        object(),
        object(),
    )


def test_append_extra_dotenv_sources_adds_entries(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / "extra.env"
    env_file.write_text("EXTRA=true")

    module = types.ModuleType("pydantic_settings")
    created: dict[str, str] = {}

    class _FakeSource:  # noqa: D401 - tiny test helper
        def __init__(self, settings_cls: Any, env_file: str, case_sensitive: bool) -> None:
            created["cls"] = settings_cls.__name__
            created["env_file"] = env_file
            created["case_sensitive"] = str(case_sensitive)

    module.DotEnvSettingsSource = _FakeSource  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pydantic_settings", module)

    result = _call_override(
        monkeypatch,
        RAPIDKIT_SETTINGS_EXTRA_DOTENV=str(env_file),
    )

    assert any(isinstance(item, _FakeSource) for item in result)
    assert created == {
        "cls": _DummySettings.__name__,
        "env_file": str(env_file),
        "case_sensitive": "True",
    }


def test_append_extra_dotenv_sources_handles_missing_module(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("WARNING")

    def _fail(_: str) -> Any:
        raise ImportError("boom")

    monkeypatch.setattr(overrides.importlib, "import_module", _fail)

    result = _call_override(
        monkeypatch,
        RAPIDKIT_SETTINGS_EXTRA_DOTENV="/tmp/missing.env",
    )

    assert result == ("init", "env", "dotenv", "secrets")
    assert "pydantic_settings is missing" in caplog.text


def test_append_extra_dotenv_sources_handles_missing_attribute(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("WARNING")

    module = types.ModuleType("pydantic_settings")
    monkeypatch.setitem(sys.modules, "pydantic_settings", module)

    result = _call_override(
        monkeypatch,
        RAPIDKIT_SETTINGS_EXTRA_DOTENV="/tmp/missing.env",
    )

    assert result == ("init", "env", "dotenv", "secrets")
    assert "DotEnvSettingsSource is unavailable" in caplog.text
