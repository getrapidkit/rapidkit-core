"""Consistency checks for module scaffolding infrastructure."""

from __future__ import annotations

from pathlib import Path

import yaml

MODULES_ROOT = Path(__file__).resolve().parents[2] / "src/modules/free"


def _iter_module_dirs() -> list[tuple[Path, Path]]:
    modules: list[tuple[Path, Path]] = []
    for module_yaml in MODULES_ROOT.rglob("module.yaml"):
        modules.append((module_yaml.parent, module_yaml))
    return modules


def test_framework_registries_do_not_define_plugins() -> None:
    """Ensure framework registries only re-export dedicated plugin implementations."""

    offenders: list[Path] = []
    for init_path in MODULES_ROOT.rglob("frameworks/__init__.py"):
        text = init_path.read_text(encoding="utf-8")
        if "class FastAPIPlugin" in text or "class NestJSPlugin" in text:
            offenders.append(init_path.relative_to(MODULES_ROOT))

    assert not offenders, (
        "inline plugin class definitions detected in registry modules" f": {offenders}"
    )


def test_declared_framework_plugins_exist() -> None:
    """Verify every declared framework variant has a concrete plugin implementation."""

    missing: list[str] = []
    for module_dir, module_yaml in _iter_module_dirs():
        data = yaml.safe_load(module_yaml.read_text(encoding="utf-8")) or {}
        variants = data.get("generation", {}).get("variants", {})
        framework_dir = module_dir / "frameworks"
        for variant_name in variants:
            if variant_name not in {"fastapi", "nestjs"}:
                continue
            candidate = framework_dir / f"{variant_name}.py"
            if not candidate.exists():
                rel_path = candidate.relative_to(MODULES_ROOT)
                missing.append(str(rel_path))

    assert not missing, "declared framework variants missing plugin implementations" f": {missing}"


def test_documentation_references_resolve() -> None:
    """Check that documentation files referenced in module manifests are present."""

    missing_docs: list[str] = []
    for module_dir, module_yaml in _iter_module_dirs():
        data = yaml.safe_load(module_yaml.read_text(encoding="utf-8")) or {}
        docs_section = data.get("documentation", {})
        for value in docs_section.values():
            if value is None:
                continue
            if isinstance(value, list):
                candidates = value
            else:
                candidates = [value]
            for rel in candidates:
                doc_path = module_dir / rel
                if not doc_path.exists():
                    missing_docs.append(str(doc_path.relative_to(MODULES_ROOT)))

    assert not missing_docs, (
        "module.yaml documentation entries referencing missing files" f": {missing_docs}"
    )
