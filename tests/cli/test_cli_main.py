from __future__ import annotations

import sys

import pytest
import typer
from _pytest.capture import CaptureFixture
from pytest import MonkeyPatch

from cli import main as cli_main
from core.config.version import get_version


def test_main_prints_banner(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["rapidkit"])

    calls: list[str] = []
    monkeypatch.setattr("cli.main.print_banner", lambda: calls.append("banner"))

    class _FakeApp:
        def __call__(self) -> None:
            calls.append("app")

    monkeypatch.setattr(cli_main, "app", _FakeApp())

    cli_main.main()

    assert calls == ["banner", "app"]


def test_main_skips_banner_in_ci(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["rapidkit", "--ci"])

    calls: list[str] = []
    monkeypatch.setattr("cli.main.print_banner", lambda: calls.append("banner"))

    class _FakeApp:
        def __call__(self) -> None:
            calls.append("app")

    monkeypatch.setattr(cli_main, "app", _FakeApp())

    cli_main.main()

    assert calls == ["app"]


def test_main_handles_unexpected_exception(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["rapidkit"])
    monkeypatch.setattr("cli.main.print_banner", lambda: None)

    class _BoomApp:
        def __call__(self) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(cli_main, "app", _BoomApp())

    with pytest.raises(typer.Exit) as exc:
        cli_main.main()

    assert exc.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Unexpected error" in captured.out


def test_cli_version_option_exits_cleanly(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["rapidkit", "--version"])
    monkeypatch.setattr("cli.main.print_banner", lambda: None)

    cli_main.main()
    captured = capsys.readouterr()
    assert captured.out.strip() == f"RapidKit Version v{get_version()}"
    assert captured.err == ""


def test_cli_short_version_option_exits_cleanly(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["rapidkit", "-v"])
    monkeypatch.setattr("cli.main.print_banner", lambda: None)

    cli_main.main()
    captured = capsys.readouterr()
    assert captured.out.strip() == f"RapidKit Version v{get_version()}"
    assert captured.err == ""
