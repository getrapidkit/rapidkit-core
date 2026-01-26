"""Integration smoke tests for Observability Core."""

from __future__ import annotations

import importlib


def test_generate_module_importable() -> None:
    module = importlib.import_module("modules.free.observability.core.generate")
    assert module.MODULE_NAME == "observability_core"


def test_template_renderer_accessible(module_generate) -> None:
    assert hasattr(module_generate, "TemplateRenderer")
