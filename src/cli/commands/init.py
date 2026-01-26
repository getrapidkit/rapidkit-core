"""Project bootstrap initializer command.

Provides `rapidkit init` which bootstraps a project:
- creates `.venv` if missing,
- installs `poetry` into the venv if not available,
- runs `poetry install` to install project dependencies.

This helps novice users avoid a separate `pip install poetry` step.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec - controlled use (non-shell, static arguments)
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Bootstrap project dependencies and virtualenv")


def _find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    cur = (start or Path.cwd()).resolve()
    for p in [cur] + list(cur.parents):
        if (p / ".rapidkit").is_dir() and (p / ".rapidkit" / "project.json").exists():
            return p
    return None


def _sync_poetry_lock(poetry_exec: str, root: Path) -> None:
    """Make sure poetry.lock matches the current pyproject configuration."""

    lock_path = root / "poetry.lock"
    if lock_path.exists():
        typer.echo("🔄 Ensuring poetry.lock matches pyproject.toml (poetry lock --no-update)")
        commands: list[list[str]] = [[poetry_exec, "lock", "--no-update"]]
    else:
        typer.echo("ℹ️  Generating poetry.lock via poetry lock")
        commands = [[poetry_exec, "lock"]]

    # If an older Poetry version is on PATH, '--no-update' may be unsupported.
    # Detect that error and retry with plain 'poetry lock' automatically.
    for _idx, cmd in enumerate(commands):
        try:
            subprocess.run(cmd, cwd=root, check=True, capture_output=True, text=True)  # nosec
            return
        except subprocess.CalledProcessError as exc:  # pragma: no cover - external tool failure
            output = (exc.stderr or "") + (exc.stdout or "")
            help_hint = output.lower()
            missing_flag = "--no-update" in cmd and "does not exist" in help_hint
            if missing_flag and len(commands) == 1:
                typer.echo(
                    "ℹ️  Installed Poetry version does not support '--no-update'. Falling back to 'poetry lock'."
                )
                commands.append([poetry_exec, "lock"])
                continue

            typer.echo(f"❌ Failed to run {' '.join(cmd)}: {exc}")
            if output.strip():
                typer.echo(output)
            if "--no-update" in cmd:
                typer.echo(
                    "💡 Run 'poetry lock --no-update' (or plain 'poetry lock' if unsupported) manually inside the project for more details."
                )
            else:
                typer.echo("💡 Run 'poetry lock' manually inside the project for more details.")
            raise typer.Exit(code=1) from exc


@app.command("init")
def init(project: Optional[Path] = None) -> None:
    """Bootstrap the project: create `.venv`, ensure poetry, and run `poetry install`.

    Examples:
      rapidkit init
      rapidkit init /path/to/project
    """
    start = project.resolve() if project else Path.cwd().resolve()
    root = _find_project_root(start)
    if root is None:
        typer.echo("❌ Not inside a RapidKit project (no .rapidkit/project.json found)")
        raise typer.Exit(code=1)

    pyproject = root / "pyproject.toml"
    package_json = root / "package.json"

    # If this is a Node project prefer the project launcher or package manager
    if package_json.exists():
        # Try to detect engine constraints in package.json and give a helpful error
        try:
            import json

            with package_json.open(encoding="utf-8") as fh:
                pkg = json.load(fh)
            engines = pkg.get("engines") or {}
            node_engine = engines.get("node")
        except (OSError, ValueError):
            node_engine = None

        if node_engine:
            # Naive major-version check for common forms like ">=20", "^20", "20.x"
            import re

            m = re.search(r"(\d+)", str(node_engine))
            try:
                required_major = int(m.group(1)) if m else None
            except (AttributeError, ValueError, TypeError):
                # Guard against malformed engine strings or unexpected values
                required_major = None

            # Check system node version
            node_exec = shutil.which("node")
            if node_exec and required_major is not None:
                try:
                    ver_proc = subprocess.run(  # nosec
                        [node_exec, "--version"], capture_output=True, text=True, check=True
                    )
                    cur_v = ver_proc.stdout.strip().lstrip("v")  # nosec
                    cur_major = int(cur_v.split(".")[0]) if cur_v else None
                except (subprocess.CalledProcessError, OSError):
                    cur_major = None

                if (
                    cur_major is not None
                    and required_major is not None
                    and cur_major < required_major
                ):
                    typer.echo(
                        f"❌ Project requires Node {node_engine} but system node is v{cur_v}."
                    )
                    typer.echo(
                        f"💡 Install a compatible Node (>= {required_major}). Use nvm, asdf, or run via Docker to proceed."
                    )
                    raise typer.Exit(code=1)
        # prefer local project launcher if present
        launcher = root / ".rapidkit" / "rapidkit"
        if launcher.exists() and launcher.is_file() and launcher.stat().st_mode & 0o111:
            typer.echo(f"🚀 Detected Node project; delegating to local launcher: {launcher}")
            proc = subprocess.run(  # nosec
                [str(launcher), "init"], check=False, cwd=root, capture_output=True, text=True
            )
            if proc.returncode == 0:  # nosec
                typer.echo("✅ Dependencies installed via project launcher")
                return
            # Provide more helpful guidance on common failure modes
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if "engine" in combined or "incompatible" in combined:
                typer.echo(
                    "❌ Node package engine mismatch detected while installing dependencies."
                )
                typer.echo(
                    "💡 This usually means your system Node.js version is incompatible with some packages (e.g. requires Node >= 20)."
                )
                typer.echo(
                    "👉 Options: install a compatible Node version (nvm/asdf), run via Docker, or use --ignore-engines (not recommended)."
                )
                raise typer.Exit(code=1)
            typer.echo(f"❌ Local launcher failed: {proc.returncode}")
            typer.echo(combined)
            raise typer.Exit(code=1)

        # No local launcher or not executable — try to pick a node package manager
        # prefer pnpm -> yarn -> npm
        pm = shutil.which("pnpm") or shutil.which("yarn") or shutil.which("npm")
        if not pm:
            typer.echo(
                "❌ No Node package manager found (pnpm/yarn/npm). Install Node and a package manager to continue."
            )
            raise typer.Exit(code=1)

        # Run the install command with the selected package manager
        typer.echo(f"🚀 Using package manager: {pm} to install dependencies")
        # Run the install and capture output so we can detect common failures
        proc = subprocess.run(  # nosec
            [pm, "install"], check=False, cwd=root, capture_output=True, text=True
        )
        if proc.returncode == 0:  # nosec
            typer.echo("✅ Node dependencies installed")
            return
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if "engine" in combined or "incompatible" in combined:
            typer.echo("❌ Node package engine mismatch detected while installing dependencies.")
            typer.echo(
                "💡 This usually means your system Node.js version is incompatible with some packages (e.g. requires Node >= 20)."
            )
            typer.echo(
                "👉 Options: install a compatible Node version (nvm/asdf), run via Docker, or use --ignore-engines (not recommended)."
            )
            raise typer.Exit(code=1)
        typer.echo(f"❌ package manager install failed: {proc.returncode}")
        typer.echo(combined)
        raise typer.Exit(code=1)

    # Otherwise rely on Poetry/pyproject for Python projects
    if not pyproject.exists():
        typer.echo("❌ No pyproject.toml found in project — cannot install dependencies")
        raise typer.Exit(code=1)

    # Prefer system poetry if available
    poetry_exec = shutil.which("poetry")

    if poetry_exec:
        typer.echo(f"🚀 Using system poetry: {poetry_exec}")
        try:
            _sync_poetry_lock(poetry_exec, root)
            subprocess.run([poetry_exec, "install"], cwd=root, check=True)  # nosec
            typer.echo("✅ Dependencies installed via system poetry")
            return
        except subprocess.CalledProcessError as e:
            typer.echo(f"❌ poetry install failed: {e}")
            raise typer.Exit(code=1) from e

    # Ensure project .venv exists
    venv_dir = root / ".venv"
    venv_python = venv_dir / "bin" / "python"
    if not venv_dir.exists():
        typer.echo("ℹ️  Creating project virtualenv at .venv")
        py = shutil.which("python3") or shutil.which("python")
        if not py:
            typer.echo("❌ No python interpreter found to create virtualenv")
            raise typer.Exit(code=1)
        try:
            subprocess.run(
                [py, "-m", "venv", str(venv_dir)], check=True
            )  # nosec - creating venv with known python
        except subprocess.CalledProcessError as e:
            typer.echo(f"❌ Failed to create virtualenv: {e}")
            raise typer.Exit(code=1) from e

    if not venv_python.exists():
        typer.echo("❌ venv python not found after creation")
        raise typer.Exit(code=1)

    # Upgrade pip and install poetry into venv
    try:
        subprocess.run([str(venv_python), "-m", "pip", "install", "-U", "pip"], check=True)  # nosec
        subprocess.run([str(venv_python), "-m", "pip", "install", "poetry"], check=True)  # nosec
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Failed to install tooling into venv: {e}")
        raise typer.Exit(code=1) from e

    venv_poetry = venv_dir / "bin" / "poetry"
    if not venv_poetry.exists():
        typer.echo("❌ poetry executable not found in venv after install")
        raise typer.Exit(code=1)

    typer.echo("🚀 Running poetry install inside project .venv")
    try:
        _sync_poetry_lock(str(venv_poetry), root)
        subprocess.run([str(venv_poetry), "install"], cwd=root, check=True)  # nosec
        typer.echo("✅ Project bootstrapped successfully")
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ poetry install failed: {e}")
        raise typer.Exit(code=1) from e
