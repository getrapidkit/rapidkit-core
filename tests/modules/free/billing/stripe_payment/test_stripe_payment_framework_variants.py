"""Framework variant expectations for Stripe Payment."""

from __future__ import annotations


def test_variants_declared(module_config: dict[str, object]) -> None:
    variants = module_config.get("generation", {}).get("variants", {})  # type: ignore[assignment]
    assert isinstance(variants, dict)
    assert "fastapi" in variants
    assert "nestjs" in variants


def test_fastapi_files_listed(module_config: dict[str, object]) -> None:
    fastapi_variants = module_config["generation"]["variants"]["fastapi"]  # type: ignore[index]
    files = fastapi_variants.get("files", [])
    assert any(
        entry.get("output") == "src/modules/free/billing/stripe_payment/stripe_payment.py"
        for entry in files
    )


def test_nestjs_files_listed(module_config: dict[str, object]) -> None:
    nest_variants = module_config["generation"]["variants"]["nestjs"]  # type: ignore[index]
    files = nest_variants.get("files", [])
    assert any(
        entry.get("output") == "src/modules/free/billing/stripe_payment/stripe-payment.service.ts"
        for entry in files
    )
