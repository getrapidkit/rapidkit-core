#!/usr/bin/env python3
"""Scaffold a RapidKit module using the shared ModuleScaffolder."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

module_structure_cli = importlib.import_module("cli.utils.module_structure_cli")
DEFAULT_MODULES_ROOT = module_structure_cli.DEFAULT_MODULES_ROOT
scaffold_module = module_structure_cli.scaffold_module
scaffold_result_to_dict = module_structure_cli.scaffold_result_to_dict
scaffold_summary_lines = module_structure_cli.scaffold_summary_lines


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Module name (snake-case)")
    parser.add_argument(
        "--category",
        "-c",
        default="core",
        help="Module category path under the tier (default: core)",
    )
    parser.add_argument(
        "--tier",
        "-t",
        default="free",
        help="Module tier (free, pro, enterprise, ...). Default: free",
    )
    parser.add_argument(
        "--description",
        "-d",
        default=None,
        help="Optional description used in README and metadata",
    )
    parser.add_argument(
        "--blueprint",
        default=None,
        help="Optional scaffold blueprint name (when available)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files when the module already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated files without writing to disk",
    )
    parser.add_argument(
        "--modules-root",
        type=Path,
        default=DEFAULT_MODULES_ROOT,
        help="Root directory where modules live (default: src/modules)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human readable output",
    )

    args = parser.parse_args(argv)

    try:
        result = scaffold_module(
            tier=args.tier,
            category=args.category,
            module_name=args.name,
            description=args.description,
            blueprint=args.blueprint,
            force=args.force,
            dry_run=args.dry_run,
            modules_root=args.modules_root,
        )
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1

    if args.json:
        print(json.dumps(scaffold_result_to_dict(result, args.dry_run), indent=2))
        return 0

    for line in scaffold_summary_lines(result, args.dry_run):
        print(line)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
