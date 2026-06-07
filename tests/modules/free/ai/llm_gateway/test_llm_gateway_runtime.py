import pytest


def test_llm_gateway_local_provider_records_usage(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_llm_gateway["vendor"]

    gateway = vendor.LlmGateway()
    response = gateway.complete(vendor.LlmGatewayRequest(prompt="Summarize invoice risk"))

    assert response.provider == "local"
    assert response.text.startswith("[local:default]")
    assert response.estimated_tokens > 0

    usage = gateway.usage_snapshot()
    assert usage["requests"] == 1
    assert usage["by_provider"]["local"]["requests"] == 1


def test_llm_gateway_fallback_after_provider_failure(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_llm_gateway["vendor"]

    def broken_provider(request):  # type: ignore[no-untyped-def]
        raise RuntimeError("upstream unavailable")

    config = vendor.LlmGatewayConfig(default_provider="primary", fallback_providers=("local",))
    gateway = vendor.LlmGateway(config=config, providers={"primary": broken_provider})

    response = gateway.complete(vendor.LlmGatewayRequest(prompt="hello"))

    assert response.provider == "local"
    assert response.fallback_used is True


def test_llm_gateway_budget_guard(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_llm_gateway["vendor"]

    config = vendor.LlmGatewayConfig(max_prompt_chars=8, max_estimated_tokens=20)
    gateway = vendor.LlmGateway(config=config)

    with pytest.raises(vendor.LlmGatewayError, match="max_prompt_chars"):
        gateway.complete(vendor.LlmGatewayRequest(prompt="this prompt is too long"))
