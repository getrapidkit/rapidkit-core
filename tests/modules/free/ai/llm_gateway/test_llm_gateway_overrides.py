from modules.free.ai.llm_gateway.overrides import LlmGatewayOverrides


def test_llm_gateway_overrides_are_configurable() -> None:
    overrides = LlmGatewayOverrides()

    info = overrides.get_override_info()

    assert info == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
