from pathlib import Path

import yaml


def test_agent_runtime_config_declares_runtime_profiles() -> None:
    config_path = Path("src/modules/free/ai/agent_runtime/config/base.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert "fastapi/standard" in config["profiles"]
    assert "nestjs/standard" in config["profiles"]
    assert config["variables"]["request_timeout_seconds"]["default"] > 0


def test_agent_runtime_config_defaults(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    config = vendor.AgentRuntimeConfig()

    assert config.enabled is True
    assert config.max_steps > 0
    assert config.retry_limit >= 0
