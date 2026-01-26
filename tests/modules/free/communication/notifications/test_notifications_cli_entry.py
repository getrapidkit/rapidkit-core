from pathlib import Path

import pytest

from modules.free.communication.notifications import generate
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

    notifications_dir = output_dir / "src" / "modules" / "free" / "communication" / "notifications"
    expected = {
        notifications_dir / "notifications.service.ts",
        notifications_dir / "notifications.controller.ts",
        notifications_dir / "notifications.module.ts",
    }

    for artefact in expected:
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} should not be empty"

    controller_src = (notifications_dir / "notifications.controller.ts").read_text()
    assert (
        "@Controller('notifications')" in controller_src
        or '@Controller("notifications")' in controller_src
    ), "Controller should expose notifications routes"
    assert "@Get('metadata')" in controller_src or '@Get("metadata")' in controller_src
    assert "@Get('features')" in controller_src or '@Get("features")' in controller_src
    assert "@Post('send')" in controller_src or '@Post("send")' in controller_src
