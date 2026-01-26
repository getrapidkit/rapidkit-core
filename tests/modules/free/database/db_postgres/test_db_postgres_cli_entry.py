from pathlib import Path

import pytest

from modules.free.database.db_postgres import generate
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

    module_root = output_dir / "src" / "modules" / "free" / "database" / "db_postgres"
    service_file = module_root / "postgres.service.ts"
    controller_file = output_dir / "src" / "health" / "postgres-health.controller.ts"
    module_file = output_dir / "src" / "health" / "postgres-health.module.ts"
    db_module_file = module_root / "postgres.module.ts"
    config_file = output_dir / "nestjs" / "configuration.js"

    for artefact in (service_file, controller_file, module_file, db_module_file, config_file):
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} should not be empty"

    controller_src = controller_file.read_text()
    assert (
        "@Controller('api/health/module')" in controller_src
        or '@Controller("api/health/module")' in controller_src
    ), "Controller should mount under health route namespace"
    assert "@Get('postgres')" in controller_src or '@Get("postgres")' in controller_src
    assert "ServiceUnavailableException" in controller_src

    module_src = module_file.read_text()
    assert "DatabasePostgresModule" in module_src

    db_module_src = db_module_file.read_text()
    assert "ConfigModule" in db_module_src
