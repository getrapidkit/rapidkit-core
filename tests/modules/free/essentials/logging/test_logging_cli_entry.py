from pathlib import Path

import pytest

from modules.free.essentials.logging import generate
from modules.shared.generator.module_generator import BaseModuleGenerator


@pytest.fixture
def generate_cli(monkeypatch, tmp_path):
    def _runner(variant: str = "fastapi") -> Path:
        def _no_bump(config, **unused):
            if unused:
                next(iter(unused.items()))
            return dict(config), False

        def _noop_validate(self, plugin, name):  # noqa: ARG001
            return None

        output_dir = tmp_path / variant
        monkeypatch.setattr(generate, "ensure_version_consistency", _no_bump)
        monkeypatch.setattr(BaseModuleGenerator, "_validate_requirements", _noop_validate)
        monkeypatch.setattr(
            generate.sys,
            "argv",
            ["generate.py", variant, str(output_dir)],
        )

        generate.main()
        return output_dir

    return _runner


def test_generate_main_fastapi(generate_cli):
    output_dir = generate_cli("fastapi")

    assert (output_dir / "src").exists()
    assert (output_dir / ".rapidkit" / "vendor").exists()


def test_generate_main_nestjs(generate_cli):
    output_dir = generate_cli("nestjs")

    config_dir = output_dir / "src" / "modules" / "free" / "essentials" / "logging"
    expected = {
        config_dir / "logging.service.ts",
        config_dir / "logging.controller.ts",
        config_dir / "logging.module.ts",
        config_dir / "configuration.ts",
        config_dir / "index.ts",
        config_dir / "validation.ts",
    }

    for artefact in expected:
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} should not be empty"

    controller_src = (config_dir / "logging.controller.ts").read_text()
    assert (
        "@Controller('logging')" in controller_src or '@Controller("logging")' in controller_src
    ), "Controller should expose logging routes"
    assert "@Get()" in controller_src
    assert "@Get('health')" in controller_src or '@Get("health")' in controller_src
