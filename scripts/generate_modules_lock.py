#!/usr/bin/env python
"""Generate modules.lock (name -> version) by scanning src/modules/*/module.yaml"""
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
    mapping = {}
    for d in sorted(modules_dir.iterdir()):
        if not d.is_dir():
            continue
        manifest = d / "module.yaml"
        if manifest.exists():
            try:
                data = yaml.safe_load(manifest.read_text()) or {}
                name = data.get("name") or d.name
                ver = data.get("version") or "0.0.0"
                mapping[name] = ver
            except (
                OSError,
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
