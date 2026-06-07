from pathlib import Path

import yaml


def test_ai_guardrails_config_declares_runtime_profiles() -> None:
    config_path = Path("src/modules/free/ai/ai_guardrails/config/base.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert "fastapi/standard" in config["profiles"]
    assert "nestjs/standard" in config["profiles"]
    assert config["variables"]["request_timeout_seconds"]["default"] > 0


def test_ai_guardrails_config_defaults(rendered_ai_guardrails) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_ai_guardrails["vendor"]

    config = vendor.AiGuardrailsConfig()

    assert config.enabled is True
    assert config.block_on_high_severity is True
    assert config.pii_redaction is True
