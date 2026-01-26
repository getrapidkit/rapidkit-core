#!/usr/bin/env python3
"""Audit RapidKit modules for FastAPI/NestJS parity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cli.utils.module_validation import (  # noqa: E402 - imported after sys.path tweak
    collect_parity_failures,
    collect_parity_reports,
    parity_reports_to_dict,
    render_parity_table,
)

MODULES_ROOT = ROOT / "src" / "modules"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--modules",
        nargs="*",
        help="Optional module slugs to audit (e.g. free/essentials/settings).",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    args = parser.parse_args()

    reports = collect_parity_reports(MODULES_ROOT, args.modules)
    if args.json:
        print(json.dumps(parity_reports_to_dict(reports), indent=2, sort_keys=True))
    else:
        print(render_parity_table(reports))

    failures = collect_parity_failures(reports)
    if failures:
        print("\nModules requiring attention:")
        for report in failures:
            print(f"- {report.slug}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
