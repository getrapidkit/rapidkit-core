from pathlib import Path

import pytest

from modules.free.auth.session import generate
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

    session_dir = output_dir / "src" / "modules" / "free" / "auth" / "session"
    expected = {
        session_dir / "session.service.ts",
        session_dir / "session.controller.ts",
        session_dir / "session.module.ts",
        session_dir / "configuration.ts",
        session_dir / "index.ts",
        session_dir / "config" / "session.validation.ts",
    }

    for artefact in expected:
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} should not be empty"

    controller_src = (session_dir / "session.controller.ts").read_text()
    assert (
        "@Controller('sessions')" in controller_src or '@Controller("sessions")' in controller_src
    ), "Controller should expose sessions routes"
    assert "@Get('metadata')" in controller_src or '@Get("metadata")' in controller_src
    assert "@Get('features')" in controller_src or '@Get("features")' in controller_src
    assert "@Post()" in controller_src
    assert "@Post('refresh')" in controller_src or '@Post("refresh")' in controller_src
    assert "@Post('verify')" in controller_src or '@Post("verify")' in controller_src
    assert "@Delete(':sessionId')" in controller_src or '@Delete(":sessionId")' in controller_src
