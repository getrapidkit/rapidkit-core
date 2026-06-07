import pytest


def test_ai_guardrails_redacts_pii_and_allows_medium_findings(rendered_ai_guardrails) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_ai_guardrails["vendor"]

    guardrails = vendor.AiGuardrails()
    decision = guardrails.check_input("Email ada@example.com or call +1 555 010 9999")

    assert decision.allowed is True
    assert "[REDACTED_EMAIL]" in decision.redacted_content
    assert "[REDACTED_PHONE]" in decision.redacted_content
    assert {finding.code for finding in decision.findings} == {"email_detected", "phone_detected"}


def test_ai_guardrails_blocks_secrets_and_terms(rendered_ai_guardrails) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_ai_guardrails["vendor"]

    guardrails = vendor.AiGuardrails(vendor.AiGuardrailsConfig(blocked_terms=("wire funds",)))
    decision = guardrails.check_output("wire funds now with api_key=sk_test_abcdefghijkl")

    assert decision.blocked is True
    assert "[REDACTED_SECRET]" in decision.redacted_content
    assert {finding.code for finding in decision.findings} == {"blocked_term", "secret_detected"}
    with pytest.raises(vendor.AiGuardrailsError):
        guardrails.assert_allowed(decision)
