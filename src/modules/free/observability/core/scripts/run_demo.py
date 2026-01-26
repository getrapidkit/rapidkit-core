#!/usr/bin/env python3
"""Generate a small demo project for Observability Core.

This script is intended for module developers to quickly smoke-check generator outputs.

Usage:
  python scripts/run_demo.py fastapi
  python scripts/run_demo.py nestjs
  python scripts/run_demo.py fastapi ./tmp/core-fastapi
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _find_project_root(start: Path) -> Path:
    for parent in (start, *start.parents):
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    return start


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("variant", choices=("fastapi", "nestjs"), help="Target kit")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="Target output directory (default: ./tmp/core-<variant>)",
    )
    args = parser.parse_args(argv)

    script_path = Path(__file__).resolve()
    module_root = script_path.parents[1]
    project_root = _find_project_root(module_root)
    modules_root = project_root / "src" / "modules"

    try:
        rel_slug = module_root.relative_to(modules_root).as_posix()
    except ValueError:
        raise SystemExit("Unable to resolve module slug for %s" % module_root) from None

    module_import = "modules." + rel_slug.replace("/", ".")

    default_out = project_root / "tmp" / ("core-" + args.variant)
    out_dir = Path(args.output_dir).resolve() if args.output_dir else default_out

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(project_root / "src"))

    cmd = [sys.executable, "-m", module_import + ".generate", args.variant, str(out_dir)]
    subprocess.run(cmd, check=True, cwd=project_root, env=env)  # nosec
    print("✅ Generated demo at: %s" % out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
