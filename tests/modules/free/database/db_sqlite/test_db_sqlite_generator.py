"""Generator-level guardrails for Db Sqlite."""

from __future__ import annotations

from pathlib import Path


def test_generate_vendor_and_variant_outputs(
    db_sqlite_generator,
    module_config,
    tmp_path: Path,
) -> None:
    renderer = db_sqlite_generator.create_renderer()
    base_context = db_sqlite_generator.apply_base_context_overrides(
        db_sqlite_generator.build_base_context(module_config)
    )

    db_sqlite_generator.generate_vendor_files(module_config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
        / "src"
    )
    vendor_expected = {
        vendor_root / "modules" / "free" / "database" / "db_sqlite" / "db_sqlite.py",
        vendor_root / "health" / "db_sqlite.py",
        vendor_root / "modules" / "free" / "database" / "db_sqlite" / "types" / "db_sqlite.py",
        vendor_root.parent / "nestjs" / "configuration.js",
    }
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated vendor file {artefact} is empty"

        relative_path = artefact.relative_to(vendor_root.parent)
        if relative_path == Path("src/modules/free/database/db_sqlite/db_sqlite.py"):
            for expected_symbol in (
                "class DbSqliteConfig",
                "class DbSqlite",
                "class SqliteConnectionManager",
                "def _normalize_database_path",
                "def _should_use_uri",
                "def execute(",
                "def executemany(",
                "def list_tables",
                "def health_check",
            ):
                assert expected_symbol in contents, f"Vendor runtime missing {expected_symbol}"
        elif relative_path == Path("src/health/db_sqlite.py"):
            assert "def perform_health_check" in contents
        elif relative_path == Path("src/modules/free/database/db_sqlite/types/db_sqlite.py"):
            for expected_type in (
                "class SqliteHealthReport",
                "class SqliteQueryResult",
                "class SqliteTableInfo",
            ):
                assert expected_type in contents
        elif relative_path == Path("nestjs/configuration.js"):
            assert "module.exports" in contents
            assert "loadConfiguration" in contents

    db_sqlite_generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    fastapi_config_file = tmp_path / "config" / "database" / "db_sqlite.yaml"
    fastapi_integration_test = (
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "database"
        / "test_db_sqlite_integration.py"
    )
    fastapi_expected = {
        tmp_path / "src" / "modules" / "free" / "database" / "db_sqlite" / "db_sqlite.py",
        tmp_path / "src" / "health" / "db_sqlite.py",
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "database"
        / "db_sqlite"
        / "routers"
        / "db_sqlite.py",
        fastapi_config_file,
        fastapi_integration_test,
    }
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated FastAPI file {artefact} is empty"

        relative_path = artefact.relative_to(tmp_path)
        if relative_path == Path("src/modules/free/database/db_sqlite/db_sqlite.py"):
            assert 'DbSqlite = _resolve_export("DbSqlite")' in contents
            assert 'DbSqliteConfig = _resolve_export("DbSqliteConfig")' in contents
            assert "def register_fastapi" in contents
            assert "app.include_router" in contents
        elif relative_path == Path("src/health/db_sqlite.py"):
            assert "def build_health_router" in contents
            assert "register_db_sqlite_health" in contents
        elif relative_path == Path("src/modules/free/database/db_sqlite/routers/db_sqlite.py"):
            for expected_feature in (
                "def get_runtime_dependency",
                "def build_router",
                "router = APIRouter",
                '@router.get("/health"',
                '@router.get("/tables"',
            ):
                assert expected_feature in contents, f"FastAPI router missing {expected_feature}"
        elif relative_path == Path("config/database/db_sqlite.yaml"):
            assert contents.startswith("# Default SQLite configuration")
            assert "sqlite:" in contents
            for expected_key in ("database:", "pool:", "pragmas:"):
                assert expected_key in contents, f"Config missing {expected_key}"
        elif relative_path == Path(
            "tests/modules/integration/database/test_db_sqlite_integration.py"
        ):
            assert "pytest.mark.integration" in contents
            assert "register_fastapi" in contents
            assert "SQLITE_AVAILABLE" in contents

    db_sqlite_generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)
    nest_root = tmp_path / "src" / "modules" / "free" / "database" / "db_sqlite"
    service_file = nest_root / "db-sqlite.service.ts"
    controller_file = nest_root / "db-sqlite.controller.ts"
    module_file = nest_root / "db-sqlite.module.ts"
    configuration_file = nest_root / "db-sqlite.configuration.ts"
    health_controller_file = tmp_path / "src" / "health" / "db-sqlite-health.controller.ts"
    health_module_file = tmp_path / "src" / "health" / "db-sqlite-health.module.ts"
    integration_spec = (
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "database"
        / "db_sqlite.integration.spec.ts"
    )

    for artefact in (
        service_file,
        controller_file,
        module_file,
        configuration_file,
        health_controller_file,
        health_module_file,
        integration_spec,
    ):
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated NestJS file {artefact} is empty"

        if artefact == service_file:
            assert "class DbSqliteService" in contents
            assert "better-sqlite3" in contents
            assert "getHealthPayload" in contents
            assert "listTables" in contents
            assert "DB_SQLITE_VENDOR_MODULE" in contents
        elif artefact == controller_file:
            assert (
                "@Controller('db-sqlite')" in contents or '@Controller("db-sqlite")' in contents
            ), "NestJS controller should declare db-sqlite route"
            assert "@Get('health')" in contents or '@Get("health")' in contents
            assert "@Get('tables')" in contents or '@Get("tables")' in contents
            assert "ServiceUnavailableException" in contents
        elif artefact == module_file:
            assert "@Module" in contents
            assert "DbSqliteService" in contents
            assert "DbSqliteController" in contents
            assert "ConfigModule" in contents
        elif artefact == configuration_file:
            assert "registerAs" in contents
            assert "dbSqliteConfiguration" in contents
            assert "retryAttempts" in contents
        elif artefact == health_controller_file:
            assert (
                "@Controller('api/health/module')" in contents
                or '@Controller("api/health/module")' in contents
            )
            assert "@Get('db-sqlite')" in contents or '@Get("db-sqlite")' in contents
            assert "ServiceUnavailableException" in contents
        elif artefact == health_module_file:
            assert "@Module" in contents
            assert "DbSqliteHealthController" in contents
            assert "DbSqliteModule" in contents
        elif artefact == integration_spec:
            assert "describe('DbSqliteModule" in contents
            assert "get('/api/health/module/db-sqlite')" in contents
            assert "DbSqliteService" in contents


def test_core_files_exist(module_root: Path) -> None:
    expected = [
        "module.yaml",
        "generate.py",
        "overrides.py",
        "config/base.yaml",
        "config/snippets.yaml",
        "module.verify.json",
        ".module_state.json",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path


def test_framework_files_exist(module_root: Path) -> None:
    expected = [
        "frameworks/fastapi.py",
        "frameworks/nestjs.py",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path


def test_templates_exist(module_root: Path) -> None:
    expected = [
        "templates/base/db_sqlite.py.j2",
        "templates/base/db_sqlite_health.py.j2",
        "templates/base/db_sqlite_types.py.j2",
        "templates/variants/fastapi/db_sqlite.py.j2",
        "templates/variants/fastapi/db_sqlite_routes.py.j2",
        "templates/variants/fastapi/db_sqlite_health.py.j2",
        "templates/variants/fastapi/db_sqlite_config.yaml.j2",
        "templates/variants/nestjs/db_sqlite.service.ts.j2",
        "templates/variants/nestjs/db_sqlite.controller.ts.j2",
        "templates/variants/nestjs/db_sqlite.module.ts.j2",
        "templates/variants/nestjs/db_sqlite.configuration.ts.j2",
        "templates/variants/nestjs/db_sqlite.health.controller.ts.j2",
        "templates/variants/nestjs/db_sqlite.health.module.ts.j2",
        "templates/vendor/nestjs/configuration.js.j2",
        "templates/tests/integration/test_db_sqlite_integration.j2",
        "templates/tests/integration/db_sqlite.integration.spec.ts.j2",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path
