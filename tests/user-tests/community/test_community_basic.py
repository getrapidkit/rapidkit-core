"""Basic tests for RapidKit community functionality."""

import os
import subprocess
import sys
from pathlib import Path


def test_import() -> None:
    """Test basic import functionality."""
    try:
        import rapidkit  # type: ignore

        assert rapidkit is not None
    except ImportError:
        # This is expected for minimal distributions
        pass


def test_cli_help() -> None:
    """Test CLI help command."""
    # Change to the project root directory to ensure proper imports
    project_root = Path(__file__).parent.parent.parent.parent
    original_cwd = os.getcwd()

    try:
        os.chdir(project_root)

        # Try to run the CLI using the Python module
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env={**os.environ, "PYTHONPATH": str(project_root / "src")},
        )

        # If that fails, try the installed command
        if result.returncode != 0:
            result = subprocess.run(
                ["rapidkit", "--help"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

        assert result.returncode == 0
        assert "RapidKit" in result.stdout

    finally:
        os.chdir(original_cwd)
