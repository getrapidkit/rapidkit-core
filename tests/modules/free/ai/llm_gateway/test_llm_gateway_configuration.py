import yaml


def test_llm_gateway_config_declares_runtime_profiles() -> None:
    with open("src/modules/free/ai/llm_gateway/config/base.yaml", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    assert "fastapi/standard" in config["profiles"]
    assert "nestjs/standard" in config["profiles"]
    assert config["variables"]["request_timeout_seconds"]["default"] > 0


def test_llm_gateway_runtime_config_defaults(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_llm_gateway["vendor"]

    config = vendor.LlmGatewayConfig()

    assert config.enabled is True
    assert config.default_provider == "local"
    assert "local" in config.fallback_providers
