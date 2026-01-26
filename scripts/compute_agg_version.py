#!/usr/bin/env python3
"""Compute aggregate version from modules.lock and write to GITHUB_OUTPUT.

Writes a line like: agg_version=1.2.3 to the file pointed by GITHUB_OUTPUT.
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, cast


def parse(v: str) -> Tuple[int, int, int]:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v)
    if not m:
        return (0, 0, 0)
    return cast(Tuple[int, int, int], tuple(int(x) for x in m.groups()))


def load_modules_lock(path: Path) -> Dict[str, Any]:
    """Load JSON data from modules.lock safely."""
    try:
        raw = path.read_text(encoding="utf-8") or "{}"
        return cast(Dict[str, Any], json.loads(raw))
    except (OSError, json.JSONDecodeError) as err:
        print(f"⚠️ Warning: cannot read or parse {path}: {err}")
        return {}


def read_pyproject_version(pyproject: Path) -> Optional[str]:
    if not pyproject.exists():
        return None
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError as err:
        print(f"⚠️ Warning: cannot read {pyproject}: {err}")
        return None
    match = re.search(r"^version\s*=\s*['\"]([^'\"]+)['\"]", text, re.MULTILINE)
    if not match:
        return None
    return match.group(1)


def main() -> None:
    path = Path("modules.lock")
    data = load_modules_lock(path)

    highest: Tuple[int, int, int] = (0, 0, 0)
    for v in data.values():
        try:
            p = parse(str(v))
        except ValueError as err:  # unlikely, safe fallback
            print(f"⚠️ Warning: cannot parse version '{v}': {err}")
            p = (0, 0, 0)
        highest = max(highest, p)

    if highest == (0, 0, 0):
        fallback = read_pyproject_version(Path("pyproject.toml"))
        if fallback:
            highest = parse(fallback)

    agg = f"{highest[0]}.{highest[1]}.{highest[2]}"
    # Write to GITHUB_OUTPUT if available, otherwise print to stdout
    out = os.environ.get("GITHUB_OUTPUT")
    line = f"agg_version={agg}\n"
    if out:
        try:
            with open(out, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError as err:
            print(f"⚠️ Warning: cannot write to GITHUB_OUTPUT '{out}': {err}")
            sys.stdout.write(line)
    else:
        sys.stdout.write(line)


if __name__ == "__main__":
    main()
