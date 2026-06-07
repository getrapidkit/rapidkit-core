from pathlib import Path

import yaml


def test_prompt_ops_config_declares_runtime_profiles() -> None:
    config_path = Path("src/modules/free/ai/prompt_ops/config/base.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert "fastapi/standard" in config["profiles"]
    assert "nestjs/standard" in config["profiles"]
    assert config["variables"]["request_timeout_seconds"]["default"] > 0


def test_prompt_ops_config_defaults(rendered_prompt_ops) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_prompt_ops["vendor"]

    config = vendor.PromptOpsConfig()

    assert config.enabled is True
    assert config.require_approval_for_publish is True
