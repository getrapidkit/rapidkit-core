#!/usr/bin/env python3
"""Generate release notes by diffing two modules.lock files.

Usage:
  python scripts/generate_release_notes.py --prev path/to/old/modules.lock --curr modules.lock

Outputs markdown summary to stdout.
If --output provided, writes there.
"""
import argparse
import json
import pathlib
import sys
from typing import Dict


def load_lock(path: str) -> Dict[str, str]:
    p = pathlib.Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", required=True, help="Previous modules.lock path")
    ap.add_argument("--curr", required=True, help="Current modules.lock path")
    ap.add_argument("--output", help="Write markdown to file")
    args = ap.parse_args()
    prev = load_lock(args.prev)
    curr = load_lock(args.curr)
    added = sorted(set(curr) - set(prev))
    removed = sorted(set(prev) - set(curr))
    changed = sorted([m for m in curr if m in prev and curr[m] != prev[m]])
    if not (added or removed or changed):
        md = "## Release Notes\n\nNo module version changes.\n"
    else:
        lines = ["## Release Notes", ""]
        if added:
            lines.append("### Added Modules")
            for m in added:
                lines.append(f"- {m} v{curr[m]}")
            lines.append("")
        if removed:
            lines.append("### Removed Modules")
            for m in removed:
                lines.append(f"- {m} (was v{prev[m]})")
            lines.append("")
        if changed:
            lines.append("### Updated Modules")
            for m in changed:
                lines.append(f"- {m}: {prev[m]} -> {curr[m]}")
            lines.append("")
        md = "\n".join(lines)
    if args.output:
        pathlib.Path(args.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)


if __name__ == "__main__":
    main()
