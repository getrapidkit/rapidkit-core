from __future__ import annotations

# ruff: noqa: I001

import sys
import types
from typing import Any

import pytest

from modules.free.essentials.settings import overrides as overrides_module


EXPECTED_EXTRA_DOTENV_SOURCES = 2


@pytest.fixture(autouse=True)
def clear_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAPIDKIT_SETTINGS_EXTRA_DOTENV", raising=False)
    monkeypatch.delenv("RAPIDKIT_SETTINGS_RELAXED_ENVS", raising=False)
    monkeypatch.delenv("RAPIDKIT_SETTINGS_ALLOW_PLACEHOLDER_SECRET", raising=False)
    monkeypatch.delenv("RAPIDKIT_SETTINGS_LOG_REFRESH", raising=False)


def test_append_extra_dotenv_sources_appends_configured_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[tuple[str, bool]] = []

    class DummyDotEnvSource:
        def __init__(self, settings_cls: type[Any], env_file: str, case_sensitive: bool) -> None:
            created.append((env_file, case_sensitive))
            self.settings_cls = settings_cls
            self.env_file = env_file
            self.case_sensitive = case_sensitive

    monkeypatch.setitem(
        sys.modules,
        "pydantic_settings",
        types.SimpleNamespace(DotEnvSettingsSource=DummyDotEnvSource),
    )
    monkeypatch.setenv("RAPIDKIT_SETTINGS_EXTRA_DOTENV", "first.env, second.env")

    append_extra = getattr(overrides_module, "_append_extra_dotenv_sources")  # noqa: B009
    result = append_extra(type("SettingsHook", (), {}), object, "init", "env", "dotenv", "secrets")

    assert result[:4] == ("init", "env", "dotenv", "secrets")
    assert len(created) == EXPECTED_EXTRA_DOTENV_SOURCES
    assert [env for env, _ in created] == ["first.env", "second.env"]
    assert all(flag is True for _, flag in created)


def test_append_extra_dotenv_sources_handles_missing_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RAPIDKIT_SETTINGS_EXTRA_DOTENV", "data.env")

    def _raise_import_error(name: str) -> None:
        raise ImportError(name)

    monkeypatch.setattr(overrides_module.importlib, "import_module", _raise_import_error)

    append_extra = getattr(overrides_module, "_append_extra_dotenv_sources")  # noqa: B009
    result = append_extra(type("SettingsHook", (), {}), object, "init", "env", "dotenv", "secrets")

    assert result == ("init", "env", "dotenv", "secrets")


def test_relaxed_production_validation_allows_placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_SETTINGS_RELAXED_ENVS", "prod")
    monkeypatch.setenv("RAPIDKIT_SETTINGS_ALLOW_PLACEHOLDER_SECRET", "true")

    class Settings:
        SECRET_PLACEHOLDER = "placeholder"

        def __init__(self) -> None:
            self.ENV = "prod"
            self.SECRET_KEY = "placeholder"

    calls: list[str] = []

    def original(_self: Settings) -> None:
        calls.append("called")

    setattr(Settings, "_original_validate_production_settings", original)  # type: ignore[attr-defined]  # noqa: B010

    relaxed = getattr(overrides_module, "_relaxed_production_validation")  # noqa: B009
    instance = Settings()
    result = relaxed(instance)

    assert result is instance
    assert calls == ["called"]


def test_relaxed_production_validation_noop_when_env_not_permitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RAPIDKIT_SETTINGS_RELAXED_ENVS", "prod")
    monkeypatch.setenv("RAPIDKIT_SETTINGS_ALLOW_PLACEHOLDER_SECRET", "true")

    class Settings:
        SECRET_PLACEHOLDER = "placeholder"

        def __init__(self) -> None:
            self.ENV = "staging"
            self.SECRET_KEY = "placeholder"

    relaxed = getattr(overrides_module, "_relaxed_production_validation")  # noqa: B009
    result = relaxed(Settings())

    assert result.SECRET_KEY == "placeholder"


def test_refresh_with_observability_logs_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_SETTINGS_LOG_REFRESH", "true")

    original_calls: list[str] = []
    log_calls: list[tuple[str, dict[str, Any]]] = []

    class DummyLogger:
        def info(self, message: str, *, extra: dict[str, Any] | None = None) -> None:
            log_calls.append((message, extra or {}))

    monkeypatch.setattr(overrides_module, "logger", DummyLogger())

    class Settings:
        def __init__(self) -> None:
            self.ENV = "prod"
            self.HOT_RELOAD_ENABLED = True

    def original(_self: Settings) -> None:
        original_calls.append("called")

    setattr(Settings, "_original_refresh", original)  # type: ignore[attr-defined]  # noqa: B010

    refresh = getattr(overrides_module, "_refresh_with_observability")  # noqa: B009
    refresh(Settings())

    assert original_calls == ["called"]
    assert log_calls == [
        ("Settings refresh executed", {"env": "prod", "hot_reload": True}),
    ]


def test_refresh_with_observability_skips_logging_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DummyLogger:
        def info(self, message: str, *, extra: dict[str, Any] | None = None) -> None:
            raise AssertionError(f"Unexpected log: {message!r} {extra!r}")

    monkeypatch.setattr(overrides_module, "logger", DummyLogger())

    original_calls: list[str] = []

    class Settings:
        def __init__(self) -> None:
            self.ENV = "prod"
            self.HOT_RELOAD_ENABLED = False

    def original(_self: Settings) -> None:
        original_calls.append("called")

    setattr(Settings, "_original_refresh", original)  # type: ignore[attr-defined]  # noqa: B010

    refresh = getattr(overrides_module, "_refresh_with_observability")  # noqa: B009
    refresh(Settings())

    assert original_calls == ["called"]
