"""Generator-level guardrails for Db Mongo."""

from __future__ import annotations

from pathlib import Path


def test_generate_vendor_and_variant_outputs(
    db_mongo_generator,
    module_config,
    tmp_path: Path,
) -> None:
    renderer = db_mongo_generator.create_renderer()
    base_context = db_mongo_generator.apply_base_context_overrides(
        db_mongo_generator.build_base_context(module_config)
    )

    db_mongo_generator.generate_vendor_files(module_config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
    )
    vendor_base = vendor_root / "src" / "modules" / "free" / "database" / "db_mongo"
    vendor_expected = {
        vendor_base / "db_mongo.py",
        vendor_root / "src" / "health" / "db_mongo.py",
        vendor_base / "types" / "db_mongo.py",
        vendor_root / "nestjs" / "configuration.js",
    }
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated vendor file {artefact} is empty"

        relative_path = artefact.relative_to(vendor_root)
        if relative_path == Path("src/modules/free/database/db_mongo/db_mongo.py"):
            for expected_symbol in (
                "class DbMongoConfig",
                "class DbMongo",
                "class DbMongoClientFactory",
                "class DbMongoDependencyError",
                "def _build_client_kwargs",
                "async def health_check",
                "async def ping",
            ):
                assert expected_symbol in contents, f"Vendor runtime missing {expected_symbol}"
        elif relative_path == Path("src/health/db_mongo.py"):
            assert "async def perform_health_check" in contents
            assert "build_health_report" in contents
            assert "MongoReplicaState" in contents
        elif relative_path == Path("src/modules/free/database/db_mongo/types/db_mongo.py"):
            for expected_type in (
                "class MongoHealthReport",
                "class MongoClusterMetrics",
                "class MongoReplicaState",
                "def build_health_report",
            ):
                assert expected_type in contents
        elif relative_path == Path("nestjs/configuration.js"):
            assert "module.exports" in contents
            assert "loadConfiguration" in contents

    db_mongo_generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    fastapi_expected = {
        tmp_path / "src" / "modules" / "free" / "database" / "db_mongo" / "db_mongo.py",
        tmp_path / "src" / "health" / "db_mongo.py",
        tmp_path / "src" / "modules" / "free" / "database" / "db_mongo" / "routers" / "db_mongo.py",
        tmp_path / "config" / "database" / "db_mongo.yaml",
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "database"
        / "test_db_mongo_integration.py",
    }
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated FastAPI file {artefact} is empty"

        relative_path = artefact.relative_to(tmp_path)
        if relative_path == Path("src/modules/free/database/db_mongo/db_mongo.py"):
            assert 'DbMongo = _resolve_export("DbMongo")' in contents
            assert "def register_fastapi" in contents
            assert "app.include_router" in contents
        elif relative_path == Path("src/health/db_mongo.py"):
            assert "def build_health_router" in contents
            assert "register_db_mongo_health" in contents
        elif relative_path == Path("src/modules/free/database/db_mongo/routers/db_mongo.py"):
            for expected_feature in (
                "async def get_runtime_dependency",
                "def build_router",
                "router = APIRouter",
                '@router.get("/health"',
                '@router.get("/info"',
            ):
                assert expected_feature in contents, f"FastAPI router missing {expected_feature}"
        elif relative_path == Path("config/database/db_mongo.yaml"):
            assert "mongo:" in contents
            for expected_key in (
                "connection:",
                "pool:",
                "security:",
                "health:",
            ):
                assert expected_key in contents, f"Config missing {expected_key}"
        elif relative_path == Path(
            "tests/modules/integration/database/test_db_mongo_integration.py"
        ):
            assert "pytest.mark.integration" in contents
            assert "register_fastapi" in contents

    db_mongo_generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)
    service_file = (
        tmp_path / "src" / "modules" / "free" / "database" / "db_mongo" / "db-mongo.service.ts"
    )
    controller_file = (
        tmp_path / "src" / "modules" / "free" / "database" / "db_mongo" / "db-mongo.controller.ts"
    )
    module_file = (
        tmp_path / "src" / "modules" / "free" / "database" / "db_mongo" / "db-mongo.module.ts"
    )
    configuration_file = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "database"
        / "db_mongo"
        / "db-mongo.configuration.ts"
    )
    health_controller_file = tmp_path / "src" / "health" / "db-mongo-health.controller.ts"
    health_module_file = tmp_path / "src" / "health" / "db-mongo-health.module.ts"
    integration_spec = (
        tmp_path / "tests" / "modules" / "integration" / "database" / "db_mongo.integration.spec.ts"
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
            for expected_feature in (
                "class DbMongoService",
                "implements OnModuleInit",
                "OnModuleInit, OnModuleDestroy",
                "async checkHealth",
                "async getServerInfo",
                "getMetadata()",
                "private async ensureClient",
                "MongoClient",
                "DB_MONGO_VENDOR_MODULE",
            ):
                assert expected_feature in contents, f"NestJS service missing {expected_feature}"
        elif artefact == controller_file:
            assert (
                "@Controller('db-mongo')" in contents or '@Controller("db-mongo")' in contents
            ), "NestJS controller should declare db-mongo route"
            assert "@Get('health')" in contents or '@Get("health")' in contents
            assert "@Get('info')" in contents or '@Get("info")' in contents
            assert "ServiceUnavailableException" in contents
        elif artefact == module_file:
            assert "@Module" in contents
            assert "DbMongoService" in contents
            assert "DbMongoController" in contents
            assert "ConfigModule" in contents
        elif artefact == configuration_file:
            assert "registerAs" in contents
            assert "dbMongoConfiguration" in contents
            assert "connection:" in contents
        elif artefact == health_controller_file:
            assert (
                "@Controller('api/health/module')" in contents
                or '@Controller("api/health/module")' in contents
            )
            assert "@Get('db-mongo')" in contents or '@Get("db-mongo")' in contents
            assert "ServiceUnavailableException" in contents
        elif artefact == health_module_file:
            assert "@Module" in contents
            assert "DbMongoHealthController" in contents
            assert "DbMongoModule" in contents
        elif artefact == integration_spec:
            assert "describe('DbMongoModule" in contents
            assert "get('/api/health/module/db-mongo')" in contents
            assert "DbMongoService" in contents


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
        "templates/base/db_mongo.py.j2",
        "templates/base/db_mongo_health.py.j2",
        "templates/base/db_mongo_types.py.j2",
        "templates/variants/fastapi/db_mongo.py.j2",
        "templates/variants/fastapi/db_mongo_routes.py.j2",
        "templates/variants/fastapi/db_mongo_health.py.j2",
        "templates/variants/fastapi/db_mongo_config.yaml.j2",
        "templates/variants/nestjs/db_mongo.service.ts.j2",
        "templates/variants/nestjs/db_mongo.controller.ts.j2",
        "templates/variants/nestjs/db_mongo.module.ts.j2",
        "templates/variants/nestjs/db_mongo.configuration.ts.j2",
        "templates/variants/nestjs/db_mongo.health.controller.ts.j2",
        "templates/variants/nestjs/db_mongo.health.module.ts.j2",
        "templates/vendor/nestjs/configuration.js.j2",
        "templates/snippets/db_mongo_env.snippet.j2",
        "templates/snippets/db_mongo_settings_fields.snippet.j2",
        "templates/snippets/db_mongo_settings_fields_nestjs.snippet.j2",
        "templates/tests/integration/db_mongo.integration.spec.ts.j2",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path
