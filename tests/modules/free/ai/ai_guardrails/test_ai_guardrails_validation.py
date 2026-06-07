import pytest


def test_ai_guardrails_validates_enterprise_policy(rendered_ai_guardrails) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_ai_guardrails["vendor"]

    guardrails = vendor.AiGuardrails()
    decision = guardrails.check_input("api_key=abcdefghijklmnop")

    assert decision.allowed is False
    assert any(finding.code == "secret_detected" for finding in decision.findings)
