"""Integration tests for Observability Core module generation."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from modules.free.observability.core import generate

pytestmark = [pytest.mark.integration, pytest.mark.template_integration]


def _run_generator(variant: str, target_dir: Path) -> None:
    """Execute the module generator for the given variant into target_dir."""
    original_argv = sys.argv
    original_ensure_version_consistency = getattr(generate, "ensure_version_consistency", None)

    def _no_bump(config, **unused):
        if unused:
            next(iter(unused.items()))
        return dict(config), False

    try:
        if original_ensure_version_consistency is not None:
            generate.ensure_version_consistency = _no_bump  # type: ignore[assignment]
        sys.argv = ["generate", variant, str(target_dir)]
        module_generator = generate.ObservabilityModuleGenerator()
        renderer = module_generator.create_renderer()
        jinja_env = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
        if jinja_env is None:
            pytest.skip("jinja2 is required to render Observability Core templates")
        generate.main()
    finally:
        sys.argv = original_argv
        if original_ensure_version_consistency is not None:
            generate.ensure_version_consistency = original_ensure_version_consistency  # type: ignore[assignment]


def test_generate_fastapi_variant() -> None:
    """Ensure FastAPI variant renders key artefacts and vendor payload."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir)
        _run_generator("fastapi", target)

        module_root = target / "src" / "modules" / "free" / "observability" / "core"
        assert (module_root / "observability_core.py").exists()
        assert (module_root / "routers" / "observability_core.py").exists()
        assert (target / "src" / "health" / "observability_core.py").exists()

        config_file = target / "config" / "observability" / "observability_core.yaml"
        assert config_file.exists(), "FastAPI configuration should be generated"
        cfg = yaml.safe_load(config_file.read_text())
        assert isinstance(cfg, dict)

        integration_test = (
            target
            / "tests"
            / "modules"
            / "integration"
            / "observability"
            / "test_observability_core_integration.py"
        )
        assert integration_test.exists(), "FastAPI integration test should be generated"

        module_cfg = generate.load_module_config()
        vendor_root = target / module_cfg["generation"]["vendor"]["root"]
        vendor_config = (
            vendor_root / module_cfg["name"] / module_cfg["version"] / "nestjs" / "configuration.js"
        )
        assert vendor_config.exists(), "Vendor configuration snapshot should be emitted"


def test_generate_nestjs_variant() -> None:
    """Ensure NestJS variant emits controller/service/module and integration spec."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir)
        _run_generator("nestjs", target)

        nest_root = target / "src" / "modules" / "free" / "observability" / "core"
        assert (nest_root / "observability-core" / "observability-core.service.ts").exists()
        assert (nest_root / "observability-core" / "observability-core.controller.ts").exists()
        assert (nest_root / "observability-core" / "observability-core.module.ts").exists()
        assert (nest_root / "observability-core" / "observability-core.configuration.ts").exists()
        assert (target / "src" / "health" / "observability-core-health.controller.ts").exists()
        assert (target / "src" / "health" / "observability-core-health.module.ts").exists()

        integration_spec = (
            target
            / "tests"
            / "modules"
            / "integration"
            / "observability"
            / "observability_core.integration.spec.ts"
        )
        assert integration_spec.exists(), "NestJS integration spec should be generated"

        # Ensure template content is non-empty to catch broken renders
        assert integration_spec.read_text().strip(), "Integration spec should not be empty"
