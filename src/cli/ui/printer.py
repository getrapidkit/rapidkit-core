# src / cli / ui / printer.py
import locale
import os
import sys
from pathlib import Path
from typing import Any, Tuple, cast

import typer
from rich.console import Console

_CONSOLE_STATE: dict[str, object] = {"instance": None, "stream": None}


def _get_console() -> Console:
    stream = sys.stdout
    console = _CONSOLE_STATE["instance"]
    target_stream = _CONSOLE_STATE["stream"]

    if not isinstance(console, Console) or stream is not target_stream:
        console = Console(file=stream)
        _CONSOLE_STATE["instance"] = console
        _CONSOLE_STATE["stream"] = stream

    return console


class _ConsoleProxy:
    def __getattr__(self, item: str) -> Any:
        return getattr(_get_console(), item)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return repr(_get_console())


console: Console = cast(Console, _ConsoleProxy())


def _encoding_candidates() -> Tuple[str, ...]:
    candidates: list[str] = []
    seen: set[str] = set()

    def _add(value: object) -> None:
        if isinstance(value, str) and value and value not in seen:
            candidates.append(value)
            seen.add(value)

    _add(os.environ.get("PYTHONIOENCODING"))
    console_obj = console
    console_file = getattr(console_obj, "file", None)
    _add(getattr(console_file, "encoding", None))
    _add(getattr(sys.stdout, "encoding", None))

    try:
        preferred = locale.getpreferredencoding(False)
    except Exception:  # noqa: BLE001
        preferred = None
    _add(preferred)

    return tuple(candidates)


def _stream_encoding() -> str:
    candidates = _encoding_candidates()
    if candidates:
        return candidates[0]
    return "utf-8"


def _can_encode(sample: str) -> bool:
    candidates = _encoding_candidates() or ("utf-8",)
    for encoding in candidates:
        try:
            sample.encode(encoding)
        except (UnicodeEncodeError, LookupError):
            return False
    return True


_SYMBOL_REPLACEMENTS: Tuple[Tuple[str, str], ...] = (
    ("🚀", ""),
    ("❌", "ERROR"),
    ("✔", "OK"),
    ("⚠️", "WARN"),
    ("⚠", "WARN"),
    ("✅", "OK"),
    ("⏩", "SKIP"),
    ("📦", "PACKAGE"),
    ("📁", "DIR"),
    ("📂", "DIR"),
    ("📊", "STATS"),
    ("✨", ""),
    ("🛠", "TOOLS"),
    ("😕", "No kits found"),
)


def _apply_symbol_replacements(text: str) -> str:
    sanitized = text
    for symbol, replacement in _SYMBOL_REPLACEMENTS:
        sanitized = sanitized.replace(f"{symbol} ", f"{replacement} " if replacement else "")
        sanitized = sanitized.replace(symbol, replacement)
    return sanitized


def sanitize_console_text(text: str) -> str:
    candidates = _encoding_candidates()
    if candidates and candidates[0].lower() not in {"utf-8", "utf8"}:
        sanitized = _apply_symbol_replacements(text)
        return sanitized.encode("ascii", errors="replace").decode("ascii")

    check_encodings = candidates or ("utf-8",)
    for encoding in check_encodings:
        try:
            text.encode(encoding)
        except (UnicodeEncodeError, LookupError):
            sanitized = _apply_symbol_replacements(text)
            primary = check_encodings[0]
            sanitized_bytes = sanitized.encode(primary, errors="replace")
            return sanitized_bytes.decode(primary, errors="replace")
    return text


_PREFIX_FALLBACKS = {
    "🚀": "",
    "❌": "ERROR:",
    "✔": "OK",
    "⚠": "WARN:",
    "✅": "OK",
    "⏩": "SKIP:",
}

_PREFIX_MARKERS: Tuple[str, ...] = (
    "🚀",
    "❌",
    "✔",
    "⚠",
    "✅",
    "⏩",
    "ERROR:",
    "ERROR",
    "WARN:",
    "WARN",
    "OK",
    "SKIP:",
    "SKIP",
    "PACKAGE",
    "DIR",
    "STATS",
    "TOOLS",
    "No kits found",
    "No kits found.",
)


def _fallback_prefix(symbol: str) -> str:
    return _PREFIX_FALLBACKS.get(symbol, "").rstrip()


def _ensure_prefix(message: str, symbol: str) -> str:
    stripped = message.lstrip()
    if stripped.startswith(_PREFIX_MARKERS):
        return message

    prefix = symbol
    if not _can_encode(symbol):
        prefix = _fallback_prefix(symbol)

    if not prefix:
        return message

    return f"{prefix} {message}" if message else prefix


def _print(color: str, message: str) -> None:
    target = console
    sanitized = sanitize_console_text(message)
    stream = getattr(target, "file", sys.stdout)
    is_tty = bool(getattr(stream, "isatty", lambda: False)())
    target.print(sanitized, style=color)
    if not is_tty:
        typer.echo(sanitized)


def print_banner() -> None:
    # Check if we're in CI mode or JSON mode
    if "--ci" in sys.argv or "--json" in sys.argv:
        return  # Skip banner in CI/JSON modes

    banner_path = Path(__file__).parent.parent.parent.parent / "assets" / "logo.txt"
    if banner_path.exists():
        # Ensure we read the artwork reliably across locales/encodings
        # Some test harnesses monkeypatch Path.read_text without an encoding
        # parameter — prefer explicit utf-8, but fall back to the default
        # signature when necessary so unit tests remain compatible.
        try:
            banner = banner_path.read_text(encoding="utf-8")
        except TypeError:
            banner = banner_path.read_text()
        console.print(f"[bold cyan]{banner}[/bold cyan]")
    else:
        _print("bold magenta", _ensure_prefix("RapidKit", "🚀"))


def print_success(message: str) -> None:
    _print("green", _ensure_prefix(message, "✔"))


def print_warning(message: str) -> None:
    _print("yellow", _ensure_prefix(message, "⚠"))


def print_error(message: str) -> None:
    _print("bold red", _ensure_prefix(message, "❌"))


def print_info(message: str) -> None:
    _print("cyan", message)
