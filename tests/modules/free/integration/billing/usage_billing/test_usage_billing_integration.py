from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

from modules.free.billing.usage_billing.generate import UsageBillingModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_billing_usage_billing_generates_and_summarizes_metered_usage(
    tmp_path: Path,
) -> None:
    generator = UsageBillingModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/billing/usage_billing.py"
    )
    vendor = _load_module("integration_usage_billing_vendor", vendor_path)

    runtime = vendor.UsageBilling()
    runtime.register_meter(
        key="downloads",
        unit="download",
        price_per_unit="0.25",
        included_units=2,
        hard_limit=10,
    )
    first = runtime.record_usage(
        account_id="acct_1",
        meter="downloads",
        quantity=5,
        idempotency_key="evt_1",
    )
    duplicate = runtime.record_usage(
        account_id="acct_1",
        meter="downloads",
        quantity=9,
        idempotency_key="evt_1",
    )
    summary = runtime.summarize(account_id="acct_1", meter="downloads")
    receipt = runtime.close_billing_cycle(account_id="acct_1", meter="downloads")

    assert first == duplicate
    assert summary.quantity == Decimal("5")
    assert summary.billable_units == Decimal("3")
    assert summary.estimated_amount == Decimal("0.75")
    assert receipt["estimated_amount"] == "0.75"
    assert runtime.audit_events(account_id="acct_1")
    assert runtime.check_quota(account_id="acct_1", meter="downloads", quantity=6).allowed is False
