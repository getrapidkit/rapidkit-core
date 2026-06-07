"""Validation tests for Stripe Payment."""

from __future__ import annotations


def test_stripe_payment_webhook_events_are_normalized(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]
    runtime_mod.WEBHOOK["events"] = [
        " payment_intent.succeeded ",
        "",
        "charge.refunded",
    ]

    webhook = runtime_mod.StripePayment().webhook_config()

    assert webhook["events"] == ["payment_intent.succeeded", "charge.refunded"]


def test_stripe_payment_invalid_string_lists_are_empty(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]
    runtime_mod.BILLING["allowed_currencies"] = "usd,eur"
    runtime_mod.BILLING["default_payment_method_types"] = None
    runtime = runtime_mod.StripePayment()

    assert runtime.allowed_currencies() == []
    assert runtime.payment_method_types() == []
