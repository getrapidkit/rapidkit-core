import pytest


def test_ai_guardrails_raises_clear_errors(rendered_ai_guardrails) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_ai_guardrails["vendor"]

    guardrails = vendor.AiGuardrails(vendor.AiGuardrailsConfig(blocked_terms=("blocked",)))
    decision = guardrails.check_input("blocked content")

    with pytest.raises(vendor.AiGuardrailsError):
        guardrails.assert_allowed(decision)
