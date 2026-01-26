"""Tests for db_postgres module generator."""

from __future__ import annotations

import os
import tempfile
from importlib import import_module
from pathlib import Path
from typing import cast


def _read_text(path: Path) -> str:
    """Read file contents with UTF-8 encoding across platforms."""

    return path.read_text(encoding="utf-8").strip()


def test_generate_vendor_and_variant_outputs(
    db_postgres_generator,
    module_config,
    tmp_path: Path,
) -> None:
    renderer = db_postgres_generator.create_renderer()
    base_context = db_postgres_generator.apply_base_context_overrides(
        db_postgres_generator.build_base_context(module_config)
    )

    db_postgres_generator.generate_vendor_files(module_config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
        / "src"
    )
    vendor_expected = {
        vendor_root / "modules" / "free" / "database" / "db_postgres" / "postgres.py",
        vendor_root / "health" / "postgres.py",
    }
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        contents = _read_text(artefact)
        assert contents, f"Generated vendor file {artefact} is empty"
        relative_path = artefact.relative_to(vendor_root)
        if relative_path == Path("modules/free/database/db_postgres/postgres.py"):
            for expected_symbol in (
                "class DatabasePostgresConfig",
                "def build_default_config",
                "def get_engine_config",
                "def validate_config",
            ):
                assert (
                    expected_symbol in contents
                ), f"Vendor postgres module missing {expected_symbol}"

    db_postgres_generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    fastapi_expected = {
        tmp_path / "src" / "modules" / "free" / "database" / "db_postgres" / "postgres.py",
        tmp_path / "src" / "health" / "postgres.py",
        tmp_path / "config" / "database" / "postgres.yaml",
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "database"
        / "test_postgres_integration.py",
    }
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        contents = _read_text(artefact)
        assert contents, f"Generated FastAPI file {artefact} is empty"
        relative_path = artefact.relative_to(tmp_path)

        if relative_path == Path("src/modules/free/database/db_postgres/postgres.py"):
            for expected_feature in (
                "async_engine = create_async_engine",
                "sync_engine = create_engine",
                "AsyncSessionLocal = async_sessionmaker",
                "SyncSessionLocal = sessionmaker",
                "async def get_postgres_db",
                "def get_sync_db",
                "@asynccontextmanager",
                "@contextmanager",
                "async def check_postgres_connection",
                "def check_postgres_connection_sync",
                "async def get_pool_status",
                "async def close_async_engine",
                "def close_sync_engine",
                "async def initialize_database",
                "def get_database_url",
            ):
                assert (
                    expected_feature in contents
                ), f"FastAPI postgres runtime missing {expected_feature}"
        elif relative_path == Path("src/health/postgres.py"):
            assert "def build_health_router" in contents
            assert "register_postgres_health" in contents
        elif relative_path == Path("config/database/postgres.yaml"):
            assert "postgres:" in contents
            for expected_key in (
                "enabled:",
                "url:",
                "pool:",
                "metadata:",
            ):
                assert expected_key in contents, f"Config template missing {expected_key}"
        elif relative_path == Path(
            "tests/modules/integration/database/test_postgres_integration.py"
        ):
            assert "pytest.mark.integration" in contents
            assert "register_postgres_health" in contents

    db_postgres_generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)
    service_file = (
        tmp_path / "src" / "modules" / "free" / "database" / "db_postgres" / "postgres.service.ts"
    )
    db_module_file = (
        tmp_path / "src" / "modules" / "free" / "database" / "db_postgres" / "postgres.module.ts"
    )
    controller_file = tmp_path / "src" / "health" / "postgres-health.controller.ts"
    module_file = tmp_path / "src" / "health" / "postgres-health.module.ts"
    config_file = tmp_path / "nestjs" / "configuration.js"
    integration_spec = (
        tmp_path / "tests" / "modules" / "integration" / "database" / "postgres.integration.spec.ts"
    )

    for artefact in (
        service_file,
        db_module_file,
        controller_file,
        module_file,
        config_file,
        integration_spec,
    ):
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        contents = _read_text(artefact)
        assert contents, f"Generated NestJS file {artefact} is empty"

        if artefact == service_file:
            assert "class DatabasePostgresService" in contents
            assert "Pool" in contents
            assert "checkHealth" in contents
            assert "runInTransaction" in contents
            assert "getPoolStatus" in contents
            assert "DATABASE_POSTGRES_MODULE" in contents
        elif artefact == db_module_file:
            assert "@Module" in contents
            assert "DatabasePostgresService" in contents
            assert "ConfigModule" in contents
        elif artefact == controller_file:
            assert (
                "@Controller('api/health/module')" in contents
                or '@Controller("api/health/module")' in contents
            ), "NestJS controller should declare health route namespace"
            assert (
                "@Get('postgres')" in contents or '@Get("postgres")' in contents
            ), "NestJS controller should expose PostgreSQL health endpoint"
            assert "ServiceUnavailableException" in contents
        elif artefact == module_file:
            assert "@Module" in contents
            assert "DatabasePostgresModule" in contents
            assert "DatabasePostgresHealthController" in contents
        elif artefact == config_file:
            assert "module.exports" in contents
            assert "loadConfiguration" in contents
        elif artefact == integration_spec:
            assert "describe('DatabasePostgresModule" in contents
            assert "get('/api/health/module/postgres')" in contents
            assert "DatabasePostgresService" in contents


MODULE_ROOT = (
    Path(cast(str, import_module("modules.free.database.db_postgres").__file__)).resolve().parent
)
PROJECT_ROOT = MODULE_ROOT.parents[4]


def _project_root() -> Path:
    return PROJECT_ROOT


def test_generator_entrypoint() -> None:
    """Smoky assertion ensuring generator is importable."""
    assert MODULE_ROOT.exists()

    # Check critical files exist
    assert (MODULE_ROOT / "module.yaml").exists()
    assert (MODULE_ROOT / "generate.py").exists()
    assert (MODULE_ROOT / "templates").exists()


def test_module_yaml_structure() -> None:
    """Verify module.yaml has required structure."""
    import yaml

    with open(MODULE_ROOT / "module.yaml") as f:
        config = yaml.safe_load(f)

    assert config["name"] == "db_postgres"
    assert "version" in config
    assert "dependencies" in config
    assert "fastapi" in config["dependencies"]

    # Check FastAPI dependencies
    fastapi_deps = config["dependencies"]["fastapi"]
    dep_names = [d["name"] for d in fastapi_deps]
    assert "asyncpg" in dep_names
    assert "sqlalchemy" in dep_names
    assert any("psycopg" in name for name in dep_names)


def test_templates_exist() -> None:
    """Verify all required templates exist."""
    templates_dir = MODULE_ROOT / "templates"

    # Check base templates
    assert (templates_dir / "base" / "postgres.py.j2").exists()

    # Check variant templates
    assert (templates_dir / "variants" / "fastapi" / "postgres.py.j2").exists()
    assert (templates_dir / "variants" / "fastapi" / "postgres_config.yaml.j2").exists()
    assert (templates_dir / "variants" / "nestjs" / "postgres.service.ts.j2").exists()
    assert (templates_dir / "variants" / "nestjs" / "postgres.module.ts.j2").exists()

    # Check test templates
    assert (templates_dir / "tests" / "integration" / "test_postgres_integration.j2").exists()
    assert (templates_dir / "tests" / "integration" / "postgres.integration.spec.ts.j2").exists()


def test_generator_imports() -> None:
    """Test that generator module has required components."""
    # Check generate.py exists and has expected structure
    generate_file = MODULE_ROOT / "generate.py"
    assert generate_file.exists()

    content = generate_file.read_text(encoding="utf-8")
    assert "class DbPostgresModuleGenerator" in content
    assert "def main(" in content
    assert "BaseModuleGenerator" in content


def test_generate_fastapi_variant() -> None:
    """Test FastAPI variant generation produces expected files."""
    import subprocess
    import sys

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir)

        # Run generator as subprocess to avoid import issues
        env = os.environ.copy()
        project_root = _project_root()
        src_path = project_root / "src"
        extra_paths = [str(project_root), str(src_path)]
        existing_pythonpath = env.get("PYTHONPATH")
        if existing_pythonpath:
            extra_paths.append(existing_pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(extra_paths)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "modules.free.database.db_postgres.generate",
                "fastapi",
                str(target),
            ],
            check=False,
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Generator failed: {result.stderr}"

        # Check generated files
        postgres_file = (
            target / "src" / "modules" / "free" / "database" / "db_postgres" / "postgres.py"
        )
        assert postgres_file.exists(), "postgres.py should be generated"

        # Check content
        content = postgres_file.read_text(encoding="utf-8")
        assert "from modules.free.essentials.logging.logging import get_logger" in content
        assert "runtime.core.logging" not in content
        assert "postgresql+asyncpg://" in content
        assert "postgresql+psycopg://" in content
        assert "AsyncSessionLocal" in content
        assert "SyncSessionLocal" in content
