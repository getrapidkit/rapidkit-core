import json
import time
from datetime import datetime, timezone

from cli.utils.module_validation import (
    DEFAULT_VERIFICATION_FILENAME,
    ModuleReport,
    VariantReport,
    apply_parity_to_verification,
)


def _bootstrap_manifest(tmp_path, *, structure_valid=True) -> ModuleReport:
    module_dir = tmp_path / "free" / "core" / "demo"
    module_dir.mkdir(parents=True)
    manifest_path = module_dir / DEFAULT_VERIFICATION_FILENAME
    manifest_payload = {
        "module": "free/essentials/demo",
        "spec_version": 3,
        "description": "demo",
        "missing_files": [],
        "missing_directories": [],
        "extra_files": [],
        "extra_directories": [],
        "structure_valid": structure_valid,
        "structure_tree_hash": "deadbeef" if structure_valid else None,
        "parity_valid": False,
        "valid": False,
        "tree_hash": None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    report = ModuleReport(
        slug="free/essentials/demo",
        tier="free",
        category="core",
        status="active",
        path=module_dir,
        vendor_snapshot=True,
    )
    return report


def test_apply_parity_to_verification_promotes_valid_snapshot(tmp_path) -> None:
    report = _bootstrap_manifest(tmp_path)
    report.variants["fastapi"] = VariantReport(
        name="fastapi",
        declared=True,
        plugin=True,
        has_health=True,
        has_config=True,
        has_metadata=True,
        has_tests=True,
    )
    report.variants["nestjs"] = VariantReport(
        name="nestjs",
        declared=True,
        plugin=True,
        has_health=True,
        has_config=True,
        has_metadata=True,
        has_tests=True,
    )

    apply_parity_to_verification(report)

    manifest_path = report.path / DEFAULT_VERIFICATION_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["parity_valid"] is True
    assert payload["valid"] is True
    assert payload["tree_hash"] == "deadbeef"
    assert payload["parity"]["fastapi"]["status"] == "ok"
    assert payload["parity"]["nestjs"]["status"] == "ok"
    assert "parity_checked_at" in payload


def test_apply_parity_to_verification_flags_failures(tmp_path) -> None:
    report = _bootstrap_manifest(tmp_path)
    report.vendor_snapshot = False
    report.notes.append("vendor snapshot missing")
    report.variants["fastapi"] = VariantReport(
        name="fastapi",
        declared=True,
        plugin=False,
        has_health=False,
        has_config=False,
        has_metadata=False,
        has_tests=False,
        notes=["variant config not a mapping"],
    )
    report.variants["nestjs"] = VariantReport(
        name="nestjs",
        declared=False,
        plugin=False,
        has_health=False,
        has_config=False,
        has_metadata=False,
        has_tests=False,
    )

    apply_parity_to_verification(report)

    manifest_path = report.path / DEFAULT_VERIFICATION_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["parity_valid"] is False
    assert payload["valid"] is False
    assert payload["tree_hash"] is None
    assert payload["parity"]["fastapi"]["status"] == "action_required"
    assert "no-plugin" in payload["parity"]["fastapi"]["issues"]
    assert payload.get("parity_notes") == ["vendor snapshot missing"]
    assert payload["structure_tree_hash"] == "deadbeef"


def test_apply_parity_preserves_timestamp_when_snapshot_unchanged(tmp_path) -> None:
    report = _bootstrap_manifest(tmp_path)
    report.variants["fastapi"] = VariantReport(
        name="fastapi",
        declared=True,
        plugin=True,
        has_health=True,
        has_config=True,
        has_metadata=True,
        has_tests=True,
    )
    report.variants["nestjs"] = VariantReport(
        name="nestjs",
        declared=True,
        plugin=True,
        has_health=True,
        has_config=True,
        has_metadata=True,
        has_tests=True,
    )

    apply_parity_to_verification(report)
    manifest_path = report.path / DEFAULT_VERIFICATION_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    first_timestamp = payload["parity_checked_at"]

    time.sleep(0.01)
    apply_parity_to_verification(report)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["parity_checked_at"] == first_timestamp


def test_apply_parity_skips_when_env_flag_set(monkeypatch, tmp_path) -> None:
    report = _bootstrap_manifest(tmp_path)
    report.variants["fastapi"] = VariantReport(
        name="fastapi",
        declared=True,
        plugin=True,
        has_health=True,
        has_config=True,
        has_metadata=True,
        has_tests=True,
    )
    report.variants["nestjs"] = VariantReport(
        name="nestjs",
        declared=True,
        plugin=True,
        has_health=True,
        has_config=True,
        has_metadata=True,
        has_tests=True,
    )

    manifest_path = report.path / DEFAULT_VERIFICATION_FILENAME
    before = manifest_path.read_text(encoding="utf-8")
    monkeypatch.setenv("RAPIDKIT_SKIP_VERIFICATION_WRITE", "1")

    apply_parity_to_verification(report)

    after = manifest_path.read_text(encoding="utf-8")
    assert after == before
