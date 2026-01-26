from pathlib import Path

import pytest

from modules.free.auth.core import generate
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

    auth_core_dir = output_dir / "src" / "modules" / "free" / "auth" / "core"
    expected = {
        auth_core_dir / "auth-core.service.ts",
        auth_core_dir / "auth-core.controller.ts",
        auth_core_dir / "auth-core.module.ts",
        auth_core_dir / "configuration.ts",
        auth_core_dir / "index.ts",
    }
    config_validation = (
        output_dir
        / "src"
        / "modules"
        / "free"
        / "auth"
        / "core"
        / "config"
        / "auth-core.validation.ts"
    )

    for artefact in (*expected, config_validation):
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} should not be empty"

    controller_src = (auth_core_dir / "auth-core.controller.ts").read_text()
    assert (
        "@Controller('auth/core')" in controller_src or '@Controller("auth/core")' in controller_src
    ), "Controller should expose auth/core routes"

    assert "@Get('metadata')" in controller_src or '@Get("metadata")' in controller_src
    assert "@Get('features')" in controller_src or '@Get("features")' in controller_src
    assert "@Get('health')" in controller_src or '@Get("health")' in controller_src
