import pytest


def test_llm_gateway_rejects_empty_prompt(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_llm_gateway["vendor"]

    with pytest.raises(vendor.LlmGatewayError, match="prompt is required"):
        vendor.LlmGateway().complete(vendor.LlmGatewayRequest(prompt=" "))


def test_llm_gateway_rejects_disabled_runtime(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_llm_gateway["vendor"]

    gateway = vendor.LlmGateway(vendor.LlmGatewayConfig(enabled=False))

    with pytest.raises(vendor.LlmGatewayError, match="disabled"):
        gateway.complete(vendor.LlmGatewayRequest(prompt="hello"))
