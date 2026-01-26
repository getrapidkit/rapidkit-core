"""Minimal compatibility shim for Typer help rendering.

We avoid patching Click/Typer internals. Dependency pins ensure
compatibility and here we just disable rich/markup to keep help stable.
"""

from __future__ import annotations

import contextlib
from typing import Any, Callable, Optional, cast

# Disable Typer's rich help when Typer is present; this avoids invoking
# rich-driven helpers that may exercise varying internal signatures.
with contextlib.suppress(ImportError):
    import typer

    with contextlib.suppress(AttributeError):
        typer.rich = None  # type: ignore[attr-defined]

    # Also try to disable rich integration completely
    with contextlib.suppress(AttributeError):
        typer.core.rich = None  # type: ignore

    # Try to disable rich console integration by setting environment variables
    with contextlib.suppress(AttributeError, ImportError):
        import os

        os.environ["NO_COLOR"] = "1"
        os.environ["TERM"] = "dumb"

with contextlib.suppress(ImportError):
    import click

    _sanitize_console_text: Optional[Callable[[str], str]]

    try:
        from .ui.printer import sanitize_console_text as _sanitize_console_text
    except ImportError:
        _sanitize_console_text = None
    else:
        _click_echo = click.utils.echo

        def _safe_echo(
            message: Any = None,
            file: Any = None,
            nl: bool = True,
            err: bool = False,
            color: Any = None,
            **kwargs: Any,
        ) -> Any:
            if isinstance(message, str) and _sanitize_console_text is not None:
                message = _sanitize_console_text(message)
            return _click_echo(
                message=message,
                file=file,
                nl=nl,
                err=err,
                color=color,
                **kwargs,
            )

        click.utils.echo = _safe_echo
        click.echo = _safe_echo

        with contextlib.suppress(ImportError):
            import click.decorators as _click_decorators

            cast(Any, _click_decorators).echo = _safe_echo

        with contextlib.suppress(ImportError):
            import click.termui as _click_termui

            cast(Any, _click_termui).echo = _safe_echo
__all__ = ["Any", "Optional", "cast"]
