#!/usr/bin/env python3
"""Run tier-specific pytest suites using the tests/tests_map.yml configuration.

This helper lets developers mirror CI distribution coverage locally before pushing.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

try:
    import yaml
except ImportError as exc:  # pragma: no cover - this script expected to run in dev envs
    raise SystemExit("PyYAML is required to run distribution tests") from exc


def _prepare_mapping(data: Dict[str, Any]) -> Dict[str, List[str]]:
    raw_map = data.get("tests_map", {})
    if not isinstance(raw_map, dict):
        raise SystemExit("tests_map.yml malformed: 'tests_map' must be a mapping")

    mapping: Dict[str, List[str]] = {}
    for pattern, tiers in raw_map.items():
        if not isinstance(pattern, str):
            raise SystemExit("tests_map.yml malformed: pattern keys must be strings")
        if not isinstance(tiers, list) or not all(isinstance(tier, str) for tier in tiers):
            raise SystemExit(
                f"tests_map.yml malformed: tiers for '{pattern}' must be a list of strings"
            )
        mapping[pattern] = list(tiers)
    return mapping


def load_tests_for_tier(tests_map_path: Path, tier: str) -> list[Path]:
    raw_data = yaml.safe_load(tests_map_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw_data, dict):
        raise SystemExit("tests_map.yml malformed: expected mapping at top-level")

    mapping = _prepare_mapping(raw_data)
    tests_root = tests_map_path.parent
    collected: Set[Path] = set()

    # Collect every python test file in repo (files starting with test_)
    known_tests = {path for path in tests_root.rglob("test_*.py") if path.is_file()}
    # also include legacy top-level tests directly under tests_root starting with test_
    known_tests.update({p for p in tests_root.glob("test_*.py") if p.is_file()})

    tier_patterns = [pattern for pattern, tiers in mapping.items() if tier in tiers]
    if not tier_patterns:
        return []

    for test_path in known_tests:
        rel_str = str(Path("tests") / test_path.relative_to(tests_root))
        if any(fnmatch.fnmatch(rel_str, pattern) for pattern in tier_patterns):
            collected.add(test_path)

    return sorted(collected)


def build_pytest_command(
    tests: Iterable[Path],
    *,
    tier: str,
    cov: bool,
    cov_xml_path: Path | None,
    cov_fail_under: int | None,
    extra_args: list[str],
) -> list[str]:
    cmd = [sys.executable, "-m", "pytest"]
    if cov:
        xml_path = cov_xml_path if cov_xml_path is not None else Path(f"coverage-{tier}.xml")
        cmd.extend(
            [
                "--cov=src",
                "--cov-report=term",
                f"--cov-report=xml:{xml_path}",
            ]
        )
        if cov_fail_under is not None:
            cmd.append(f"--cov-fail-under={cov_fail_under}")
    cmd.extend(extra_args)
    cmd.extend(str(path) for path in tests)
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest for a specific distribution tier")
    parser.add_argument("--tier", default="community", help="Distribution tier to execute")
    parser.add_argument(
        "--tests-map",
        default=Path("tests/tests_map.yml"),
        type=Path,
        help="Path to tests_map.yml",
    )
    parser.add_argument(
        "--cov",
        dest="cov",
        action="store_true",
        help="Enable coverage reporting (default)",
    )
    parser.add_argument(
        "--no-cov",
        dest="cov",
        action="store_false",
        help="Disable coverage reporting",
    )
    parser.set_defaults(cov=True)
    parser.add_argument(
        "--cov-fail-under",
        type=int,
        default=None,
        help="Fail if coverage percentage is below this value",
    )
    parser.add_argument(
        "--cov-xml-path",
        type=Path,
        default=None,
        help="Custom output path for coverage XML (default: coverage-<tier>.xml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected tests without running pytest",
    )
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Additional arguments passed through to pytest",
    )

    args = parser.parse_args()

    tests_map_path = args.tests_map if args.tests_map.is_absolute() else Path.cwd() / args.tests_map
    if not tests_map_path.exists():
        raise SystemExit(f"tests map not found: {tests_map_path}")

    tests = load_tests_for_tier(tests_map_path, args.tier)
    if not tests:
        raise SystemExit(f"No tests mapped to tier '{args.tier}'")

    if args.dry_run:
        for test in tests:
            print(test)
        print(f"Total tests for tier '{args.tier}': {len(tests)}")
        return 0

    cov_fail_under = args.cov_fail_under
    if cov_fail_under is None and args.cov and args.tier == "community":
        cov_fail_under = 60

    cmd = build_pytest_command(
        tests,
        tier=args.tier,
        cov=args.cov,
        cov_xml_path=args.cov_xml_path,
        cov_fail_under=cov_fail_under,
        extra_args=args.pytest_args,
    )

    print("Running:", " ".join(cmd))
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    result = subprocess.run(cmd, env=env, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
