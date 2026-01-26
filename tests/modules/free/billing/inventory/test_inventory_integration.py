"""Integration smoke tests for Inventory."""

from __future__ import annotations

import importlib


def test_generate_module_importable() -> None:
    module = importlib.import_module("src.modules.free.billing.inventory.generate")
    assert module.MODULE_NAME == "inventory"


def test_template_renderer_accessible(module_generate) -> None:
    assert hasattr(module_generate, "TemplateRenderer")


def test_generated_bundle_contains_framework_outputs(generated_bundle) -> None:
    target = generated_bundle["target"]
    assert (target / "src" / "modules" / "free" / "billing" / "inventory" / "inventory.py").exists()
    assert (
        target / "src" / "modules" / "free" / "billing" / "inventory" / "routers" / "inventory.py"
    ).exists()
    assert (target / "nestjs" / "configuration.js").exists()
