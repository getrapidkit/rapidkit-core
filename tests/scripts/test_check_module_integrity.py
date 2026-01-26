"""Smoke tests for the settings integrity automation script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_check_module_integrity_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "scripts/check_module_integrity.py", "--skip-nestjs"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        raise AssertionError(
            "settings module integrity script failed\n" f"stdout:\n{stdout}\n" f"stderr:\n{stderr}"
        )
