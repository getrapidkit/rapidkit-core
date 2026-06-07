def test_llm_gateway_generated_runtime_is_usable(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    runtime = rendered_llm_gateway["runtime"]

    gateway = runtime.LlmGateway()
    response = gateway.complete(runtime.LlmGatewayRequest(prompt="enterprise smoke"))

    assert response.text
    assert gateway.metadata()["module"] == "llm_gateway"
