"""Tests for module validator utilities."""

from __future__ import annotations

from pathlib import Path

from core.services.module_validator import (
    ModuleRichSpec,
    load_all_specs,
    load_rich_spec,
    validate_spec,
)

SIMPLE_FEATURE_COUNT = 2
SIMPLE_DEPENDENCY_COUNT = 2
MAPPING_DEPENDENCY_COUNT = 3


def _write_yaml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_module_rich_spec_properties() -> None:
    spec = ModuleRichSpec(
        name="reporting",
        display_name="Reporting Suite",
        features={"dashboards": {}, "exports": {}},
        depends_on=["auth", "analytics"],
    )

    assert spec.effective_name == "Reporting Suite"
    assert spec.feature_count == SIMPLE_FEATURE_COUNT
    assert spec.dependency_count == SIMPLE_DEPENDENCY_COUNT


def test_module_rich_spec_dependency_mapping() -> None:
    spec = ModuleRichSpec(
        name="reporting",
        profiles=["standard", "enterprise"],
        depends_on={
            "standard": ["auth", {"notifications": []}],
            "enterprise": ["auth", "analytics"],
        },
    )

    assert spec.dependency_count == MAPPING_DEPENDENCY_COUNT


def test_load_rich_spec_reads_yaml(tmp_path: Path) -> None:
    spec_path = tmp_path / "module.yaml"
    _write_yaml(
        spec_path,
        """
name: reporting
version: 2.0.0
features:
  dashboards: {}
profiles:
  - standard
""".strip(),
    )

    spec = load_rich_spec(spec_path)

    assert spec.name == "reporting"
    assert spec.version == "2.0.0"
    assert spec.feature_count == 1


def test_load_all_specs_skips_invalid(tmp_path: Path) -> None:
    modules_root = tmp_path / "modules"
    (modules_root / "valid").mkdir(parents=True)
    _write_yaml(modules_root / "valid/module.yaml", "name: valid\n")

    (modules_root / "invalid").mkdir(parents=True)
    _write_yaml(
        modules_root / "invalid/module.yaml",
        """
name: invalid
profiles: invalid
""".strip(),
    )

    specs = load_all_specs(modules_root)

    assert set(specs) == {"valid"}
    assert isinstance(specs["valid"], ModuleRichSpec)


def test_validate_spec_reports_missing_profiles(tmp_path: Path) -> None:
    spec_path = tmp_path / "module.yaml"
    _write_yaml(
        spec_path,
        """
name: reporting
profiles:
  - standard
profile_inherits:
  enterprise: standard
""".strip(),
    )

    errors = validate_spec(spec_path)

    assert "child 'enterprise'" in errors[0]
    assert "parent 'standard'" not in errors[0]


def test_validate_spec_detects_cycle(tmp_path: Path) -> None:
    spec_path = tmp_path / "module.yaml"
    _write_yaml(
        spec_path,
        """
name: reporting
profiles:
  - standard
  - enterprise
profile_inherits:
  standard: enterprise
  enterprise: standard
""".strip(),
    )

    errors = validate_spec(spec_path)

    assert any("cycle detected" in error for error in errors)


def test_validate_spec_happy_path(tmp_path: Path) -> None:
    spec_path = tmp_path / "module.yaml"
    _write_yaml(
        spec_path,
        """
name: reporting
profiles:
  - standard
  - enterprise
profile_inherits:
  enterprise: standard
""".strip(),
    )

    errors = validate_spec(spec_path)

    assert errors == []
