"""Integration smoke tests for Security Headers."""

from __future__ import annotations

import importlib


def test_generate_module_importable() -> None:
    module = importlib.import_module("modules.free.security.security_headers.generate")
    assert module.MODULE_NAME == "security_headers"


def test_template_renderer_accessible(module_generate) -> None:
    assert hasattr(module_generate, "TemplateRenderer")
