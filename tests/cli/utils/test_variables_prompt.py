from __future__ import annotations

from typing import Any, Dict

import pytest
import typer
from pytest import MonkeyPatch

from cli.utils.variables_prompt import prompt_for_variables


def _silence_printer(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("cli.utils.variables_prompt.print_error", lambda *_args, **_kwargs: None)


def test_prompt_uses_environment_overrides(monkeypatch: MonkeyPatch) -> None:
    _silence_printer(monkeypatch)
    monkeypatch.setenv("API_KEY", "secret")
    monkeypatch.setenv("RETRIES", "3")
    monkeypatch.setenv("CHANNELS", "alpha,beta")

    config: Dict[str, Dict[str, Any]] = {
        "api_key": {"type": "string", "required": True},
        "retries": {"type": "int", "default": 1},
        "channels": {"type": "list", "default": []},
    }

    variables = prompt_for_variables(config)

    assert variables == {
        "api_key": "secret",
        "retries": 3,
        "channels": ["alpha", "beta"],
    }


def test_prompt_collects_required_values(monkeypatch: MonkeyPatch) -> None:
    _silence_printer(monkeypatch)

    prompt_answers = {
        "🔑 Enter value for required variable 'username' (Main admin user)": "admin",
        "🔑 Enter value for required variable 'timeout' (Request timeout)": "42",
    }

    def _fake_prompt(text: str) -> str:
        return prompt_answers[text]

    confirmations = {"🔑 Enter value for required variable 'enable_cache' (Enable caching)": True}

    def _fake_confirm(text: str) -> bool:
        return confirmations[text]

    monkeypatch.setenv("EXTRA", "ignored")
    monkeypatch.delenv("USERNAME", raising=False)
    monkeypatch.delenv("TIMEOUT", raising=False)
    monkeypatch.delenv("ENABLE_CACHE", raising=False)
    monkeypatch.setattr(typer, "prompt", _fake_prompt)
    monkeypatch.setattr(typer, "confirm", _fake_confirm)

    config: Dict[str, Dict[str, Any]] = {
        "username": {"type": "string", "required": True, "description": "Main admin user"},
        "timeout": {"type": "int", "required": True, "description": "Request timeout"},
        "enable_cache": {"type": "bool", "required": True, "description": "Enable caching"},
    }

    variables = prompt_for_variables(config)

    assert variables == {
        "username": "admin",
        "timeout": 42,
        "enable_cache": True,
    }


def test_prompt_validation_errors_surface(monkeypatch: MonkeyPatch) -> None:
    _silence_printer(monkeypatch)

    def _fake_prompt(_: str) -> str:
        return "@@bad@@"

    monkeypatch.setattr(typer, "prompt", _fake_prompt)

    config: Dict[str, Dict[str, Any]] = {
        "service": {"type": "string", "required": True, "validation": r"^[a-z]+$"}
    }

    with pytest.raises(typer.BadParameter) as exc:
        prompt_for_variables(config)

    assert "does not match pattern" in str(exc.value)


def test_prompt_list_validation(monkeypatch: MonkeyPatch) -> None:
    _silence_printer(monkeypatch)
    monkeypatch.setenv("ENDPOINTS", "ok-1, invalid!,ok-2")

    config: Dict[str, Dict[str, Any]] = {
        "endpoints": {
            "type": "list",
            "required": False,
            "item_validation": r"^[a-z0-9-]+$",
        }
    }

    with pytest.raises(typer.BadParameter) as exc:
        prompt_for_variables(config)

    assert "does not match pattern" in str(exc.value)
