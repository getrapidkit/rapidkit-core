"""Shared lockfile generation helpers for scaffolded kits."""

from __future__ import annotations

import os

# subprocess is used for static lockfile generation commands selected by kit code.
import subprocess  # nosec B404
from pathlib import Path
from typing import Mapping, Sequence


def is_truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def is_falsey(value: object) -> bool:
    return str(value).strip().lower() in {"0", "false", "no", "off"}


def should_generate_lockfile(variables: Mapping[str, object] | None = None) -> bool:
    should_generate = True
    env_toggle = os.environ.get("RAPIDKIT_GENERATE_LOCKS")
    if env_toggle is not None:
        should_generate = is_truthy(env_toggle)
    elif is_truthy(os.environ.get("RAPIDKIT_SKIP_LOCKS", "0")):
        should_generate = False
    elif variables and "generate_lock" in variables:
        value = variables.get("generate_lock", True)
        if isinstance(value, bool):
            should_generate = value
        elif value is None or is_falsey(value):
            should_generate = False
        elif is_truthy(value):
            should_generate = True
        else:
            should_generate = bool(value)
    return should_generate


def _summarize_lockfile_failure(stdout: str | None, stderr: str | None, returncode: int) -> str:
    stderr_lines = [line.strip() for line in (stderr or "").splitlines() if line.strip()]
    stdout_lines = [line.strip() for line in (stdout or "").splitlines() if line.strip()]
    lines = [
        line.strip() for line in f"{stderr or ''}\n{stdout or ''}".splitlines() if line.strip()
    ]
    for line in lines:
        lowered = line.lower()
        if lowered.startswith(("error ", "error:", "virtualenv: error")):
            return line.removeprefix("error Error: ").removeprefix("Error: ")
    if stderr_lines:
        return stderr_lines[-1]
    if stdout_lines:
        return stdout_lines[-1]
    return lines[-1] if lines else f"exit code {returncode}"


def attempt_lockfile_generation(
    *,
    output_path: Path,
    command: Sequence[str],
    label: str,
) -> None:
    print(f"\nℹ️ Generating {label} (automatic lockfiles enabled)")
    try:
        # Command is selected from trusted kit code and executed without shell.
        result = subprocess.run(
            list(command),
            cwd=str(output_path),
            check=False,
            capture_output=True,
            text=True,
        )  # nosec B603
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as exc:
        print(f"⚠️  {label} generation skipped: {exc}")
        return

    if result.returncode == 0:
        print(f"ℹ️ {label} generated.")
        return

    detail = _summarize_lockfile_failure(result.stdout, result.stderr, result.returncode)
    print(f"⚠️  {label} generation skipped: {detail}")
    print("   Run the package manager install command later when dependencies are available.")
