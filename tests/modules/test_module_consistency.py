"""Consistency checks for module scaffolding infrastructure."""

from __future__ import annotations

from pathlib import Path

import yaml

MODULES_ROOT = Path(__file__).resolve().parents[2] / "src/modules/free"
REGISTRY_PATH = MODULES_ROOT / "modules.yaml"


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


def test_free_modules_registry_matches_module_manifests() -> None:
    """Keep the legacy free registry in parity with module.yaml manifests."""

    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    registry_modules = registry.get("modules", {})
    manifest_modules: dict[str, Path] = {}

    for module_dir, module_yaml in _iter_module_dirs():
        data = yaml.safe_load(module_yaml.read_text(encoding="utf-8")) or {}
        name = str(data.get("name") or module_dir.name)
        manifest_modules[name] = module_yaml

    missing_from_registry = sorted(set(manifest_modules) - set(registry_modules))
    stale_registry_entries = sorted(set(registry_modules) - set(manifest_modules))

    assert not missing_from_registry, (
        "module.yaml files missing from free/modules.yaml" f": {missing_from_registry}"
    )
    assert not stale_registry_entries, (
        "free/modules.yaml contains modules without module.yaml" f": {stale_registry_entries}"
    )

    broken_template_paths: list[str] = []
    non_free_entries: list[str] = []
    metadata_mismatches: list[str] = []
    for name, entry in registry_modules.items():
        manifest = yaml.safe_load(manifest_modules[name].read_text(encoding="utf-8")) or {}
        if entry.get("access") != "free" or entry.get("tier") != "free":
            non_free_entries.append(name)
        templates_path = entry.get("templates_path")
        if not templates_path or not (MODULES_ROOT / str(templates_path) / "module.yaml").exists():
            broken_template_paths.append(name)
        for field in (
            "name",
            "display_name",
            "version",
            "status",
            "description",
            "tags",
            "category",
            "capabilities",
            "config_sources",
            "compatibility",
            "testing",
            "documentation",
            "support",
            "changelog",
            "validation",
            "rollback",
            "performance",
        ):
            expected = manifest.get(field)
            if field == "display_name":
                expected = manifest.get(
                    field, str(manifest.get("name", name)).replace("_", " ").title()
                )
            if field == "version":
                expected = str(manifest.get(field, "0.1.0"))
            if field == "status":
                expected = manifest.get(field, "stable")
            if field == "description":
                expected = manifest.get(field, "")
            if entry.get(field) != expected:
                metadata_mismatches.append(f"{name}.{field}")

    assert not non_free_entries, (
        "free/modules.yaml contains non-free entries" f": {non_free_entries}"
    )
    assert not broken_template_paths, (
        "free/modules.yaml templates_path entries do not resolve" f": {broken_template_paths}"
    )
    assert not metadata_mismatches, (
        "free/modules.yaml metadata drift detected" f": {metadata_mismatches}"
    )


def test_free_module_manifest_dependencies_resolve() -> None:
    """Every free manifest dependency should point to a real module slug."""

    known_slugs = {
        module_yaml.parent.relative_to(MODULES_ROOT.parent).as_posix()
        for _, module_yaml in _iter_module_dirs()
    }
    unresolved: list[str] = []

    for module_dir, module_yaml in _iter_module_dirs():
        data = yaml.safe_load(module_yaml.read_text(encoding="utf-8")) or {}
        slug = module_dir.relative_to(MODULES_ROOT.parent).as_posix()
        for dependency in data.get("depends_on", []) or []:
            dep = str(dependency).strip("/")
            if dep and dep not in known_slugs:
                unresolved.append(f"{slug} -> {dep}")

    assert not unresolved, "free module manifests reference unknown dependencies" f": {unresolved}"
