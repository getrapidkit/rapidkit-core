"""Integration tests for Stripe Payment."""

from __future__ import annotations

import hmac
import importlib.util
import json
import sys
from hashlib import sha256
from pathlib import Path

from modules.free.billing.stripe_payment.generate import StripePaymentModuleGenerator


def _load_generated_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated Stripe Payment runtime from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _sign(payload: dict, secret: str) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), body, sha256).hexdigest()


def test_stripe_payment_end_to_end_intent_and_webhook(tmp_path: Path) -> None:
    generator = StripePaymentModuleGenerator()
    config = generator.load_module_config()
    context = generator.apply_base_context_overrides(generator.build_base_context(config))
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(context["rapidkit_vendor_module"])
        / str(context["rapidkit_vendor_version"])
        / "src"
        / "modules"
        / "free"
        / "billing"
        / "stripe_payment"
        / "stripe_payment.py"
    )
    runtime_mod = _load_generated_module("integration_stripe_payment_vendor", vendor_path)
    runtime = runtime_mod.StripePayment()

    intent = runtime.create_payment_intent(
        account_id="acct_1",
        amount="49.90",
        currency="usd",
        idempotency_key="intent-1",
    )
    payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": intent.id}}}
    signature = _sign(payload, "local-dev-webhook-secret")
    result = runtime.handle_webhook(payload=payload, signature=signature)

    assert result["accepted"] is True
    assert runtime.list_payment_intents(status="succeeded")[0].id == intent.id
    assert runtime.reconcile()["by_status"]["succeeded"] == 1
    assert runtime.audit_events(intent_id=intent.id)
