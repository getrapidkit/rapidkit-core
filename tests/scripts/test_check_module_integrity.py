"""Smoke tests for the settings integrity automation script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts import check_module_integrity


@pytest.mark.external_tooling
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


def test_nestjs_smoke_non_strict_skips_execution_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(check_module_integrity.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(check_module_integrity, "NESTJS_SMOKE_SCRIPT", tmp_path / "smoke.js")
    (tmp_path / "smoke.js").write_text("throw new Error('offline')", encoding="utf-8")
    monkeypatch.setattr(
        check_module_integrity.tempfile, "mkdtemp", lambda prefix: str(tmp_path / prefix)
    )

    def fail_run(*_args: object, **_kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, ["node", "smoke.js"])

    monkeypatch.setattr(check_module_integrity.subprocess, "run", fail_run)

    check_module_integrity.run_nestjs_smoke(strict=False)


def test_nestjs_smoke_strict_fails_execution_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(check_module_integrity.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(check_module_integrity, "NESTJS_SMOKE_SCRIPT", tmp_path / "smoke.js")
    (tmp_path / "smoke.js").write_text("throw new Error('offline')", encoding="utf-8")
    monkeypatch.setattr(
        check_module_integrity.tempfile, "mkdtemp", lambda prefix: str(tmp_path / prefix)
    )

    def fail_run(*_args: object, **_kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, ["node", "smoke.js"])

    monkeypatch.setattr(check_module_integrity.subprocess, "run", fail_run)

    with pytest.raises(subprocess.CalledProcessError):
        check_module_integrity.run_nestjs_smoke(strict=True)
