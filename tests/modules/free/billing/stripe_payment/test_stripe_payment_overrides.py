"""Override scaffolding tests for Stripe Payment."""

from __future__ import annotations

from pathlib import Path


def test_override_class_declared(module_root: Path) -> None:
    overrides_source = (module_root / "overrides.py").read_text(encoding="utf-8")
    assert "class StripePaymentOverrides" in overrides_source
