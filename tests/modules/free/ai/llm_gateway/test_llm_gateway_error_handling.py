import pytest


def test_llm_gateway_reports_all_provider_failures(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_llm_gateway["vendor"]

    def broken_provider(request):  # type: ignore[no-untyped-def]
        raise RuntimeError("provider secret should not appear")

    config = vendor.LlmGatewayConfig(default_provider="broken", fallback_providers=())
    gateway = vendor.LlmGateway(config=config, providers={"broken": broken_provider})

    with pytest.raises(vendor.LlmGatewayError) as exc_info:
        gateway.complete(vendor.LlmGatewayRequest(prompt="hello"))

    assert "all providers failed" in str(exc_info.value)
    assert "broken" in str(exc_info.value)
