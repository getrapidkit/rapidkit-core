from pathlib import Path

import yaml


def test_tool_registry_config_declares_runtime_profiles() -> None:
    config_path = Path("src/modules/free/ai/tool_registry/config/base.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert "fastapi/standard" in config["profiles"]
    assert "nestjs/standard" in config["profiles"]
    assert config["variables"]["request_timeout_seconds"]["default"] > 0


def test_tool_registry_config_defaults(rendered_tool_registry) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_tool_registry["vendor"]

    config = vendor.ToolRegistryConfig()

    assert config.enabled is True
    assert config.strict_permissions is True
    assert config.default_timeout_seconds > 0
