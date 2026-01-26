"""Aggregated module validation helpers for structure and parity checks."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

import yaml

DEFAULT_VERIFICATION_FILENAME = "module.verify.json"


def _is_draft_status(status: str) -> bool:
    return status.strip().lower() == "draft"


@dataclass
class VariantReport:
    """Describe validation status for a single framework variant."""

    name: str
    declared: bool
    plugin: bool
    has_health: bool
    has_config: bool
    has_metadata: bool
    has_tests: bool
    notes: List[str] = field(default_factory=list)

    def is_compliant(self) -> bool:
        return (
            self.declared and self.plugin and self.has_health and self.has_config and self.has_tests
        )

    def as_dict(self) -> Mapping[str, object]:
        payload: MutableMapping[str, object] = {
            "declared": self.declared,
            "plugin": self.plugin,
            "has_health": self.has_health,
            "has_config": self.has_config,
            "has_metadata": self.has_metadata,
            "has_tests": self.has_tests,
        }
        if self.notes:
            payload["notes"] = list(self.notes)
        return payload


@dataclass
class ModuleReport:
    """Summarise validation status for a module across variants."""

    slug: str
    tier: str
    category: str
    status: str
    path: Path
    vendor_snapshot: bool
    variants: MutableMapping[str, VariantReport] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def is_compliant(self) -> bool:
        if not self.vendor_snapshot:
            return False

        normalized_status = self.status.strip().lower()
        # Draft modules are allowed to be incomplete (missing health/config/tests) while
        # work is in progress. We still require a vendor snapshot to exist so the module
        # can be generated and reviewed consistently.
        if normalized_status == "draft":
            return True

        return all(variant.is_compliant() for variant in self.variants.values())

    def as_dict(self) -> Mapping[str, object]:
        return {
            "slug": self.slug,
            "tier": self.tier,
            "category": self.category,
            "status": self.status,
            "path": str(self.path),
            "vendor_snapshot": self.vendor_snapshot,
            "variants": {name: variant.as_dict() for name, variant in self.variants.items()},
            "notes": list(self.notes),
        }


def _variant_issues(variant: VariantReport) -> List[str]:
    issues: List[str] = []
    if not variant.declared:
        issues.append("missing-config")
    if not variant.plugin:
        issues.append("no-plugin")
    if not variant.has_health:
        issues.append("no-health")
    if not variant.has_config:
        issues.append("no-config")
    if not variant.has_tests:
        issues.append("no-tests")
    return issues


def _variant_snapshot(variant: VariantReport, *, skip_checks: bool = False) -> Dict[str, object]:
    issues = [] if skip_checks else _variant_issues(variant)
    snapshot: Dict[str, object] = {
        "status": "skipped" if skip_checks else ("ok" if not issues else "action_required"),
        "issues": issues,
        "declared": variant.declared,
        "plugin": variant.plugin,
        "has_health": variant.has_health,
        "has_config": variant.has_config,
        "has_metadata": variant.has_metadata,
        "has_tests": variant.has_tests,
    }
    if variant.notes:
        snapshot["notes"] = list(variant.notes)
    return snapshot


def _load_yaml(path: Path) -> MutableMapping[str, object]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError(f"Expected mapping in {path}")
    return dict(data)


def _module_slug(modules_root: Path, module_dir: Path) -> str:
    return module_dir.resolve().relative_to(modules_root.resolve()).as_posix()


def _detect_outputs(files_cfg: Iterable[Mapping[str, object]]) -> List[str]:
    outputs: List[str] = []
    for entry in files_cfg:
        output = entry.get("output") or entry.get("relative")
        if isinstance(output, str):
            outputs.append(output)
    return outputs


def _audit_variant(
    module_root: Path,
    variants_cfg: Mapping[str, object],
    name: str,
    vendor_outputs: Optional[Iterable[str]] = None,
    config_sources: Optional[Iterable[str]] = None,
    declared_tests: Optional[Iterable[str]] = None,
) -> VariantReport:
    declared = name in variants_cfg
    plugin_path = module_root / "frameworks" / f"{name}.py"
    plugin_available = plugin_path.exists()

    outputs: List[str] = []
    notes: List[str] = []

    if declared:
        variant_cfg_raw = variants_cfg.get(name)
        if isinstance(variant_cfg_raw, Mapping):
            files_cfg = variant_cfg_raw.get("files", [])
            if isinstance(files_cfg, list):
                outputs = _detect_outputs(
                    entry for entry in files_cfg if isinstance(entry, Mapping)
                )
            else:
                notes.append("files list missing or malformed")
        else:
            notes.append("variant config not a mapping")
    else:
        notes.append("variant not declared in module.yaml")

    combined_outputs = list(outputs)
    if vendor_outputs:
        combined_outputs.extend(o for o in vendor_outputs if isinstance(o, str))

    config_candidates = list(combined_outputs)
    if config_sources:
        config_candidates.extend(p for p in config_sources if isinstance(p, str))

    test_candidates = list(combined_outputs)
    if declared_tests:
        test_candidates.extend(p for p in declared_tests if isinstance(p, str))

    has_health = any("health" in output for output in combined_outputs)
    has_config = any(
        any(token in output for token in ("config", "settings", "configuration"))
        for output in config_candidates
    )
    metadata_tokens = ("metadata", "router", "routes", "controller", "module", "service")
    has_metadata = any(any(token in output for token in metadata_tokens) for output in outputs)
    has_tests = any(output.startswith("tests/") or "test" in output for output in test_candidates)

    return VariantReport(
        name=name,
        declared=declared,
        plugin=plugin_available,
        has_health=has_health,
        has_config=has_config,
        has_metadata=has_metadata,
        has_tests=has_tests,
        notes=notes,
    )


def collect_parity_reports(
    modules_root: Path, modules: Optional[Sequence[str]] = None
) -> List[ModuleReport]:
    modules_root = modules_root.resolve()
    modules_filter = {slug.lower() for slug in modules} if modules else None
    reports: List[ModuleReport] = []

    for module_yaml in sorted(modules_root.glob("**/module.yaml")):
        module_dir = module_yaml.parent.resolve()
        slug = _module_slug(modules_root, module_dir)

        args = _load_yaml(module_yaml)
        status = str(args.get("status") or "unknown")
        generation_cfg = args.get("generation")
        if not isinstance(generation_cfg, Mapping):
            generation_cfg = {}
        vendor_snapshot = bool(generation_cfg.get("vendor"))
        variants_cfg = generation_cfg.get("variants", {})
        if not isinstance(variants_cfg, Mapping):
            variants_cfg = {}

        config_sources = args.get("config_sources", [])
        if not isinstance(config_sources, list):
            config_sources = []

        testing_cfg = args.get("testing")
        declared_tests: list[str] = []
        if isinstance(testing_cfg, Mapping):
            unit_tests = testing_cfg.get("unit_tests", [])
            if isinstance(unit_tests, list):
                declared_tests = [t for t in unit_tests if isinstance(t, str)]

        tier, category = _extract_tier_and_category(slug)

        # If this is a paid-tier module skip it unless the caller explicitly
        # requested specific slugs to vet. Also skip any modules that don't
        # match a provided modules filter.
        if tier.lower() == "paid" and not (
            isinstance(modules_filter, set) and slug.lower() in modules_filter
        ):
            continue

        if modules_filter is not None and slug.lower() not in modules_filter:
            continue

        # Collect vendor-level outputs (if present) so variant audits consider
        # vendor-provided files when evaluating parity (health/config/tests).
        vendor_cfg = (
            generation_cfg.get("vendor")
            if isinstance(generation_cfg.get("vendor"), Mapping)
            else {}
        )
        vendor_files = vendor_cfg.get("files", []) if isinstance(vendor_cfg, Mapping) else []
        vendor_outputs = _detect_outputs(
            entry for entry in vendor_files if isinstance(entry, Mapping)
        )

        report = ModuleReport(
            slug=slug,
            tier=tier,
            category=category,
            status=status,
            path=module_dir,
            vendor_snapshot=vendor_snapshot,
        )

        for variant_name in ("fastapi", "nestjs"):
            report.variants[variant_name] = _audit_variant(
                module_dir,
                variants_cfg,
                variant_name,
                vendor_outputs=vendor_outputs,
                config_sources=config_sources,
                declared_tests=declared_tests,
            )

        if not vendor_snapshot:
            report.notes.append("vendor snapshot missing")
        for variant_name, variant in report.variants.items():
            if not variant.plugin:
                report.notes.append(f"{variant_name} plugin file missing")
            report.notes.extend(f"{variant_name}: {note}" for note in variant.notes)

        reports.append(report)

    return sorted(reports, key=lambda r: r.slug)


def _extract_tier_and_category(slug: str) -> tuple[str, str]:
    parts = slug.split("/")
    tier = parts[0] if len(parts) > 0 else "unknown"
    category = parts[1] if len(parts) > 1 else "unknown"
    return tier, category


def _summarise_variant(variant: VariantReport) -> str:
    issues = _variant_issues(variant)
    if not issues:
        return "ok"
    return ",".join(issues)


def render_parity_table(reports: Iterable[ModuleReport]) -> str:
    headers = ("Module", "Category", "Status", "Vendor", "FastAPI", "NestJS", "Notes")
    body_rows: List[List[str]] = []

    for report in reports:
        if _is_draft_status(report.status):
            fastapi_summary = "skipped"
            nestjs_summary = "skipped"
        else:
            fastapi_summary = _summarise_variant(
                report.variants.get(
                    "fastapi",
                    VariantReport(
                        name="fastapi",
                        declared=False,
                        plugin=False,
                        has_health=False,
                        has_config=False,
                        has_metadata=False,
                        has_tests=False,
                    ),
                )
            )
            nestjs_summary = _summarise_variant(
                report.variants.get(
                    "nestjs",
                    VariantReport(
                        name="nestjs",
                        declared=False,
                        plugin=False,
                        has_health=False,
                        has_config=False,
                        has_metadata=False,
                        has_tests=False,
                    ),
                )
            )
        note_text = "; ".join(report.notes)

        body_rows.append(
            [
                report.slug,
                report.category,
                report.status,
                "yes" if report.vendor_snapshot else "no",
                fastapi_summary,
                nestjs_summary,
                note_text,
            ]
        )

    widths = [len(header) for header in headers]
    for row in body_rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def border(char: str) -> str:
        segments = [char * (width + 2) for width in widths]
        return "+" + "+".join(segments) + "+"

    def make_row(cells: Iterable[str]) -> str:
        items = list(cells)
        padded: List[str] = []
        for idx, width in enumerate(widths):
            cell = items[idx] if idx < len(items) else ""
            padded.append(f" {cell.ljust(width)} ")
        return "|" + "|".join(padded) + "|"

    lines: List[str] = [border("-")]
    lines.append(make_row(headers))
    lines.append(border("="))
    for row in body_rows:
        lines.append(make_row(row))
    lines.append(border("-"))
    return "\n".join(lines)


def parity_reports_to_dict(reports: Iterable[ModuleReport]) -> List[Mapping[str, object]]:
    return [report.as_dict() for report in reports]


def collect_parity_failures(reports: Iterable[ModuleReport]) -> List[ModuleReport]:
    # Draft modules are allowed to be incomplete while under development.
    return [
        report
        for report in reports
        if not report.is_compliant() and not _is_draft_status(report.status)
    ]


def apply_parity_to_verification(
    report: ModuleReport, verification_filename: Optional[str] = None
) -> None:
    """Update module.verify manifest with parity results.

    Recomputes the aggregate ``valid`` flag so it only passes when both structure and parity
    checks succeed. The function is resilient to partially populated manifests produced by
    older validators; missing fields fall back to sensible defaults.
    """

    if os.getenv("RAPIDKIT_SKIP_VERIFICATION_WRITE"):
        return

    verification_name = verification_filename or DEFAULT_VERIFICATION_FILENAME
    manifest_path = report.path / verification_name
    if not manifest_path.exists():
        return

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    previous_parity_snapshot = (
        payload["parity"] if isinstance(payload.get("parity"), dict) else None
    )
    previous_parity_valid = bool(payload.get("parity_valid"))
    raw_previous_notes = payload.get("parity_notes")
    previous_notes = list(raw_previous_notes) if isinstance(raw_previous_notes, list) else []
    previous_timestamp = payload.get("parity_checked_at")
    if not isinstance(previous_timestamp, str):
        previous_timestamp = None

    skip_checks = _is_draft_status(report.status)
    parity_details = {
        name: _variant_snapshot(variant, skip_checks=skip_checks)
        for name, variant in report.variants.items()
    }
    parity_valid = report.is_compliant()
    new_notes = list(report.notes)

    payload["parity_valid"] = parity_valid
    payload["parity"] = parity_details
    if report.notes:
        payload["parity_notes"] = list(report.notes)
    else:
        payload.pop("parity_notes", None)

    parity_changed = previous_parity_snapshot != parity_details
    notes_changed = previous_notes != new_notes
    validity_changed = previous_parity_valid != parity_valid

    if parity_changed or notes_changed or validity_changed or previous_timestamp is None:
        payload["parity_checked_at"] = datetime.now(timezone.utc).isoformat()
    else:
        payload["parity_checked_at"] = previous_timestamp

    structure_valid = bool(payload.get("structure_valid"))
    structure_tree_hash = payload.get("structure_tree_hash") or payload.get("tree_hash")
    fully_valid = structure_valid and parity_valid
    payload["valid"] = fully_valid
    payload["tree_hash"] = structure_tree_hash if fully_valid else None

    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
