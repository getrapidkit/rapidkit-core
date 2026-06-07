def test_llm_gateway_vendor_exports_runtime_contract(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_llm_gateway["vendor"]

    for name in (
        "LlmGateway",
        "LlmGatewayConfig",
        "LlmGatewayRequest",
        "LlmGatewayResponse",
        "LlmGatewayUsage",
        "LlmGatewayError",
    ):
        assert hasattr(vendor, name)

    assert vendor.estimate_tokens("abcd", 10) == 11
