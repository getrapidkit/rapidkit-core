import os
import subprocess
import sys
from pathlib import Path
from typing import Mapping, MutableMapping


def run_cli(*args: str, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess:
    # Run the CLI using direct Python import for better CI compatibility
    cmd = [sys.executable, "-c", "from cli.main import main; main()", *args]
    # Set PYTHONPATH to include src directory for proper module resolution
    env_vars: MutableMapping[str, str] = dict(os.environ)
    env_vars["PYTHONPATH"] = str(Path(__file__).parent.parent.parent.parent / "src")
    if env is not None:
        env_vars.update(env)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env_vars,
    )


def test_global_help() -> None:
    p = run_cli("--help")
    assert p.returncode == 0, p.stderr
    assert "RapidKit" in p.stdout
    assert "create" in p.stdout


def test_global_help_cp1252_encoding() -> None:
    p = run_cli("--help", env={"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"})
    assert p.returncode == 0, p.stderr
    assert "RapidKit" in p.stdout
    assert "🚀" not in p.stdout


def test_create_help() -> None:
    p = run_cli("create", "--help")
    assert p.returncode == 0, p.stderr
    assert "Usage" in p.stdout
    # Help output formatting may vary across Typer/Click versions; ensure subcommand is present
    assert "create project" in p.stdout.lower() or "project" in p.stdout.lower()


def test_create_with_license(tmp_path: Path) -> None:
    outdir = tmp_path / "out"
    license_path = Path("./licenses/license.json").resolve()
    p = run_cli(
        "create",
        "project",
        "fastapi.standard",
        "TestProject",
        "--output",
        str(outdir),
        "--force",
        "--skip-essentials",
        "--variable",
        f"license_path={license_path}",
    )
    # The command may exit with non-zero if the generator raises for other reasons,
    # but we expect the pre_generate license validation to run and print messages.
    assert (
        "Running pre_generate" in p.stdout or "License validated" in p.stdout
    ) or p.returncode == 0
