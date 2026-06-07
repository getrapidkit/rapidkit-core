"""Adapter integration tests for Stripe Payment."""

from __future__ import annotations


def test_stripe_payment_exports_stable_public_api(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]

    assert runtime_mod.MODULE_NAME == "stripe_payment"
    assert runtime_mod.MODULE_TITLE == "Stripe Payment"
    assert "StripePayment" in runtime_mod.__all__
    assert "StripePaymentConfig" in runtime_mod.__all__


def test_stripe_payment_config_metadata_is_isolated(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]
    first = runtime_mod.StripePaymentConfig()
    second = runtime_mod.StripePaymentConfig()

    first.metadata["tenant"] = "acme"

    assert second.metadata == {"product": "rapidkit", "source": "stripe-payment-module"}
