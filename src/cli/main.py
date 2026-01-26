# src/cli/main.py
"""CLI entrypoint -- ensure compatibility shims are applied early.

This file intentionally keeps runtime shims out oflined here. Import
`_compat` early so the rest of the CLI can assume a stable Click/Typer
surface for help rendering.
"""

import contextlib
import importlib
import inspect
import sys
from typing import Any, Callable, Iterable, Optional, Sequence, Tuple, cast

import click
import typer

from core.config.version import get_version

# Import compatibility shim for side effects (disables rich help). Do not export names.
from . import _compat as _compat_shim  # noqa: F401

# --- Imports after patching --------------------------------------------------
from .commands import create_app, info, license_app
from .commands.add import add_app
from .commands.checkpoint import checkpoint_app
from .commands.dev import dev_app
from .commands.diff import diff_app
from .commands.doctor import doctor_app
from .commands.frameworks import frameworks_app
from .commands.init import init as init_cmd
from .commands.list import list_kits
from .commands.merge import merge_app
from .commands.migrate import migrate_app
from .commands.modules import modules_app
from .commands.optimize import opt_app
from .commands.reconcile import reconcile
from .commands.rollback import rollback_app
from .commands.snapshot import snapshot_app
from .commands.uninstall import uninstall_app
from .commands.upgrade import upgrade_app
from .ui.printer import print_banner, print_error, print_info, sanitize_console_text

ui_app: Optional[typer.Typer] = None


def _load_ui_app() -> Optional[typer.Typer]:
    """Attempt to import the optional UI command tree.

    Community distributions omit the UI bridge entirely. Import lazily so
    environments without the UI module (or its heavy dependencies) can still
    type-check and run the remaining CLI surface.
    """

    try:
        module = importlib.import_module("cli.commands.ui")
    except ImportError:
        return None

    loaded_app = getattr(module, "ui_app", None)
    if isinstance(loaded_app, typer.Typer):
        return loaded_app
    return None


ui_app = _load_ui_app()


def _harden_io_streams() -> None:
    """Prefer replace error handling for stdio on legacy encodings."""

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue

        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue

        encoding = getattr(stream, "encoding", None)
        if not encoding:
            continue

        errors = getattr(stream, "errors", None)
        if errors == "replace":
            continue

        with contextlib.suppress(Exception):
            reconfigure(encoding=encoding, errors="replace")


def _sanitize_option_decls(typer_app: typer.Typer) -> None:
    """Remove non-string option declarations to avoid click parse crashes.

    Some OptionInfo instances may carry accidental boolean entries in
    `param_decls`, which click rejects (expects strings for option names).
    We defensively strip any non-string entries before Click command
    construction. This keeps the CLI resilient without altering runtime
    behaviour for valid options.
    """

    stack = [typer_app]
    seen: set[int] = set()
    while stack:
        current = stack.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))

        for cmd in getattr(current, "registered_commands", []):
            callback = getattr(cmd, "callback", None)
            if not callback:
                continue
            for param in inspect.signature(callback).parameters.values():
                default = param.default
                param_decls = getattr(default, "param_decls", None)
                if not param_decls:
                    continue
                cleaned = tuple(d for d in param_decls if isinstance(d, str))
                if cleaned != param_decls:
                    with contextlib.suppress(AttributeError, TypeError):
                        # If mutation is disallowed, at least avoid crashing.
                        default.param_decls = cleaned

        for group_info in getattr(current, "registered_groups", []):
            nested = getattr(group_info, "typer_instance", None)
            if nested:
                stack.append(nested)


def _apply_option_sanitizers(typer_app: typer.Typer) -> None:
    """Defend against malformed option declarations before Click builds commands."""

    _sanitize_option_decls(typer_app)

    # Guarded monkeypatch: strip non-string decls before click inspects them.
    stored_parse = getattr(click.core.Option, "_rapid_orig_parse_decls", None)
    if stored_parse is None:
        ParseDeclsFn = Callable[
            [click.core.Option, Sequence[str], bool],
            Tuple[Any, list[str], list[str]],
        ]
        original_parse: ParseDeclsFn = click.core.Option._parse_decls

        def _safe_parse_decls(
            self: click.core.Option,
            decls: Iterable[Any],
            expose_value: bool,
        ) -> Tuple[Any, list[str], list[str]]:
            clean_decls = tuple(d for d in decls if isinstance(d, str))
            return original_parse(self, clean_decls, expose_value)

        option_cls = cast(Any, click.core.Option)
        option_cls._rapid_orig_parse_decls = original_parse
        option_cls._parse_decls = _safe_parse_decls


# --- CLI App -----------------------------------------------------------------
app = typer.Typer(
    help=sanitize_console_text(
        """🚀 RapidKit - FastAPI project generator with Clean Architecture

🎯 Interactive Features:
  • rapidkit create project --interactive    # Guided project setup
  • rapidkit modules install-interactive     # Browse & install modules
  • rapidkit modules configure               # Setup project configuration

🔍 Module Management:
  • rapidkit modules list                    # Browse available modules
  • rapidkit modules search <query>          # Search modules
  • rapidkit modules info <name>             # Detailed module info"""
    ),
    no_args_is_help=True,
    rich_markup_mode=None,  # Disable rich markup to avoid compatibility issues
    rich_help_panel=None,  # Disable rich help panels
)

# Touch the shim symbol to avoid 'unused import' while preserving side effects.
_ = _compat_shim  # noqa: F841

# Register subcommands
app.add_typer(create_app, name="create")
app.add_typer(add_app, name="add")
app.add_typer(dev_app, name="dev")
app.add_typer(diff_app, name="diff")
app.add_typer(license_app, name="license")
app.add_typer(upgrade_app, name="upgrade")
app.add_typer(rollback_app, name="rollback")
app.add_typer(uninstall_app, name="uninstall")
app.add_typer(checkpoint_app, name="checkpoint")
app.command(name="list")(list_kits)
app.command(name="info")(info)
app.add_typer(doctor_app, name="doctor")
app.add_typer(opt_app, name="optimize")
app.add_typer(snapshot_app, name="snapshot")
app.add_typer(frameworks_app, name="frameworks")
app.add_typer(modules_app, name="modules")
app.add_typer(merge_app, name="merge")
app.add_typer(migrate_app, name="migrate")
# Register init as a direct top-level command (simple UX for beginners)
app.command(name="init")(init_cmd)
app.command(name="reconcile")(reconcile)

if ui_app is not None:
    app.add_typer(ui_app, name="ui")

# Apply sanitizers at import time so Typer testing also benefits
_apply_option_sanitizers(app)


@app.command("tui")
def launch_tui() -> None:
    """Launch Terminal User Interface."""
    try:
        from core.tui import RapidTUI

        print_info("🚀 Starting RapidKit Enterprise TUI...")
        tui = RapidTUI()
        tui.run()
    except ImportError as e:
        print_error(f"❌ TUI not available: {e}")
        print_info(
            "Install curses library: pip install windows-curses (Windows) "
            "or apt-get install libncurses5-dev (Linux)"
        )
        raise typer.Exit(code=1) from None
    except (RuntimeError, OSError) as e:
        print_error(f"❌ TUI error: {e}")
        raise typer.Exit(code=1) from None


def main() -> None:
    """Function to start the CLI application."""
    try:
        _harden_io_streams()
        _sanitize_option_decls(app)
        _apply_option_sanitizers(app)
        argv = sys.argv[1:]

        if "--version" in argv or "-v" in argv:
            typer.echo(f"RapidKit Version v{get_version()}")
            return
        # Check for CI mode before Typer processes arguments
        ci_mode = "--ci" in argv
        json_mode = "--json" in argv
        help_mode = "--help" in argv

        # Only print banner if neither --json nor --ci flag is present AND not showing help
        if not ci_mode and not json_mode and not help_mode:
            print_banner()
        app()
    except KeyboardInterrupt:
        print_error("❌ Operation cancelled by user")
        raise typer.Exit(code=1) from None
    except (typer.Exit, click.exceptions.Exit):
        raise
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        print_error(f"❌ Unexpected error: {exc}")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    main()
