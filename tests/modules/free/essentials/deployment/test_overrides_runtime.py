from __future__ import annotations

from pathlib import Path

import pytest  # type: ignore[import-not-found]

from modules.free.essentials.deployment.overrides import DeploymentOverrides


def test_apply_base_context_overrides_respect_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RAPIDKIT_DEPLOYMENT_SKIP_CI", "1")
    monkeypatch.setenv("RAPIDKIT_DEPLOYMENT_INCLUDE_POSTGRES", "1")

    overrides = DeploymentOverrides(module_root=tmp_path)
    base_context = {"include_ci": True, "include_postgres": False}
    mutated = overrides.apply_base_context(base_context)

    assert not mutated["include_ci"]
    assert mutated["include_postgres"]


def test_apply_variant_context_forces_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RAPIDKIT_DEPLOYMENT_FORCE_RUNTIME", "node")

    overrides = DeploymentOverrides(module_root=tmp_path)
    variant_context = {"runtime": "python"}
    mutated = overrides.apply_variant_context(variant_context)

    assert mutated["runtime"] == "node"


def test_extra_workflow_template_absolute_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template_path = tmp_path / "extra.yml.j2"
    template_path.write_text("name: extra\n")
    monkeypatch.setenv("RAPIDKIT_DEPLOYMENT_EXTRA_WORKFLOW", str(template_path))

    overrides = DeploymentOverrides(module_root=tmp_path)
    resolved = overrides.extra_workflow_template()
    assert resolved == template_path
    assert overrides.extra_workflow_root() == template_path.parent


def test_extra_workflow_template_relative_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    template_path = module_root / "templates" / "extra.yml.j2"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text("name: extra\n")

    monkeypatch.setenv("RAPIDKIT_DEPLOYMENT_EXTRA_WORKFLOW", "templates/extra.yml.j2")
    overrides = DeploymentOverrides(module_root=module_root)

    resolved = overrides.extra_workflow_template()
    assert resolved == template_path
    assert overrides.extra_workflow_root() == template_path.parent
