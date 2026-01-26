#!/usr/bin/env python3
# rapidkit_cli.py
"""RapidKit Global CLI - Next.js-style project commands with automatic detection."""

import argparse
import shutil
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from typing import Callable, Protocol, cast

try:
    import tomllib
except ModuleNotFoundError:  # Python <3.11
    import tomli as tomllib

# Add the src directory to the path for imports
core_root = Path(__file__).parent
src_path = core_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def _print_global_help() -> None:
    """Display global CLI help message."""
    parser = argparse.ArgumentParser(
        description="🚀 RapidKit Global CLI - Next.js-style professional commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🏗️  Global Engine Commands (run anywhere):
  rapidkit create <name>    📦 Create new project
  rapidkit add <module>     ➕ Add module to project
  rapidkit dev <command>    🔧 Developer tools for contributors
  rapidkit upgrade          🔄 Upgrade project templates
  rapidkit diff             📋 Compare template changes
  rapidkit doctor           🩺 Check development environment
  rapidkit --tui            🖥️  Launch interactive TUI
  rapidkit --version        ℹ️  Show version information

🚀 Project Commands (run within RapidKit projects):
  rapidkit init             📦 Initialize project (create .venv, install poetry, dependencies)
  rapidkit dev              ⚡ Start development server
  rapidkit build            📦 Build for production
  rapidkit start            ⚡ Start production server
  rapidkit test             🧪 Run tests with coverage
  rapidkit lint             🔧 Run linting checks
  rapidkit format           ✨ Format code automatically
  rapidkit help             📚 Show project help

Examples:
  rapidkit create my-api          # Create FastAPI project
  cd my-api && rapidkit dev       # Start development
  rapidkit add module auth        # Add authentication
  rapidkit test                   # Run project tests

Note: Project commands auto-detect .rapidkit/ directory
        """,
    )
    parser.print_help()


def _find_project_root() -> Path | None:
    """Find RapidKit project root by looking for .rapidkit directory with project.json."""
    current = Path.cwd()

    # Check current directory and all parents
    for path in [current] + list(current.parents):
        rapidkit_dir = path / ".rapidkit"
        project_json = rapidkit_dir / "project.json"

        # Must have both .rapidkit directory AND project.json file
        if rapidkit_dir.exists() and rapidkit_dir.is_dir() and project_json.exists():
            return path

    return None


def _print_banner(emoji: str, message: str, color_code: str = "36") -> None:
    """Print colored banner message."""
    print(f"\033[{color_code}m{emoji} {message}\033[0m")


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

    def _run_project_script_direct(
        project_root: Path, command: str, args: list[str], python_exec: str, env: dict
    ) -> bool:
        """Attempt to run the project's console-script entry directly using a python executable.

        Returns True if execution succeeded (exit code 0), False otherwise.
        """
        try:
            data = tomllib.loads(pyproject_toml.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, tomllib.TOMLDecodeError):
            return False

        scripts = {}
        try:
            scripts = data.get("tool", {}).get("poetry", {}).get("scripts", {})
        except (AttributeError, TypeError, KeyError):
            scripts = {}

        target = scripts.get(command)
        if not target or ":" not in target:
            return False

        module, attr = target.split(":", 1)

        # Prepare argv for the target function
        argv = [command] + args
        # Build a small Python one-liner to import and call the entrypoint
        one_liner = (
            "import sys; sys.argv="
            + repr(argv)
            + "; "
            + f"from {module} import {attr} as __entry; __entry()"
        )

        proc = subprocess.run(
            [python_exec, "-c", one_liner], cwd=project_root, env=env, check=False
        )
        return proc.returncode == 0

    # If a project-local CLI exists under .rapidkit/cli.py we prefer calling
    # the callable entrypoints directly with the project's python executable
    # (or the closest available interpreter). This avoids relying on Poetry
    # being present on the system and prevents dispatch issues when the
    # project-local CLI exposes explicit functions.
    project_local_cli = project_root / ".rapidkit" / "cli.py"
    # Prepare environment and python candidate that may be used by either a
    # local CLI wrapper or the Poetry fallback. We try to prefer an active
    # virtualenv, then a project-local `.venv` before falling back to the
    # system Python executable.
    import os

    env = os.environ.copy()

    project_src_path = str(project_root / "src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{project_src_path}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = project_src_path

    venv_env = env.get("VIRTUAL_ENV")

    python_for_module = None
    if venv_env and (Path(venv_env) / "bin" / "python").exists():
        python_for_module = str(Path(venv_env) / "bin" / "python")
    elif (project_root / ".venv" / "bin" / "python").exists():
        python_for_module = str(project_root / ".venv" / "bin" / "python")
    else:
        python_for_module = sys.executable

    if project_local_cli.exists():
        # Prepare a python one-liner that imports the file and invokes the
        # requested function by name (if callable).
        argv = [command] + args
        one_liner = (
            "import importlib.util, sys; sys.argv="
            + repr(argv)
            + "; "
            + f"spec=importlib.util.spec_from_file_location('proj_cli', '{project_local_cli}'); "
            + "mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); "
            + f"fn=getattr(mod, '{command}', None); "
            + "import inspect\n"
            + "if callable(fn):\n    fn()\nelse:\n    raise SystemExit(127)"
        )

        _print_banner("🚀", f"Running project-local .rapidkit/cli.py -> {project_local_cli}", "36")
        _print_banner("📁", f"Project: {project_root.name}", "33")

        try:
            result = subprocess.run(
                [python_for_module, "-c", one_liner], cwd=project_root, env=env, check=False
            )
            sys.exit(result.returncode)
        except FileNotFoundError:
            # No interpreter available -> fall through to poetry logic
            pass

    if pyproject_toml.exists():
        # Use Poetry script with proper environment
        import os

        env = os.environ.copy()

        # Add project src to PYTHONPATH for proper imports
        project_src_path = str(project_root / "src")
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{project_src_path}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = project_src_path

        # Prefer calling an installed `poetry` executable if available,
        # but prefer the currently active virtualenv, then the project's
        # `.venv`, then system `poetry`. If no poetry executable is found,
        # run `python -m poetry` using the venv/python closest to the user.
        venv_poetry = project_root / ".venv" / "bin" / "poetry"
        poetry_path = None

        # 1) Active virtualenv from environment (user may have activated it)
        venv_env = os.environ.get("VIRTUAL_ENV")
        if venv_env:
            venv_env_poetry = Path(venv_env) / "bin" / "poetry"
            if venv_env_poetry.exists():
                poetry_path = str(venv_env_poetry)

        # 2) Project-local .venv
        if poetry_path is None and venv_poetry.exists():
            poetry_path = str(venv_poetry)

        # 3) Poetry on PATH (system / pipx)
        if poetry_path is None:
            which_poetry = shutil.which("poetry")
            if which_poetry:
                poetry_path = which_poetry

        # Choose python executable to use when invoking `-m poetry` fallback
        python_for_module = None
        if venv_env and (Path(venv_env) / "bin" / "python").exists():
            python_for_module = str(Path(venv_env) / "bin" / "python")
        elif (project_root / ".venv" / "bin" / "python").exists():
            python_for_module = str(project_root / ".venv" / "bin" / "python")
        else:
            python_for_module = sys.executable

        if poetry_path:
            poetry_command = [poetry_path, "run", command, *args]
        else:
            poetry_command = [python_for_module, "-m", "poetry", "run", command, *args]

        # Ensure project's venv/bin is earlier in PATH so subprocesses pick it up
        try:
            project_bin = str((project_root / ".venv" / "bin").resolve())
            env_path = env.get("PATH", "")
            if project_bin and project_bin not in env_path:
                env["PATH"] = f"{project_bin}:{env_path}"
        except (OSError, RuntimeError):
            # best-effort, ignore any resolution errors
            pass

        _print_banner("🚀", f"Running: {' '.join(poetry_command)}", "36")
        _print_banner("📁", f"Project: {project_root.name}", "33")

        try:
            result = subprocess.run(poetry_command, cwd=project_root, env=env, check=False)
            # If poetry ran and returned, just exit with its code
            sys.exit(result.returncode)
        except FileNotFoundError:
            # Poetry executable/module not found. Attempt a direct fallback:
            _print_banner("⚠️", "Poetry not available — attempting direct fallback", "33")
            # Try to run the project's console-script target directly
            run_direct = _run_project_script_direct(
                project_root, command, args, python_for_module, env
            )
            if run_direct:
                sys.exit(0)
            _print_banner("❌", "Poetry not found and fallback failed", "31")
            print("💡 Install Poetry: https://python-poetry.org/docs/#installation")
            sys.exit(1)
    else:
        _print_banner("❌", "No pyproject.toml found", "31")
        print("💡 This doesn't appear to be a Poetry-based RapidKit project")
        sys.exit(1)


def _load_enterprise_tui() -> tuple[Callable[[], _RapidTUILike] | None, str | None]:
    """Attempt to import the enterprise TUI factory."""

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

    return cast(Callable[[], _RapidTUILike], rapid_tui_factory), None


def _launch_tui() -> None:
    """Launch the enterprise TUI when available."""

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


def main() -> None:
    """Main global CLI entry point with Next.js-style commands."""
    if len(sys.argv) == 1:
        # No arguments - show help
        _print_global_help()
        return

    # Handle special flags first
    command = sys.argv[1]

    if command in {"--help", "-h"}:
        _print_global_help()
        return

    if command in {"--version", "-v"}:
        version_value = "unknown"

        try:
            mod = import_module("core.config.version")
            get_version = getattr(mod, "get_version", None)
            if callable(get_version):
                version_value = get_version()
        except (ImportError, ModuleNotFoundError):
            pass

        print(f"RapidKit Version v{version_value}")
        return

    if command == "--tui":
        _launch_tui()
        return

    # Define command categories
    global_commands = {
        "create",
        "add",
        "diff",
        "license",
        "upgrade",
        "rollback",
        "uninstall",
        "checkpoint",
        "doctor",
        "optimize",
        "snapshot",
        "frameworks",
        "modules",
        "init",
        "merge",
        "list",
        "info",
    }
    # Project-level commands delegated to local CLI when inside a project
    project_commands = {"start", "build", "test", "lint", "format", "help", "init", "dev"}

    if command in project_commands:
        # Project-specific commands - delegate to local project CLI
        args_start_index = 2
        remaining_args = sys.argv[args_start_index:] if len(sys.argv) > args_start_index else []
        _delegate_to_project_cli(command, remaining_args)
        return

    if command in global_commands:
        # Global engine commands - run in main CLI
        try:
            from cli.main import main as cli_main

            # Keep original args for main CLI processing
            cli_main()
        except ImportError as e:
            _print_banner("❌", f"Failed to import main CLI: {e}", "31")
            print("💡 Make sure you're running from the RapidKit core directory")
            sys.exit(1)
        return

    # Unknown command
    _print_banner("❌", f"Unknown command: {command}", "31")
    _print_banner("💡", "Run 'rapidkit' to see all available commands", "33")
    sys.exit(1)


if __name__ == "__main__":
    main()
