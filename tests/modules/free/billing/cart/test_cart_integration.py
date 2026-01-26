"""Integration smoke tests for Cart."""

from __future__ import annotations

import importlib


def test_generate_module_importable() -> None:
    module = importlib.import_module("src.modules.free.billing.cart.generate")
    assert module.MODULE_NAME == "cart"


def test_template_renderer_accessible(module_generate) -> None:
    assert hasattr(module_generate, "CartModuleGenerator")
