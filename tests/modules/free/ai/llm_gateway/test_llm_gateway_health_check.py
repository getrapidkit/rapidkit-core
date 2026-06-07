def test_llm_gateway_health_reports_providers_and_usage(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_llm_gateway["vendor"]

    gateway = vendor.LlmGateway()
    gateway.complete(vendor.LlmGatewayRequest(prompt="health probe"))

    payload = gateway.health_check()

    assert payload["module"] == "llm_gateway"
    assert payload["status"] == "ok"
    assert "local" in payload["providers"]
    assert payload["usage"]["requests"] == 1
