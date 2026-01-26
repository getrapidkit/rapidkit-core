from __future__ import annotations

from typing import Any, Dict, List

import click
from pytest import MonkeyPatch

from cli.utils.prompts import prompt_variables
from core.config.kit_config import KitConfig, Variable, VariableType


def _config_with_variables(variables: List[Variable]) -> KitConfig:
    return KitConfig(
        name="demo",
        display_name="Demo",
        description="Demo kit",
        version="1.0.0",
        min_rapidkit_version="1.0.0",
        category="demo",
        tags=[],
        dependencies={},
        modules=[],
        variables=variables,
        structure=[],
        hooks={},
    )


def _silence_click(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(click, "echo", lambda *_args, **_kwargs: None)


def test_prompt_variables_skips_optional_and_existing_non_interactive(
    monkeypatch: MonkeyPatch,
) -> None:
    _silence_click(monkeypatch)
    captured_prompts: List[str] = []

    def _fail_prompt(*_args: Any, **_kwargs: Any) -> None:
        captured_prompts.append("called")
        raise AssertionError("click.prompt should not be called in this scenario")

    monkeypatch.setattr(click, "prompt", _fail_prompt)
    monkeypatch.setattr(click, "confirm", _fail_prompt)

    variables = [
        Variable(name="project_name", type=VariableType.STRING, required=True),
        Variable(name="service_name", type=VariableType.STRING, required=True),
        Variable(name="log_level", type=VariableType.STRING, required=False, default="info"),
    ]

    kit_config = _config_with_variables(variables)
    existing = {"service_name": "api-service", "extra": "value"}

    result = prompt_variables(kit_config, existing, interactive=False)

    assert result == existing
    assert not captured_prompts


def test_prompt_variables_boolean_required(monkeypatch: MonkeyPatch) -> None:
    _silence_click(monkeypatch)
    confirmations: Dict[str, Any] = {}

    def _fake_confirm(text: str, default: bool | None = None) -> bool:
        confirmations[text] = default
        return True

    monkeypatch.setattr(click, "confirm", _fake_confirm)
    monkeypatch.setattr(click, "prompt", lambda *_args, **_kwargs: None)

    variables = [
        Variable(name="enable_cache", type=VariableType.BOOLEAN, required=True, default=False),
    ]

    kit_config = _config_with_variables(variables)
    result = prompt_variables(kit_config, existing_vars={}, interactive=False)

    assert result["enable_cache"] is True
    assert confirmations == {"enable_cache": False}


def test_prompt_variables_choice_interactive(monkeypatch: MonkeyPatch) -> None:
    _silence_click(monkeypatch)
    prompt_calls: Dict[str, Dict[str, Any]] = {}

    def _fake_prompt(text: str, **kwargs: Any) -> str:
        prompt_calls[text] = kwargs
        return "asyncio"

    monkeypatch.setattr(click, "prompt", _fake_prompt)
    monkeypatch.setattr(click, "confirm", lambda *_args, **_kwargs: None)

    variables = [
        Variable(
            name="worker",
            type=VariableType.CHOICE,
            required=False,
            default="uvicorn",
            choices=["uvicorn", "asyncio"],
            description="Select async worker",
        ),
    ]

    kit_config = _config_with_variables(variables)
    result = prompt_variables(kit_config, existing_vars={}, interactive=True)

    assert result["worker"] == "asyncio"
    kwargs = prompt_calls["worker (Select async worker)"]
    assert isinstance(kwargs["type"], click.Choice)
    assert kwargs["type"].choices == ("uvicorn", "asyncio")
    assert kwargs["default"] == "uvicorn"
    assert kwargs["show_default"] is True
