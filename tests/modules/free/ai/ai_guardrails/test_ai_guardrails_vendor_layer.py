def test_ai_guardrails_vendor_exports_contract(rendered_ai_guardrails) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_ai_guardrails["vendor"]

    for name in (
        "AiGuardrails",
        "AiGuardrailsConfig",
        "AiGuardrailsError",
        "GuardrailDecision",
        "GuardrailFinding",
        "GuardrailSeverity",
    ):
        assert hasattr(vendor, name)
