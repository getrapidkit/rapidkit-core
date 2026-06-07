"""Health checks tests for Stripe Payment."""

from __future__ import annotations


def test_stripe_payment_health_reflects_enabled_state(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]

    enabled = runtime_mod.StripePayment().health_check()
    disabled = runtime_mod.StripePayment(
        runtime_mod.StripePaymentConfig(enabled=False)
    ).health_check()

    assert enabled["status"] == "ok"
    assert enabled["mode"] == "test"
    assert enabled["default_currency"] == "usd"
    assert enabled["manual_capture_available"] is True
    assert enabled["stats"]["payment_intents"] == 0
    assert disabled["status"] == "degraded"
