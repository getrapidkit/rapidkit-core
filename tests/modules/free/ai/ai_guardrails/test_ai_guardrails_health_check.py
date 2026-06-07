def test_ai_guardrails_health_check_reports_runtime_state(rendered_ai_guardrails) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_ai_guardrails["vendor"]

    guardrails = vendor.AiGuardrails(vendor.AiGuardrailsConfig(blocked_terms=("x",)))
    guardrails.check_input("hello")

    health = guardrails.health_check()

    assert health["module"] == "ai_guardrails"
    assert health["checks"] == 1
