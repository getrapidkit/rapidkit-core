import sys
import types

import pytest

from cli.ui import printer


@pytest.fixture(name="captured_console")
def _captured_console(monkeypatch):
    class DummyConsole:
        def __init__(self):
            self.prints: list[tuple[str, str | None]] = []
            self.file = types.SimpleNamespace(encoding="utf-8")

        def print(self, message: str, style: str | None = None) -> None:
            self.prints.append((message, style))

    dummy = DummyConsole()
    monkeypatch.setattr(printer, "console", dummy)
    return dummy


@pytest.mark.parametrize(
    "candidates, message, expected",
    [
        (("cp1252",), "🚀 Launch", "Launch"),
        (("ascii", "utf-8"), "⚠️ Danger", "WARN Danger"),
    ],
)
def test_sanitize_console_text_handles_incompatible_encodings(
    monkeypatch, candidates, message, expected
):
    monkeypatch.setattr(printer, "_encoding_candidates", lambda: candidates)

    sanitized = printer.sanitize_console_text(message)

    assert sanitized == expected


def test_encoding_candidates_handles_locale_failure(monkeypatch):
    dummy_console = types.SimpleNamespace(file=types.SimpleNamespace(encoding=None))
    monkeypatch.setattr(printer, "console", dummy_console)
    monkeypatch.setattr(printer.sys, "stdout", types.SimpleNamespace(encoding=None))
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)

    def fail(_flag: bool) -> str:
        raise RuntimeError("locale boom")

    monkeypatch.setattr(printer.locale, "getpreferredencoding", fail)

    assert printer._encoding_candidates() == ()


def test_stream_encoding_defaults_without_candidates(monkeypatch):
    monkeypatch.setattr(printer, "_encoding_candidates", lambda: ())

    assert printer._stream_encoding() == "utf-8"


def test_print_helpers_emit_expected_styles(monkeypatch, captured_console):
    captured_console.file.encoding = "utf-8"
    monkeypatch.setattr(printer, "_encoding_candidates", lambda: ("utf-8",))

    printer.print_success("Completed")
    printer.print_warning("Check this")
    printer.print_error("Failure")
    printer.print_info("FYI")

    assert captured_console.prints == [
        ("✔ Completed", "green"),
        ("⚠ Check this", "yellow"),
        ("❌ Failure", "bold red"),
        ("FYI", "cyan"),
    ]


def test_print_warning_preserves_existing_prefix(monkeypatch, captured_console):
    monkeypatch.setattr(printer, "_encoding_candidates", lambda: ("utf-8",))

    printer.print_warning("WARN: already handled")

    assert captured_console.prints[-1] == ("WARN: already handled", "yellow")


def test_print_warning_uses_fallback_prefix(monkeypatch, captured_console):
    captured_console.file.encoding = "ascii"
    monkeypatch.setattr(printer, "_encoding_candidates", lambda: ("ascii",))

    printer.print_warning("needs attention")

    assert captured_console.prints[-1] == ("WARN: needs attention", "yellow")


def test_print_banner_skips_in_ci_mode(monkeypatch, captured_console):
    monkeypatch.setattr(sys, "argv", ["rapidkit", "--ci"])

    printer.print_banner()

    assert not captured_console.prints


def test_print_banner_fallback_when_logo_missing(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["rapidkit"])
    monkeypatch.setattr(printer, "_encoding_candidates", lambda: ("utf-8",))

    def path_missing(_path: printer.Path) -> bool:
        return False

    monkeypatch.setattr(printer.Path, "exists", path_missing)

    captured: list[tuple[str, str]] = []

    def fake_print(color: str, message: str) -> None:
        captured.append((color, message))

    monkeypatch.setattr(printer, "_print", fake_print)

    printer.print_banner()

    assert captured == [("bold magenta", "🚀 RapidKit")]


def test_print_banner_outputs_logo(monkeypatch, captured_console):
    monkeypatch.setattr(sys, "argv", ["rapidkit"])

    def path_exists(_path: printer.Path) -> bool:
        return True

    def path_read_text(_path: printer.Path) -> str:
        return "LOGO\n"

    monkeypatch.setattr(printer.Path, "exists", path_exists)
    monkeypatch.setattr(printer.Path, "read_text", path_read_text)

    printer.print_banner()

    assert captured_console.prints == [("[bold cyan]LOGO\n[/bold cyan]", None)]


def test_ensure_prefix_falls_back_to_original_message(monkeypatch):
    monkeypatch.setattr(printer, "_can_encode", lambda _symbol: False)
    monkeypatch.setattr(printer, "_fallback_prefix", lambda _symbol: "")

    assert printer._ensure_prefix("status", "🚀") == "status"


def test_ensure_prefix_returns_symbol_when_message_empty(monkeypatch):
    monkeypatch.setattr(printer, "_can_encode", lambda _symbol: True)

    assert printer._ensure_prefix("", "❌") == "❌"
