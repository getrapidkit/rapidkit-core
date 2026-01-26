import pathlib
from typing import Any, Dict, List

import pytest

from cli.utils import module_structure_cli
from core.services.module_structure_validator import ModuleStructureError, ValidationResult


def make_validation_result(
    module: str, *, valid: bool, messages: List[str] | None = None
) -> ValidationResult:
    return ValidationResult(
        module=module,
        module_path=module_structure_cli.REPO_ROOT / "src" / module,
        valid=valid,
        spec_version=1,
        missing_files=[],
        missing_directories=[],
        extra_files=[],
        extra_directories=[],
        verification_file=None,
        tree_hash=None,
        messages=messages or [],
    )


def test_scaffold_module_delegates_to_scaffolder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    captured: Dict[str, Any] = {}

    class DummyScaffolder:
        def __init__(self, modules_root: pathlib.Path) -> None:
            captured["modules_root"] = modules_root

        def create_module(self, **kwargs: Any) -> str:
            captured["kwargs"] = kwargs
            return "sentinel"

    monkeypatch.setattr(module_structure_cli, "ModuleScaffolder", DummyScaffolder)

    result = module_structure_cli.scaffold_module(
        tier="free",
        category="essentials",
        module_name="example",
        description="demo",
        blueprint="default",
        force=True,
        dry_run=False,
        modules_root=tmp_path,
    )

    assert result == "sentinel"
    assert captured["kwargs"] == {
        "tier": "free",
        "category": "essentials",
        "module_name": "example",
        "description": "demo",
        "blueprint": "default",
        "force": True,
        "dry_run": False,
    }


def test_scaffold_result_to_dict_formats_relative_paths() -> None:
    module_path = (
        module_structure_cli.REPO_ROOT / "src" / "modules" / "free" / "essentials" / "demo"
    )
    result = module_structure_cli.ModuleScaffoldResult(
        module_path=module_path,
        created_files=[module_path / "file.txt"],
        skipped_files=[pathlib.Path("/tmp/outside.txt")],
        overwritten_files=[module_structure_cli.REPO_ROOT / "README.md"],
        context={"tier": "free"},
    )

    payload = module_structure_cli.scaffold_result_to_dict(result, dry_run=True)

    assert payload["module_path"] == "src/modules/free/essentials/demo"
    assert payload["created_files"] == ["src/modules/free/essentials/demo/file.txt"]
    assert payload["skipped_files"] == [pathlib.Path("/tmp/outside.txt").as_posix()]
    assert payload["dry_run"] is True


def test_scaffold_summary_lines_for_dry_run() -> None:
    module_path = (
        module_structure_cli.REPO_ROOT / "src" / "modules" / "free" / "essentials" / "demo"
    )
    result = module_structure_cli.ModuleScaffoldResult(
        module_path=module_path,
        created_files=[module_path / "__init__.py", module_path / "__init__.py"],
        skipped_files=[],
        overwritten_files=[],
        context={"tier": "free", "category_path": "essentials", "module_name": "demo"},
    )

    lines = module_structure_cli.scaffold_summary_lines(result, dry_run=True)

    assert lines[0] == "Dry run — planned scaffold (no files written):"
    assert "Would create (1):" in lines
    assert "Would skip" not in lines


def test_scaffold_summary_lines_for_real_run() -> None:
    module_path = (
        module_structure_cli.REPO_ROOT / "src" / "modules" / "free" / "essentials" / "demo"
    )
    result = module_structure_cli.ModuleScaffoldResult(
        module_path=module_path,
        created_files=[],
        skipped_files=[],
        overwritten_files=[module_path / "module.yaml"],
        context={
            "tier": "free",
            "category_path": "essentials",
            "module_name": "demo",
            "module_import_path": "modules.free.essentials.demo",
        },
    )

    lines = module_structure_cli.scaffold_summary_lines(result, dry_run=False)

    assert "Next steps:" in lines
    assert any("Validate structure" in line for line in lines)
    assert any("module.yaml" in line for line in lines)


def test_format_paths_deduplicates_and_labels() -> None:
    base = module_structure_cli.REPO_ROOT / "src" / "modules" / "free" / "essentials" / "demo"
    items = [base / "a.txt", base / "a.txt"]

    lines = module_structure_cli._format_paths("Created", items)

    assert lines == ["Created (1):", f"  - {module_structure_cli._relative(base / 'a.txt')}"]
    assert module_structure_cli._format_paths("Skipped", []) == []


def test_ensure_structure_spec_ready_invokes_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    called: Dict[str, bool] = {"value": False}

    def fake_loader() -> None:
        called["value"] = True

    monkeypatch.setattr(module_structure_cli, "load_structure_spec", fake_loader)

    module_structure_cli.ensure_structure_spec_ready()

    assert called["value"] is True


def test_collect_validation_results_delegates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    captured: Dict[str, Any] = {}

    def fake_validate(targets: List[str] | None, *, modules_root: pathlib.Path) -> List[str]:
        captured["targets"] = targets
        captured["modules_root"] = modules_root
        return ["ok"]

    monkeypatch.setattr(module_structure_cli, "validate_modules", fake_validate)

    result_specific = module_structure_cli.collect_validation_results(
        ["free/essentials/demo"], modules_root=tmp_path
    )
    result_all = module_structure_cli.collect_validation_results(None, modules_root=tmp_path)

    assert result_specific == ["ok"]
    assert result_all == ["ok"]
    assert captured["targets"] is None
    assert captured["modules_root"] == tmp_path


def test_validation_summary_lines_reports_all_messages() -> None:
    results = [
        make_validation_result("free/essentials/valid", valid=True, messages=["All good"]),
        make_validation_result("free/essentials/bad", valid=False, messages=["Missing file"]),
    ]

    exit_code, lines = module_structure_cli.validation_summary_lines(results, fail_fast=False)

    assert exit_code == 1
    assert "✔ free/essentials/valid matches spec v1" in lines
    assert any("Missing file" in line for line in lines)


def test_validation_summary_lines_honors_fail_fast() -> None:
    results = [
        make_validation_result("free/essentials/bad", valid=False, messages=["Broken"]),
        make_validation_result("free/essentials/other", valid=False, messages=["Also broken"]),
    ]

    exit_code, lines = module_structure_cli.validation_summary_lines(results, fail_fast=True)

    assert exit_code == 1
    assert len([line for line in lines if line.startswith("✖")]) == 1


def test_validation_results_to_dict_wraps_payload(tmp_path: pathlib.Path) -> None:
    results = [
        make_validation_result("free/essentials/valid", valid=True),
    ]

    payload = module_structure_cli.validation_results_to_dict(results, modules_root=tmp_path)

    assert payload["modules_root"] == tmp_path.as_posix()
    assert payload["results"][0]["module"] == "free/essentials/valid"
    assert payload["valid"] is True


def test_validation_result_to_dict_serializes_fields() -> None:
    result = make_validation_result("free/essentials/demo", valid=False, messages=["warn"])

    payload = module_structure_cli.validation_result_to_dict(result)

    assert payload["module"] == "free/essentials/demo"
    assert payload["messages"] == ["warn"]


def test_ensure_module_validation_returns_result_when_valid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    validation = make_validation_result("free/essentials/demo", valid=True)

    def fake_collect(modules: List[str], modules_root: pathlib.Path) -> List[ValidationResult]:
        assert modules == ["free/essentials/demo"]
        assert modules_root == tmp_path
        return [validation]

    monkeypatch.setattr(module_structure_cli, "collect_validation_results", fake_collect)
    called = False

    def fail_if_called(*_args: Any, **_kwargs: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(module_structure_cli, "ensure_module_structure", fail_if_called)

    result, error = module_structure_cli.ensure_module_validation(
        "free/essentials/demo", modules_root=tmp_path
    )

    assert result is validation
    assert error is None
    assert called is False


def test_ensure_module_validation_captures_structure_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    validation = make_validation_result("free/essentials/demo", valid=False)

    def fake_collect(modules: List[str], modules_root: pathlib.Path) -> List[ValidationResult]:

        assert modules == ["free/essentials/demo"]
        assert modules_root == tmp_path
        return [validation]

    monkeypatch.setattr(module_structure_cli, "collect_validation_results", fake_collect)

    expected_error = ModuleStructureError("boom")

    def raise_error(*_args: Any, **_kwargs: Any) -> None:
        raise expected_error

    monkeypatch.setattr(module_structure_cli, "ensure_module_structure", raise_error)

    result, error = module_structure_cli.ensure_module_validation(
        "free/essentials/demo", modules_root=tmp_path
    )

    assert result is validation
    assert error is expected_error


def test_ensure_module_validation_returns_result_after_fix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    validation = make_validation_result("free/essentials/demo", valid=False)

    def fake_collect(modules: List[str], modules_root: pathlib.Path) -> List[ValidationResult]:
        assert modules == ["free/essentials/demo"]
        assert modules_root == tmp_path
        return [validation]

    monkeypatch.setattr(module_structure_cli, "collect_validation_results", fake_collect)
    called = False

    def pretend_fix(*_args: Any, **_kwargs: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(module_structure_cli, "ensure_module_structure", pretend_fix)

    result, error = module_structure_cli.ensure_module_validation(
        "free/essentials/demo", modules_root=tmp_path
    )

    assert result is validation
    assert error is None
    assert called is True
