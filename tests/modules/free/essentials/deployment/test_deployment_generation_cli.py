from pathlib import Path

import pytest

from modules.free.essentials.deployment import generate
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

    root_expected = {
        output_dir / "Makefile",
        output_dir / ".dockerignore",
        output_dir / "Dockerfile",
        output_dir / "docker-compose.yml",
        output_dir / ".github" / "workflows" / "ci.yml",
    }
    deployment_dir = output_dir / "src" / "modules" / "free" / "essentials" / "deployment"
    health_dir = output_dir / "src" / "health"
    module_expected = {
        deployment_dir / "deployment.service.ts",
        deployment_dir / "deployment.controller.ts",
        deployment_dir / "deployment.module.ts",
        health_dir / "deployment-health.controller.ts",
        health_dir / "deployment-health.module.ts",
    }

    for artefact in (*root_expected, *module_expected):
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} should not be empty"

    controller_src = (deployment_dir / "deployment.controller.ts").read_text()
    assert (
        "@Controller('deployment')" in controller_src
        or '@Controller("deployment")' in controller_src
    ), "Controller should expose deployment routes"
    assert "@Get('plan')" in controller_src or '@Get("plan")' in controller_src

    health_controller_src = (health_dir / "deployment-health.controller.ts").read_text()
    assert (
        "@Controller('health')" in health_controller_src
        or '@Controller("health")' in health_controller_src
    ), "Health controller should mount under health route"
    assert (
        "@Get('deployment')" in health_controller_src
        or '@Get("deployment")' in health_controller_src
    ), "Health controller should expose deployment health endpoint"
