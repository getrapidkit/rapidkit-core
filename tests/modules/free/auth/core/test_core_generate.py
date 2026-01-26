from pathlib import Path

import yaml


def test_generator_entrypoint() -> None:
    """Smoky assertion ensuring generator is importable."""

    module_root = Path(__file__).resolve().parents[5] / "src/modules/free/auth/core"
    assert module_root.exists()


def test_config_registers_snippets() -> None:
    module_root = Path(__file__).resolve().parents[5] / "src/modules/free/auth/core"
    config_path = module_root / "config" / "base.yaml"
    content = config_path.read_text(encoding="utf-8")
    config = yaml.safe_load(content)

    snippets = {entry["name"] for entry in config.get("snippets", [])}

    assert "auth_core_env" in snippets
    assert "auth_core_settings_fields" in snippets


def test_integration_template_exists() -> None:
    module_root = Path(__file__).resolve().parents[5] / "src/modules/free/auth/core"
    template_path = (
        module_root / "templates" / "tests" / "integration" / "test_auth_core_integration.j2"
    )
    assert template_path.exists()
