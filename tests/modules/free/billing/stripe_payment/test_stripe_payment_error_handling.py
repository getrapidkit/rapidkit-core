"""Error handling tests for Stripe Payment."""

from __future__ import annotations


def test_stripe_payment_bool_resolution_uses_safe_fallback(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]

    assert runtime_mod._resolve_bool("yes", False) is True
    assert runtime_mod._resolve_bool("off", True) is False
    assert runtime_mod._resolve_bool("definitely", True) is True


def test_stripe_payment_webhook_config_handles_missing_events(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]
    runtime_mod.WEBHOOK.pop("events", None)

    webhook = runtime_mod.StripePayment().webhook_config()

    assert webhook["events"] == []


def test_stripe_payment_rejects_invalid_webhook_signature(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]
    runtime = runtime_mod.StripePayment()
    intent = runtime.create_payment_intent(
        account_id="acct_1",
        amount="10.00",
        currency="usd",
        idempotency_key="pi-webhook",
    )
    payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": intent.id}}}

    try:
        runtime.handle_webhook(payload=payload, signature="bad-signature")
    except runtime_mod.StripePaymentError as exc:
        assert "invalid webhook signature" in str(exc)
    else:
        raise AssertionError("expected StripePaymentError")
