#!/usr/bin/env python3
"""RapidKit Global CLI Entry Point - Next.js-style professional commands."""

import contextlib
import json
import os
import shlex
import subprocess  # nosec # safe: controlled command execution for Poetry delegation
import sys
from importlib import import_module
from json import JSONDecodeError
from pathlib import Path
from typing import Callable, Protocol, cast

from core.config.version import get_version

ENGINE_FLAG_MIN_ARGS = 2


def _distribution_tier() -> str | None:
    """Best-effort distribution tier detection for installed packages."""

    forced = os.environ.get("RAPIDKIT_FORCE_TIER")
    if forced:
        return forced.strip().lower()

    try:
        import core as core_pkg
    except ModuleNotFoundError:
        return None

    core_file = getattr(core_pkg, "__file__", None)
    if not core_file:
        return "community"

    marker_path = Path(core_file).resolve().parent / "distribution.json"
    if not marker_path.exists():
        return "community"

    try:
        data = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, JSONDecodeError):
        return "community"

    tier = data.get("tier")
    return str(tier).strip().lower() if tier else "community"


def _activation_snippet(project_root: Path) -> str:
    """Return a shell-safe activation snippet that can be eval'd in the user's shell.

    This prints a small script that sources the project's virtualenv activation
    script (if present) in a platform-friendly way and adds the project root to PATH.
    The intended usage is: eval "$(rapidkit shell activate)"
    """
    project_root = project_root.resolve()
    root_quoted = shlex.quote(str(project_root))
    return (
        '# RapidKit: activation snippet - eval "$(rapidkit shell activate)"\n'
        f"RAPIDKIT_ROOT={root_quoted}\n"
        'VENV="$RAPIDKIT_ROOT/.venv"\n'
        'if [ -f "$VENV/bin/activate" ]; then\n'
        "  # bash/zsh\n"
        '  . "$VENV/bin/activate"\n'
        'elif [ -f "$VENV/bin/activate.fish" ]; then\n'
        "  # fish\n"
        '  source "$VENV/bin/activate.fish"\n'
        "fi\n"
        "# expose project root on PATH for convenience\n"
        'export RAPIDKIT_PROJECT_ROOT="$RAPIDKIT_ROOT"\n'
        'export PATH="$RAPIDKIT_ROOT/.rapidkit:$RAPIDKIT_ROOT:$PATH"\n'
    )


def _write_activate_file(project_root: Path) -> None:
    """Write a small `.rapidkit/activate` helper script into the project that
    sources the virtualenv activation script and adds the project root to PATH.
    """
    rapid_dir = project_root / ".rapidkit"
    rapid_dir.mkdir(parents=True, exist_ok=True)
    activate_path = rapid_dir / "activate"
    content = _activation_snippet(project_root)
    activate_path.write_text(content, encoding="utf-8")
    # make it readable/executable by scripts (no harm)
    with contextlib.suppress(OSError):
        activate_path.chmod(0o755)
    # chmod may fail on some filesystems; ignore


def _find_project_root() -> Path | None:
    current = Path.cwd()

    # Check current directory and all parents
    for path in [current] + list(current.parents):
        rapidkit_dir = path / ".rapidkit"
        project_json = rapidkit_dir / "project.json"

        # Must have both .rapidkit directory AND project.json file
        if rapidkit_dir.exists() and rapidkit_dir.is_dir() and project_json.exists():
            return path

    return None


def _find_upwards(filename: str) -> Path | None:
    """Find filename by walking parents, return first match."""

    current = Path.cwd()
    for path in [current] + list(current.parents):
        candidate = path / filename
        if candidate.exists():
            return candidate
    return None


def _has_package_json_with_rapidkit() -> bool:
    package_json = _find_upwards("package.json")
    if not package_json:
        return False
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False

    def _contains(dep_map: dict | None) -> bool:
        if not isinstance(dep_map, dict):
            return False
        return any(str(key).startswith("rapidkit") for key in dep_map)

    return _contains(data.get("dependencies")) or _contains(data.get("devDependencies"))


def _detect_engine(argv: list[str]) -> str:
    """Decide which engine to route to: python (default) or node."""

    env_pref = os.environ.get("RAPIDKIT_ENGINE", "auto").lower()
    engine = env_pref if env_pref in {"python", "node"} else "auto"

    if argv and argv[0] == "--engine" and len(argv) >= ENGINE_FLAG_MIN_ARGS:
        flag = argv[1].lower()
        if flag in {"python", "node"}:
            engine = flag
            # strip the flag so downstream sees clean args
            del argv[:2]

    if engine != "auto":
        return engine

    if _find_project_root() is not None:
        return "python"

    if _has_package_json_with_rapidkit():
        return "node"

    return "python"


def _delegate_to_node_cli(argv: list[str]) -> None:
    """Invoke the Node-based rapidkit if present (local npx preferred)."""

    cmd = ["npx", "rapidkit", *argv]
    result = subprocess.run(cmd, check=False)  # nosec B603 - controlled command invocation
    sys.exit(result.returncode)


def _print_banner(emoji: str, message: str, color_code: str = "36") -> None:
    """Print colored banner message."""
    print(f"\033[{color_code}m{emoji} {message}\033[0m")


def _get_engine_commands() -> dict[str, str]:
    """Get available engine commands with descriptions."""
    # Use comprehensive static list - more reliable and complete
    commands = {
        "version": "ℹ️  Show version information",
        "project": "🧭 Project detection utilities",
        "create": "📦 Create new project",
        "add": "➕ Add module to project",
        "list": "📋 List available kits",
        "info": "🔍 Show kit information",
        "ui": "🖥️ UI bridge utilities",
        "upgrade": "🔄 Upgrade project templates",
        "diff": "📋 Compare template changes",
        "doctor": "🩺 Diagnose environment",
        "license": "📄 Manage license",
        "reconcile": "🧩 Reconcile pending snippet injections",
        "rollback": "↩️  Rollback changes",
        "uninstall": "🗑️  Remove module",
        "checkpoint": "💾 Create checkpoint",
        "optimize": "⚡ Optimize project",
        "snapshot": "📸 Snapshot utilities",
        "frameworks": "🏗️  Framework adapters",
        "modules": "🧩 Module utilities",
        "merge": "🔀 Merge changes",
    }

    # Community distributions must not expose UI bridge HTTP surface.
    if _distribution_tier() in {"community", "community-staging"}:
        commands.pop("ui", None)

    return commands


def _get_project_commands() -> dict[str, str]:
    """Get available project commands with descriptions."""
    return {
        "init": "📦 Initialize project (create .venv, install poetry, dependencies)",
        "dev": "🔥 Start development server",
        "start": "⚡ Start production server",
        "build": "📦 Build for production",
        "test": "🧪 Run tests with coverage",
        "lint": "🔧 Run linting checks",
        "format": "✨ Format code automatically",
        "help": "📚 Show project help",
    }


def _print_global_command_help() -> None:
    """Print global command help section."""
    print("🏗️  Global Engine Commands (run anywhere):")
    for cmd, desc in _get_engine_commands().items():
        print(f"  rapidkit {cmd:<12} {desc}")

    print("  rapidkit --tui       🖥️  Launch interactive TUI")
    print("  rapidkit --version   ℹ️  Show version information")
    print("  rapidkit -v          ℹ️  Alias for --version")
    print()


def _print_project_command_help() -> None:
    """Print project command help section."""
    print("🚀 Project Commands (run within RapidKit projects):")
    for cmd, desc in _get_project_commands().items():
        print(f"  rapidkit {cmd:<12} {desc}")

    print()


def _show_help() -> None:
    """Show professional help with comprehensive command listing."""
    print("🚀 RapidKit Global CLI - Next.js-style professional commands")
    print()

    is_project_context = _find_project_root() is not None

    if is_project_context:
        _print_project_command_help()
        _print_global_command_help()
    else:
        _print_global_command_help()
        _print_project_command_help()
    print("Examples:")
    print("  rapidkit create my-api          # Create FastAPI project")
    print("  cd my-api && rapidkit dev       # Start development")
    print("  rapidkit add module auth        # Add authentication")
    print("  rapidkit test                   # Run project tests")
    print()
    print("Note: Project commands auto-detect .rapidkit/ directory")


class _RapidTUILike(Protocol):
    """Protocol describing the RapidTUI interface we rely on."""

    def run(self) -> None:
        """Start the TUI loop."""


def _delegate_to_project_cli(command: str, args: list[str]) -> None:
    """Delegate command to project's local CLI."""
    project_root = _find_project_root()

    if not project_root:
        _print_banner("❌", "No RapidKit project found", "31")
        print("💡 Run this command from within a RapidKit project directory")
        print("💡 Or create a new project with: rapidkit create <project-name>")
        sys.exit(1)

    # Check if project has Poetry
    pyproject_toml = project_root / "pyproject.toml"
    # Prepare environment and python candidate for fallbacks
    env = os.environ.copy()

    # Add project src to PYTHONPATH for proper imports
    project_src_path = str(project_root / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        env["PYTHONPATH"] = os.pathsep.join([project_src_path, existing_pythonpath])
    else:
        env["PYTHONPATH"] = project_src_path

    # Choose python executable to use when invoking fallbacks
    venv_env = env.get("VIRTUAL_ENV")
    python_for_module = None
    if venv_env and (Path(venv_env) / "bin" / "python").exists():
        python_for_module = str(Path(venv_env) / "bin" / "python")
    elif (project_root / ".venv" / "bin" / "python").exists():
        python_for_module = str(project_root / ".venv" / "bin" / "python")
    else:
        python_for_module = sys.executable

    # If a project-local CLI exists prefer invoking its callable function
    project_local_cli = project_root / ".rapidkit" / "cli.py"
    if project_local_cli.exists():
        try:
            argv = [command] + args
            # Build a small execution snippet that parses common flags and forwards
            # them as keyword args to the callable in the project-local CLI if
            # possible. Falls back to calling the function without kwargs.
            one_liner = (
                "import importlib.util, sys, argparse; sys.argv="
                + repr(argv)
                + "; "
                + f"spec=importlib.util.spec_from_file_location('proj_cli', '{project_local_cli}'); "
                + "mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); "
                + "fn=getattr(mod, '"
                + command
                + "', None); "
                + "\nif callable(fn):\n"
                + "    parser=argparse.ArgumentParser(prog='rapidkit "
                + command
                + "', add_help=False)\n"
                + "    parser.add_argument('-p', '--port', type=int, dest='port')\n"
                + "    parser.add_argument('--allow-global-runtime', action='store_true', dest='allow_global_runtime')\n"
                + "    parser.add_argument('--host', dest='host')\n"
                + "    ns, _ = parser.parse_known_args(sys.argv[1:])\n"
                + "    kwargs = {}\n"
                + "    if getattr(ns, 'port', None) is not None: kwargs['port'] = ns.port\n"
                + "    if getattr(ns, 'host', None) is not None: kwargs['host'] = ns.host\n"
                + "    if getattr(ns, 'allow_global_runtime', None): kwargs['allow_global_runtime'] = True\n"
                + "    try:\n        fn(**kwargs)\n    except TypeError:\n        fn()\n"
                + "else:\n    raise SystemExit(127)"
            )
            _print_banner(
                "🚀", f"Running project-local .rapidkit/cli.py -> {project_local_cli}", "36"
            )
            _print_banner("📁", f"Project: {project_root.name}", "33")
            result = subprocess.run(  # nosec - controlled python one-liner executed without shell
                [python_for_module, "-c", one_liner], cwd=project_root, env=env, check=False
            )
            # If this was an init and it succeeded, ensure .rapidkit/activate exists
            if command == "init" and result.returncode == 0:
                try:
                    _write_activate_file(project_root)
                    print("\n✅ Created .rapidkit/activate helper.")
                    print("💡 To activate the project in your current shell run:")
                    print('  eval "$(rapidkit shell activate)"')
                    print("")
                except OSError:
                    pass
            sys.exit(result.returncode)
        except FileNotFoundError:
            # Interpreter missing - fall through to poetry
            pass

    if pyproject_toml.exists():
        # Use Poetry script with proper environment

        # Add project src to PYTHONPATH for proper imports
        project_src_path = str(project_root / "src")
        existing_pythonpath = env.get("PYTHONPATH")
        if existing_pythonpath:
            env["PYTHONPATH"] = os.pathsep.join([project_src_path, existing_pythonpath])
        else:
            env["PYTHONPATH"] = project_src_path

        poetry_command = [sys.executable, "-m", "poetry", "run", command, *args]
        _print_banner("🚀", f"Running: {' '.join(poetry_command)}", "36")
        _print_banner("📁", f"Project: {project_root.name}", "33")

        try:
            result = subprocess.run(  # nosec B603 # safe: controlled CLI command execution
                poetry_command, cwd=project_root, env=env, check=False
            )
            # If init succeeded, create an activation helper
            if command == "init" and result.returncode == 0:
                try:
                    _write_activate_file(project_root)
                    print("\n✅ Created .rapidkit/activate helper.")
                    print("💡 To activate the project in your current shell run:")
                    print('  eval "$(rapidkit shell activate)"')
                    print("")
                except OSError:
                    pass
            sys.exit(result.returncode)
        except FileNotFoundError:
            _print_banner("❌", "Poetry not found", "31")
            print("💡 Install Poetry: https://python-poetry.org/docs/#installation")
            sys.exit(1)
    else:
        _print_banner("❌", "No pyproject.toml found", "31")
        print("💡 This doesn't appear to be a Poetry-based RapidKit project")
        sys.exit(1)


def _load_enterprise_tui() -> tuple[Callable[[], _RapidTUILike] | None, str | None]:
    """Try to import the enterprise TUI factory."""

    try:
        module = import_module("core.tui.main_tui")
    except ModuleNotFoundError:
        return None, (
            "Interactive TUI is not bundled in this edition. "
            "Upgrade to a RapidKit enterprise license to unlock it."
        )
    except ImportError as exc:  # pragma: no cover - defensive guard
        return None, f"Failed to import enterprise TUI backend: {exc}"

    rapid_tui_factory = getattr(module, "RapidTUI", None)
    if rapid_tui_factory is None:
        return None, "Enterprise TUI module is missing the RapidTUI entrypoint."

    if not callable(rapid_tui_factory):
        return None, "Enterprise TUI entrypoint is not callable."

    factory = cast(Callable[[], _RapidTUILike], rapid_tui_factory)
    return factory, None


def _launch_tui() -> None:
    """Launch the TUI interface if available, otherwise guide the user."""

    rapid_tui_factory, error_message = _load_enterprise_tui()
    if rapid_tui_factory is None:
        _print_banner("ℹ️", "Interactive TUI unavailable", "34")
        print(f"💡 {error_message}")
        return

    print("🚀 Starting RapidKit Enterprise TUI...")
    print("📍 Controls: Press 'q' to quit, use number keys to navigate")
    try:
        tui = rapid_tui_factory()
        tui.run()
        print("✅ TUI session ended successfully!")
    except (RuntimeError, ImportError, OSError, TypeError, ValueError) as exc:
        _print_banner("❌", f"TUI Error: {exc}", "31")
        print("💡 Make sure curses library is installed")
        sys.exit(1)


def _delegate_if_context_engine(argv: list[str]) -> bool:
    """Delegate to Node CLI when context.json requests npm engine."""

    rapidkit_dir = Path.cwd() / ".rapidkit"
    context_file = rapidkit_dir / "context.json"
    if not context_file.exists():
        return False
    try:
        ctx = json.loads(context_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if ctx.get("engine") == "npm":
        _delegate_to_node_cli(list(argv))
        return True
    return False


def _handle_shell_command(args: list[str]) -> bool:
    """Handle `rapidkit shell ...` invocations."""

    sub = args[0] if args else None
    if sub == "activate":
        proj = _find_project_root()
        if not proj:
            _print_banner("❌", "No RapidKit project found to activate", "31")
            print("💡 Run this from within a RapidKit project directory.")
            sys.exit(1)
        snippet = _activation_snippet(proj)
        _print_banner(
            "✅",
            "Activation snippet — run the following to activate this project in your current shell:",
            "32",
        )
        print(snippet)
        print("\n💡 After activation you can run: rapidkit dev")
        return True
    _print_banner("❌", f"Unknown shell command: {sub}", "31")
    return False


def _run_global_command(argv: list[str]) -> None:
    command = argv[0] if argv else None
    if command is None or command in {"--help", "-h"}:
        _show_help()
        return

    if command == "shell":
        if _handle_shell_command(argv[1:]):
            return
        sys.exit(1)

    if command in {"--version", "-v"}:
        package_version = get_version()
        if "--json" in argv:
            print(json.dumps({"schema_version": 1, "version": package_version}, ensure_ascii=False))
        else:
            print(f"RapidKit Version v{package_version}")
        return

    if command == "--tui":
        _launch_tui()
        return

    if command == "ui" and _distribution_tier() in {"community", "community-staging"}:
        # Do not reveal paid/internal surfaces in community builds.
        print("Error: No such command 'ui'.", file=sys.stderr)
        sys.exit(2)

    project_commands = {"dev", "start", "build", "test", "lint", "format", "help"}
    if command in project_commands:
        remaining_args = argv[1:] if len(argv) > 1 else []
        _delegate_to_project_cli(command, remaining_args)
        return

    global_commands = {
        "version",
        "project",
        "create",
        "add",
        "diff",
        "license",
        "upgrade",
        "reconcile",
        "rollback",
        "uninstall",
        "checkpoint",
        "doctor",
        "optimize",
        "snapshot",
        "frameworks",
        "modules",
        "merge",
        "init",
        "list",
        "info",
        "ui",
    }

    if _distribution_tier() in {"community", "community-staging"}:
        global_commands.discard("ui")
    if command in global_commands:
        try:
            from cli.main import main as cli_main  # noqa: E402

            sys.argv = [sys.argv[0], *argv]
            cli_main()
        except ImportError as exc:
            _print_banner("❌", f"Failed to import main CLI: {exc}", "31")
            print("💡 Make sure you're running from the RapidKit core directory")
            sys.exit(1)
        return

    _print_banner("❌", f"Unknown command: {command}", "31")
    _print_banner("💡", "Run 'rapidkit' to see all available commands", "33")
    sys.exit(1)


def main() -> None:
    """Main global CLI entry point with Next.js-style commands."""

    argv = sys.argv[1:]
    if _delegate_if_context_engine(argv):
        return

    engine = _detect_engine(argv)
    if engine == "node":
        _delegate_to_node_cli(argv)
        return

    _run_global_command(argv)


if __name__ == "__main__":
    main()
