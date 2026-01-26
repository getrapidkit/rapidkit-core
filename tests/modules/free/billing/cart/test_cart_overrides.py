"""Override scaffolding tests for Cart."""

from __future__ import annotations

from pathlib import Path


def test_override_class_declared(module_root: Path) -> None:
    overrides_source = (module_root / "overrides.py").read_text(encoding="utf-8")
    assert "class CartOverrides" in overrides_source


def test_environment_overrides_mutate_context(
    monkeypatch, cart_module_generator, module_config
) -> None:
    monkeypatch.setenv("RAPIDKIT_CART_DEFAULT_DISCOUNT", "ENV10")
    monkeypatch.setenv("RAPIDKIT_CART_MAX_UNIQUE_ITEMS", "7")
    base_context = cart_module_generator.build_base_context(module_config)
    enriched = cart_module_generator.apply_base_context_overrides(base_context)
    defaults = enriched["cart_defaults"]
    assert defaults["default_discount_code"] == "ENV10"
    assert defaults["auto_apply_default_discount"] is True
    assert defaults["max_unique_items"] == 7
