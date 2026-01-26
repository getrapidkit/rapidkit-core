#!/usr/bin/env python3
"""Validate per-module coverage against a configurable threshold."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import yaml

MODULE_SLUG_DEPTH = 3
DEFAULT_IGNORE_PATTERNS: tuple[str, ...] = (
    "*/generate.py",
    "*/overrides.py",
    "*/frameworks/__init__.py",
)


@dataclass
class ModuleInfo:
    slug: str
    tier: str = "free"
    coverage_min: Optional[float] = None
    coverage_ignore: tuple[str, ...] = ()


@dataclass
class ModuleCoverage:
    """Accumulate coverage metrics for a single module slug."""

    slug: str
    covered_lines: int = 0
    total_lines: int = 0
    files: List[Mapping[str, object]] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        if self.total_lines == 0:
            return 100.0
        return (self.covered_lines / self.total_lines) * 100.0

    def display_percentage(self) -> str:
        if self.total_lines == 0:
            return "n/a"
        return f"{self.percentage:.1f}%"

    def as_dict(self) -> Dict[str, object]:
        return {
            "module": self.slug,
            "covered_lines": self.covered_lines,
            "total_lines": self.total_lines,
            "coverage": round(self.percentage, 2),
            "files": list(self.files),
        }


def _relative_to_modules(filename: str, modules_root: Path) -> Optional[PurePosixPath]:
    """Return the path of *filename* relative to *modules_root* if possible."""

    normalised = filename.replace("\\", "/")
    modules_posix = modules_root.as_posix()

    if modules_posix in normalised:
        relative = normalised.split(modules_posix, 1)[1].lstrip("/")
        if relative:
            return PurePosixPath(relative)

    marker = "src/modules/"
    if normalised.startswith(marker):
        return PurePosixPath(normalised[len(marker) :])

    alt_marker = f"{modules_root.name}/"
    if normalised.startswith(alt_marker):
        return PurePosixPath(normalised[len(alt_marker) :])

    candidate = Path(normalised)
    if candidate.exists():
        try:
            resolved = candidate.resolve().relative_to(modules_root)
            return PurePosixPath(resolved.as_posix())
        except ValueError:
            return None

    return None


def _discover_module_slugs(modules_root: Path) -> List[str]:
    """Find all module slugs by locating module.yaml manifests."""

    slugs: List[str] = []
    for manifest in modules_root.glob("**/module.yaml"):
        try:
            relative = manifest.parent.relative_to(modules_root)
        except ValueError:
            continue
        slugs.append(relative.as_posix())
    return sorted(set(slugs))


def _load_module_infos(modules_root: Path) -> Dict[str, ModuleInfo]:
    infos: Dict[str, ModuleInfo] = {}
    for manifest in modules_root.glob("**/module.yaml"):
        try:
            relative = manifest.parent.relative_to(modules_root)
        except ValueError:
            continue

        slug = relative.as_posix()
        try:
            data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            data = {}

        tier = str(data.get("tier") or data.get("access") or "free")

        testing_section = data.get("testing") if isinstance(data, Mapping) else None
        coverage_min: Optional[float] = None
        coverage_ignore: Sequence[str] = ()
        if isinstance(testing_section, Mapping):
            raw_threshold = testing_section.get("coverage_min")
            if isinstance(raw_threshold, (int, float)):
                coverage_min = float(raw_threshold)
            raw_ignore = testing_section.get("coverage_ignore")
            if isinstance(raw_ignore, list):
                coverage_ignore = [str(item) for item in raw_ignore if isinstance(item, str)]

        infos[slug] = ModuleInfo(
            slug=slug,
            tier=tier,
            coverage_min=coverage_min,
            coverage_ignore=tuple(coverage_ignore),
        )

    return infos


def _collect_module_coverage(
    coverage_xml: Path,
    modules_root: Path,
    module_infos: Mapping[str, ModuleInfo],
) -> Dict[str, ModuleCoverage]:
    """Aggregate coverage data from a Cobertura XML report."""

    tree = ET.parse(coverage_xml)
    root = tree.getroot()

    modules: Dict[str, ModuleCoverage] = {}

    for class_elem in root.findall(".//class"):
        filename = class_elem.get("filename")
        if not filename:
            continue

        relative = _relative_to_modules(filename, modules_root)
        if relative is None:
            continue

        parts = relative.parts
        if len(parts) < MODULE_SLUG_DEPTH:
            continue
        slug = "/".join(parts[:MODULE_SLUG_DEPTH])

        info = module_infos.get(slug)

        ignore_patterns: Sequence[str] = DEFAULT_IGNORE_PATTERNS
        if info and info.coverage_ignore:
            ignore_patterns = tuple(dict.fromkeys(DEFAULT_IGNORE_PATTERNS + info.coverage_ignore))

        if any(fnmatch.fnmatch(relative.as_posix(), pattern) for pattern in ignore_patterns):
            continue

        module_cov = modules.setdefault(slug, ModuleCoverage(slug=slug))

        file_total = 0
        file_covered = 0
        for line_elem in class_elem.findall(".//line"):
            file_total += 1
            hits = int(line_elem.get("hits", "0"))
            if hits > 0:
                file_covered += 1

        module_cov.total_lines += file_total
        module_cov.covered_lines += file_covered
        module_cov.files.append(
            {
                "filename": relative.as_posix(),
                "covered_lines": file_covered,
                "total_lines": file_total,
                "coverage": round((file_covered / file_total * 100.0), 2) if file_total else 0.0,
            }
        )

    return modules


def _format_table(
    records: Iterable[ModuleCoverage],
    thresholds: Mapping[str, float],
) -> str:
    header = f"{'Module':<40} {'Lines':>10} {'Covered':>10} {'Coverage':>10}"
    separator = "-" * len(header)
    lines = [header, separator]

    for record in records:
        threshold = thresholds.get(record.slug, 0.0)
        status = "✅" if record.total_lines == 0 or record.percentage >= threshold else "❌"
        lines.append(
            f"{status} {record.slug:<40} {record.total_lines:>10} {record.covered_lines:>10} {record.display_percentage():>10}"
        )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check per-module coverage thresholds.")
    parser.add_argument(
        "--coverage-xml",
        type=Path,
        default=Path("coverage.xml"),
        help="Path to the Cobertura XML report generated by coverage.py",
    )
    parser.add_argument(
        "--modules-root",
        type=Path,
        default=Path("src/modules"),
        help="Root directory containing RapidKit modules",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=85.0,
        help="Minimum coverage percentage required per module (default: 85)",
    )
    parser.add_argument(
        "--tiers",
        nargs="*",
        default=["free"],
        help="Module tiers to include (default: free). Use 'all' to include every tier.",
    )
    parser.add_argument(
        "--modules",
        nargs="*",
        help="Optional subset of module slugs to validate (e.g. free/essentials/settings)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine readable JSON instead of a human-readable table",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    coverage_xml = args.coverage_xml
    modules_root = args.modules_root.resolve()
    threshold = args.threshold
    tiers = set(args.tiers or [])
    include_all_tiers = "all" in {tier.lower() for tier in tiers}

    if coverage_xml.suffix.lower() != ".xml":
        print(f"⚠️ Expected an XML coverage report, got: {coverage_xml}")
    if not coverage_xml.exists():
        print(
            f"❌ Coverage report not found at {coverage_xml}. Run pytest with --cov first.",
            file=sys.stderr,
        )
        return 2

    discovered_slugs = _discover_module_slugs(modules_root)
    module_infos = _load_module_infos(modules_root)

    if args.modules:
        requested = {slug.strip() for slug in args.modules}
        missing = requested - set(discovered_slugs)
        if missing:
            print(f"⚠️ Requested module(s) not found: {', '.join(sorted(missing))}")
        target_slugs = sorted(set(discovered_slugs) & requested)
    else:
        target_slugs = discovered_slugs

    if not include_all_tiers:
        tiers_lower = {tier.lower() for tier in (tiers or {"free"})}
        target_slugs = [
            slug
            for slug in target_slugs
            if module_infos.get(slug, ModuleInfo(slug=slug)).tier.lower() in tiers_lower
        ]

    coverage_by_module = _collect_module_coverage(coverage_xml, modules_root, module_infos)

    records: List[ModuleCoverage] = []
    thresholds: Dict[str, float] = {}
    for slug in target_slugs:
        record = coverage_by_module.get(slug, ModuleCoverage(slug=slug))
        records.append(record)
        info = module_infos.get(slug)
        if info and info.coverage_min is not None:
            thresholds[slug] = max(float(info.coverage_min), threshold)
        else:
            thresholds[slug] = threshold

    records.sort(
        key=lambda item: (item.percentage if item.total_lines else float("inf"), item.slug)
    )

    failing = [
        record
        for record in records
        if record.total_lines and record.percentage < thresholds.get(record.slug, threshold)
    ]

    if args.json:
        payload = {
            "threshold": threshold,
            "modules": [
                record.as_dict()
                | {
                    "status": "pass" if record not in failing else "fail",
                    "threshold": thresholds.get(record.slug, threshold),
                }
                for record in records
            ],
            "failing_modules": [record.slug for record in failing],
        }
        json.dump(payload, sys.stdout, indent=2)
        print()
    else:
        print(_format_table(records, thresholds))
        if failing:
            print("\nModules below threshold:")
            for record in failing:
                module_threshold = thresholds.get(record.slug, threshold)
                print(
                    f"  - {record.slug} ({record.display_percentage()}) — threshold {module_threshold:.1f}%"
                )
        else:
            print("\nAll modules meet the coverage threshold.")

    if failing:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
