"""Utility to surface GitHub Actions toggle state locally.

This script reads `.github/run-github-actions.flag`, normalizes the value,
prints the current state (ENABLE/DISABLE), and optionally fails if the state
matches a disallowed value. It is intended to run via pre-commit/pre-push so
contributors know whether workflows are currently paused.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
FLAG_PATH = REPO_ROOT / ".github" / "run-github-actions.flag"

STATE_ALIASES: Dict[str, str] = {
    "enable": "enable",
    "enabled": "enable",
    "true": "enable",
    "on": "enable",
    "1": "enable",
    "disable": "disable",
    "disabled": "disable",
    "false": "disable",
    "off": "disable",
    "0": "disable",
}


def normalize(value: str | None) -> str:
    if not value:
        raise ValueError("Flag file is empty; set to 'enable' or 'disable'.")
    normalized = STATE_ALIASES.get(value.strip().lower())
    if not normalized:
        raise ValueError(
            "Unsupported flag value %r. Use enable/disable (or on/off, true/false)." % value
        )
    return normalized


def run() -> int:
    parser = argparse.ArgumentParser(description="Report GitHub Actions toggle state.")
    parser.add_argument(
        "--fail-when",
        choices=("enable", "disable"),
        default=None,
        help="Exit non-zero when the flag matches this state.",
    )
    args = parser.parse_args()

    if not FLAG_PATH.exists():
        print(
            "[actions-flag] Flag file missing at %s. Create it to control workflows." % FLAG_PATH,
            file=sys.stderr,
        )
        return 1

    value = FLAG_PATH.read_text(encoding="utf-8").strip()
    try:
        state = normalize(value)
    except ValueError as exc:  # pragma: no cover - user facing message
        print(f"[actions-flag] {exc}", file=sys.stderr)
        return 1

    print(f"[actions-flag] GitHub Actions are currently **{state.upper()}**.")

    if state == "disable":
        print(
            "[actions-flag] Toggle workflow: gh workflow run 'Toggle GitHub Actions' --field desired_state=enable",
            file=sys.stderr,
        )
    else:
        print(
            "[actions-flag] To pause automation: echo disable > .github/run-github-actions.flag && git commit",
            file=sys.stderr,
        )

    if args.fail_when and state == args.fail_when:
        print(
            f"[actions-flag] State '{state}' is not allowed for this stage (fail-when={args.fail_when}).",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(run())
