#!/usr/bin/env python
"""Generate modules.lock (module slug -> version) from src/modules/**/module.yaml."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
modules_dir = ROOT / "src" / "modules"
lock_path = ROOT / "modules.lock"


def main():
    if not modules_dir.exists():
        print("No modules directory", file=sys.stderr)
        return 1
    mapping: dict[str, str] = {}
    for manifest in sorted(modules_dir.rglob("module.yaml")):
        module_dir = manifest.parent
        try:
            slug = module_dir.relative_to(modules_dir).as_posix()
        except ValueError:
            continue
        try:
            data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                raise TypeError("manifest root must be a mapping")
            ver = data.get("version") or "0.0.0"
            mapping[slug] = str(ver)
        except (
            OSError,
            TypeError,
            yaml.YAMLError,
            json.JSONDecodeError,
            UnicodeDecodeError,
        ) as e:
            # Skip malformed module manifest but keep going (avoid silent swallow)
            print(f"Skipping {manifest}: {e}", file=sys.stderr)
    lock_path.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {lock_path} ({len(mapping)} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
