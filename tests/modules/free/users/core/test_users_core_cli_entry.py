from pathlib import Path

import pytest

from modules.free.users.users_core import generate
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

    users_core_dir = output_dir / "src" / "modules" / "free" / "users" / "users_core"
    expected = {
        users_core_dir / "users-core.service.ts",
        users_core_dir / "users-core.controller.ts",
        users_core_dir / "users-core.module.ts",
        users_core_dir / "index.ts",
    }

    for artefact in expected:
        assert artefact.exists(), f"Expected {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} should not be empty"

    controller_src = (users_core_dir / "users-core.controller.ts").read_text()
    assert (
        "@Controller('users-core')" in controller_src
        or '@Controller("users-core")' in controller_src
    ), "Controller should route under users-core"
