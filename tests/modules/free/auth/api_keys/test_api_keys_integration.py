"""Integration smoke tests for Api Keys."""

from __future__ import annotations

import importlib


def test_generate_module_importable() -> None:
    module = importlib.import_module("modules.free.auth.api_keys.generate")
    assert module.MODULE_NAME == "api_keys"


def test_template_renderer_accessible(module_generate) -> None:
    assert hasattr(module_generate, "TemplateRenderer")
