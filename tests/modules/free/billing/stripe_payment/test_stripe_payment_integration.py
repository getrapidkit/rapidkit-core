"""Integration smoke tests for Stripe Payment."""

from __future__ import annotations

import importlib


def test_generate_module_importable() -> None:
    module = importlib.import_module("src.modules.free.billing.stripe_payment.generate")
    assert module.MODULE_NAME == "stripe_payment"


def test_template_renderer_accessible(module_generate) -> None:
    assert hasattr(module_generate, "TemplateRenderer")
