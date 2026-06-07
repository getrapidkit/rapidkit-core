"""Runtime tests for Stripe Payment."""

from __future__ import annotations


def test_stripe_payment_metadata_is_defensive_copy(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]
    runtime = runtime_mod.StripePayment()

    first = runtime.metadata()
    first["defaults"]["mode"] = "mutated"
    second = runtime.metadata()

    assert second["module"] == "stripe_payment"
    assert second["defaults"]["mode"] == "test"
    assert second["features"]["enable_idempotency_keys"] is True
    assert second["environment"] == {
        "has_api_key": False,
        "has_webhook_secret": False,
    }


def test_stripe_payment_lists_runtime_billing_policy(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]
    runtime = runtime_mod.StripePayment()

    assert runtime.allowed_currencies() == ["usd", "eur", "gbp"]
    assert runtime.payment_method_types() == ["card", "us_bank_account"]
    assert runtime.retry_policy()["max_attempts"] == 3


def test_stripe_payment_creates_and_confirms_intent(rendered_stripe_payment) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_stripe_payment["runtime"]
    runtime = runtime_mod.StripePayment()

    first = runtime.create_payment_intent(
        account_id="acct_1",
        amount="19.99",
        currency="usd",
        idempotency_key="pi-1",
    )
    second = runtime.create_payment_intent(
        account_id="acct_1",
        amount="99.00",
        currency="usd",
        idempotency_key="pi-1",
    )
    confirmed = runtime.confirm_payment_intent(first.id)

    assert second.id == first.id
    assert confirmed.status == "succeeded"
    assert runtime.reconcile()["by_status"]["succeeded"] == 1
