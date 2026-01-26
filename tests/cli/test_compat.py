from __future__ import annotations

import importlib
import os
import sys
import types
from typing import Any, cast


def test_compat_disables_rich_and_sanitizes_echo() -> None:
    captured_messages: list[str] = []

    def record_echo(*args: Any, **kwargs: Any) -> Any:
        message = kwargs.get("message")
        if message is None and args:
            message = args[0]
        message_str = str(message) if message is not None else ""
        captured_messages.append(message_str)
        return message_str

    original_no_color = os.environ.get("NO_COLOR")
    original_term = os.environ.get("TERM")

    stub_typer = types.ModuleType("typer")
    stub_typer_any = cast(Any, stub_typer)
    stub_typer_any.core = types.SimpleNamespace()
    stub_typer_any.rich = object()
    stub_typer_any.core.rich = object()

    stub_click = types.ModuleType("click")
    stub_click_any = cast(Any, stub_click)
    stub_click_any.utils = types.SimpleNamespace(echo=record_echo)
    stub_click_any.echo = record_echo
    stub_click_any.decorators = types.SimpleNamespace(echo=record_echo)
    stub_click_any.termui = types.SimpleNamespace(echo=record_echo)

    stub_printer = types.ModuleType("cli.ui.printer")
    stub_printer_any = cast(Any, stub_printer)
    stub_printer_any.sanitize_console_text = lambda text: str(text).upper()

    original_modules = {
        "cli._compat": sys.modules.get("cli._compat"),
        "click": sys.modules.get("click"),
        "typer": sys.modules.get("typer"),
        "cli.ui.printer": sys.modules.get("cli.ui.printer"),
    }

    try:
        os.environ.pop("NO_COLOR", None)
        os.environ.pop("TERM", None)

        sys.modules.pop("cli._compat", None)
        sys.modules["click"] = stub_click
        sys.modules["typer"] = stub_typer
        sys.modules["cli.ui.printer"] = stub_printer

        compat_module = importlib.import_module("cli._compat")

        assert getattr(stub_typer_any, "rich", None) is None
        assert getattr(stub_typer_any.core, "rich", None) is None
        assert os.environ["NO_COLOR"] == "1"
        assert os.environ["TERM"] == "dumb"

        stub_click_any.echo("hello")
        stub_click_any.decorators.echo("decor")
        stub_click_any.termui.echo("term")

        assert captured_messages == ["HELLO", "DECOR", "TERM"]
        assert set(compat_module.__all__) == {"Any", "Optional", "cast"}
    finally:
        if original_no_color is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = original_no_color

        if original_term is None:
            os.environ.pop("TERM", None)
        else:
            os.environ["TERM"] = original_term

        sys.modules.pop("cli._compat", None)
        for name, module in original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
