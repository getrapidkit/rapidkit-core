"""Shared helpers for module scaffolding and structure validation CLIs."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from core.services.module_structure_validator import (
    ModuleStructureError,
    ValidationResult,
    ensure_module_structure,
    load_structure_spec,
    validate_modules,
)

from .module_scaffold import ModuleScaffolder, ModuleScaffoldResult

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODULES_ROOT = REPO_ROOT / "src" / "modules"


def _relative(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def scaffold_module(
    *,
    tier: str,
    category: str,
    module_name: str,
    description: str | None,
    blueprint: str | None,
    force: bool,
    dry_run: bool,
    modules_root: Path,
) -> ModuleScaffoldResult:
    scaffolder = ModuleScaffolder(modules_root=modules_root)
    return scaffolder.create_module(
        tier=tier,
        category=category,
        module_name=module_name,
        description=description,
        blueprint=blueprint,
        force=force,
        dry_run=dry_run,
    )


def scaffold_result_to_dict(result: ModuleScaffoldResult, dry_run: bool) -> dict:
    return {
        "module_path": _relative(result.module_path),
        "created_files": [_relative(path) for path in result.created_files],
        "overwritten_files": [_relative(path) for path in result.overwritten_files],
        "skipped_files": [_relative(path) for path in result.skipped_files],
        "context": result.context,
        "dry_run": dry_run,
    }


def scaffold_summary_lines(result: ModuleScaffoldResult, dry_run: bool) -> List[str]:
    lines: List[str] = []
    if dry_run:
        lines.append("Dry run — planned scaffold (no files written):")

    lines.extend(_format_paths("Created" if not dry_run else "Would create", result.created_files))
    lines.extend(
        _format_paths(
            "Overwritten" if not dry_run else "Would overwrite",
            result.overwritten_files,
        )
    )
    lines.extend(_format_paths("Skipped" if not dry_run else "Would skip", result.skipped_files))

    tier = result.context.get("tier", "free")
    category_path = result.context.get("category_path", "core")
    module_name = result.context.get("module_name", result.module_path.name)
    module_slug = result.context.get("module_slug") or f"{tier}/{category_path}/{module_name}"
    module_import_path = result.context.get("module_import_path")

    lines.append("")
    lines.append("📁 Module scaffold ready at:" if not dry_run else "📍 Module scaffold path:")
    lines.append(f"  {_relative(result.module_path)}")

    if not dry_run:
        lines.append("Next steps:")
        lines.append("  • Review module.yaml metadata and adjust compatibility/testing sections.")
        lines.append("  • Define snippet bundles in config/snippets.yaml for reusable inserts.")
        if module_import_path:
            lines.append(
                "  • Smoke-test generator: poetry run python -m "
                f"{module_import_path}.generate fastapi ./tmp/{module_name}"
            )
        validate_cmd = (
            "  • Validate structure: poetry run python -c "
            '"from core.services.module_structure_validator import ensure_module_structure; '
            f"ensure_module_structure('{module_slug}')\""
        )
        lines.append(validate_cmd)

    return lines


def _format_paths(label: str, items: Iterable[Path]) -> List[str]:
    entries = [f"  - {_relative(path)}" for path in sorted(set(items))]
    if not entries:
        return []
    return [f"{label} ({len(entries)}):", *entries]


def ensure_structure_spec_ready() -> None:
    load_structure_spec()


def collect_validation_results(
    modules: Sequence[str] | None,
    modules_root: Path,
) -> List[ValidationResult]:
    targets: Sequence[str] | None = modules or None
    return validate_modules(targets, modules_root=modules_root)


def validation_summary_lines(
    results: Sequence[ValidationResult],
    fail_fast: bool,
) -> Tuple[int, List[str]]:
    lines: List[str] = []
    exit_code = 0
    for result in results:
        lines.append(result.summary())
        for message in result.messages:
            lines.append(f"  - {message}")
        if not result.valid:
            exit_code = 1
            if fail_fast:
                break
    return exit_code, lines


def validation_results_to_dict(
    results: Sequence[ValidationResult],
    modules_root: Path,
) -> dict:
    return {
        "modules_root": _relative(modules_root),
        "results": [validation_result_to_dict(result) for result in results],
        "valid": all(result.valid for result in results),
    }


def validation_result_to_dict(result: ValidationResult) -> dict:
    return {
        "module": result.module,
        "module_path": _relative(result.module_path),
        "valid": result.valid,
        "spec_version": result.spec_version,
        "missing_files": result.missing_files,
        "missing_directories": result.missing_directories,
        "extra_files": result.extra_files,
        "extra_directories": result.extra_directories,
        "verification_file": result.verification_file,
        "tree_hash": result.tree_hash,
        "messages": result.messages,
    }


def ensure_module_validation(
    module_slug: str,
    modules_root: Path,
) -> Tuple[ValidationResult, ModuleStructureError | None]:
    result = collect_validation_results([module_slug], modules_root)[0]
    if result.valid:
        return result, None
    try:
        ensure_module_structure(module_slug, modules_root=modules_root)
    except ModuleStructureError as exc:
        return result, exc
    return result, None


__all__ = [
    "DEFAULT_MODULES_ROOT",
    "ModuleStructureError",
    "ValidationResult",
    "collect_validation_results",
    "ensure_module_validation",
    "ensure_structure_spec_ready",
    "scaffold_module",
    "scaffold_result_to_dict",
    "scaffold_summary_lines",
    "validation_result_to_dict",
    "validation_results_to_dict",
    "validation_summary_lines",
]
