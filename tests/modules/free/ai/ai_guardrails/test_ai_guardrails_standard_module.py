def test_ai_guardrails_generated_runtime_is_usable(rendered_ai_guardrails) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_ai_guardrails["vendor"]

    guardrails = vendor.AiGuardrails()
    decision = guardrails.check_input("hello")

    assert decision.allowed is True
    assert decision.redacted_content == "hello"
