"""Standard module metadata checks for Stripe Payment."""

from __future__ import annotations

from pathlib import Path


def test_documentation_links_present(module_docs: dict[str, object]) -> None:
    expected = [
        "readme",
        "overview",
        "usage",
        "advanced",
        "migration",
        "troubleshooting",
        "api_docs",
    ]
    for key in expected:
        assert key in module_docs, f"documentation.{key} missing"
        if key == "api_docs":
            continue
        assert module_docs.get(key), f"documentation.{key} must be set"


def test_unit_tests_list(module_config: dict[str, object]) -> None:
    unit_tests = module_config.get("testing", {}).get("unit_tests", [])  # type: ignore[assignment]
    normalized = {Path(test_path).name for test_path in unit_tests}
    expected = [
        "test_stripe_payment_generator.py",
        "test_stripe_payment_overrides.py",
        "test_stripe_payment_runtime.py",
        "test_stripe_payment_adapters.py",
        "test_stripe_payment_validation.py",
        "test_stripe_payment_error_handling.py",
        "test_stripe_payment_health_check.py",
        "test_stripe_payment_framework_variants.py",
        "test_stripe_payment_vendor_layer.py",
        "test_stripe_payment_configuration.py",
        "test_stripe_payment_versioning.py",
        "test_stripe_payment_integration.py",
        "test_stripe_payment_standard_module.py",
    ]
    for name in expected:
        assert name in normalized
