"""Tests for module manifest utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.services import module_manifest


def _write_manifest(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_module_manifest_load_and_effective_name(tmp_path: Path) -> None:
    manifest_path = tmp_path / "module.yaml"
    _write_manifest(
        manifest_path,
        """
name: blog
version: 1.2.3
status: experimental
description: Blog module
display_name: Blog Wizard
profiles:
  - default
depends_on:
  - auth
feature_flags:
  preview: true
""".strip(),
    )

    manifest = module_manifest.ModuleManifest.load(manifest_path)

    assert manifest.name == "blog"
    assert manifest.version == "1.2.3"
    assert manifest.effective_name == "Blog Wizard"
    assert manifest.depends_on == ["auth"]
    assert manifest.raw == {"feature_flags": {"preview": True}}


def test_module_manifest_invalid_status_raises(tmp_path: Path) -> None:
    manifest_path = tmp_path / "module.yaml"
    _write_manifest(
        manifest_path,
        """
name: blog
status: totally-unknown
""".strip(),
    )

    with pytest.raises(RuntimeError):
        module_manifest.ModuleManifest.load(manifest_path)


def test_find_and_load_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules_root = tmp_path / "modules"
    module_dir = modules_root / "blog"
    module_dir.mkdir(parents=True)
    manifest_path = module_dir / "module.yaml"
    _write_manifest(manifest_path, "name: blog\n")

    # ensure resolver simply returns the directory we created
    monkeypatch.setattr(module_manifest, "resolve_module_directory", lambda root, name: root / name)

    found = module_manifest.find_manifest(modules_root, "blog")
    assert found == manifest_path

    loaded = module_manifest.load_manifest_or_none(modules_root, "blog")
    assert loaded is not None
    assert loaded.name == "blog"
    assert loaded.slug == "blog"

    missing = module_manifest.load_manifest_or_none(modules_root, "missing")
    assert missing is None


def test_load_all_manifests_skips_invalid(tmp_path: Path) -> None:
    modules_root = tmp_path / "modules"
    (modules_root / "valid").mkdir(parents=True)
    _write_manifest(modules_root / "valid/module.yaml", "name: valid\n")

    (modules_root / "invalid").mkdir(parents=True)
    _write_manifest(modules_root / "invalid/module.yaml", "name: invalid\nstatus: bad\n")

    (modules_root / "nested/a").mkdir(parents=True)
    _write_manifest(modules_root / "nested/a/module.yaml", "name: nested\n")

    manifests = module_manifest.load_all_manifests(modules_root)

    assert set(manifests) == {"valid", "nested/a"}
    assert all(isinstance(m, module_manifest.ModuleManifest) for m in manifests.values())


def test_topo_sort_modules_orders_dependencies() -> None:
    manifests: dict[str, module_manifest.ModuleManifest] = {
        "core": module_manifest.ModuleManifest(name="core", slug="core"),
        "auth": module_manifest.ModuleManifest(name="auth", slug="auth", depends_on=["core"]),
        "billing": module_manifest.ModuleManifest(
            name="billing", slug="billing", depends_on=["auth"]
        ),
    }

    ordered = module_manifest.topo_sort_modules(manifests)

    assert [m.name for m in ordered] == ["core", "auth", "billing"]


def test_topo_sort_modules_detects_cycles() -> None:
    manifests: dict[str, module_manifest.ModuleManifest] = {
        "a": module_manifest.ModuleManifest(name="a", slug="a", depends_on=["c"]),
        "b": module_manifest.ModuleManifest(name="b", slug="b", depends_on=["a"]),
        "c": module_manifest.ModuleManifest(name="c", slug="c", depends_on=["b"]),
    }

    with pytest.raises(module_manifest.DependencyCycleError):
        module_manifest.topo_sort_modules(manifests)


def test_compute_install_order_filters_to_targets() -> None:
    manifests: dict[str, module_manifest.ModuleManifest] = {
        "core": module_manifest.ModuleManifest(name="core", slug="core"),
        "auth": module_manifest.ModuleManifest(name="auth", slug="auth", depends_on=["core"]),
        "billing": module_manifest.ModuleManifest(
            name="billing", slug="billing", depends_on=["auth"]
        ),
        "notifications": module_manifest.ModuleManifest(name="notifications", slug="notifications"),
    }

    ordered = module_manifest.compute_install_order(["billing"], manifests)

    assert [m.name for m in ordered] == ["core", "auth", "billing"]
