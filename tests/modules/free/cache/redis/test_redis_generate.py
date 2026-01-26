import importlib.util
from pathlib import Path

import pytest

from modules.free.cache.redis.generate import RedisModuleGenerator

MASKED_PORT = 6380
MASKED_DB = 2
MASKED_ATTEMPTS = 5
MASKED_TTL = 7200


@pytest.fixture(scope="module")
def generator() -> RedisModuleGenerator:
    return RedisModuleGenerator()


def _render(
    generator: RedisModuleGenerator, framework: str, target_dir: Path
) -> tuple[Path, dict[str, object], dict[str, object]]:
    config = generator.load_module_config()
    base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
    renderer = generator.create_renderer()
    jinja_env = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
    if jinja_env is None:
        pytest.skip("jinja2 is required to render Redis templates")

    generator.generate_vendor_files(config, target_dir, renderer, base_context)
    generator.generate_variant_files(framework, target_dir, renderer, base_context)

    return target_dir, config, base_context


def test_fastapi_generation_produces_wrappers(
    generator: RedisModuleGenerator, tmp_path: Path
) -> None:
    output_dir, config, base_context = _render(generator, "fastapi", tmp_path)

    vendor_root = output_dir / ".rapidkit" / "vendor" / config["name"] / config["version"]
    vendor_cfg = config["generation"]["vendor"]
    vendor_expected = {
        vendor_root / Path(entry["relative"]) for entry in vendor_cfg.get("files", [])
    }
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated vendor file {artefact} is empty"

        relative_path = artefact.relative_to(vendor_root)
        if relative_path == Path("src/modules/free/cache/redis/client.py"):
            for expected_symbol in (
                "class RedisClient",
                "class RedisSyncClient",
                "async def get_redis",
                "def get_redis_sync",
                "async def redis_dependency",
                "def register_redis",
                "def get_redis_metadata",
            ):
                assert expected_symbol in contents, f"Vendor client missing {expected_symbol}"
        elif relative_path == Path("src/modules/free/cache/redis/runtime.py"):
            assert "def describe_cache" in contents
            assert "def list_features" in contents
        elif relative_path == Path("src/modules/free/cache/redis/redis_types.py"):
            assert "class RedisHealthSnapshot" in contents
            assert "def as_dict" in contents
        elif relative_path == Path("src/health/redis.py"):
            assert "async def redis_health_check" in contents
            assert "def register_redis_health" in contents
        elif relative_path == Path("src/modules/free/cache/redis/__init__.py"):
            assert "__all__" in contents
            assert "get_redis" in contents
            assert "register_redis" in contents
        elif relative_path == Path("nestjs/configuration.js"):
            assert "module.exports" in contents
            assert "loadConfiguration" in contents

    fastapi_cfg = config["generation"]["variants"]["fastapi"]
    fastapi_expected = {
        output_dir / Path(entry["output"]) for entry in fastapi_cfg.get("files", [])
    }

    # FastAPI generation enforces canonical health layout under `src/health/<module>.py`
    # and removes any module-local `src/modules/**/health/**` artefacts.
    fastapi_expected.discard(output_dir / "src/modules/free/cache/redis/health/__init__.py")
    fastapi_expected.discard(output_dir / "src/modules/free/cache/redis/health/redis.py")
    fastapi_expected.add(output_dir / "src/health/redis.py")
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated FastAPI file {artefact} is empty"

        relative_path = artefact.relative_to(output_dir)
        if relative_path == Path("src/modules/free/cache/redis/client.py"):
            for expected_symbol in (
                "def _load_vendor_module",
                "def refresh_vendor_module",
                "AsyncRedis = _resolve_export",
                "register_redis = _resolve_export",
                "def get_redis_metadata",
            ):
                assert (
                    expected_symbol in contents
                ), f"FastAPI client wrapper missing {expected_symbol}"
        elif relative_path == Path("src/modules/free/cache/redis/__init__.py"):
            assert "from .client import" in contents
            assert "__all__" in contents
        elif relative_path == Path("src/modules/free/cache/redis/redis.py"):
            assert "from src.modules.free.cache.redis.client import" in contents
            assert "from src.modules.free.cache.redis.runtime import" in contents
            assert "describe_cache" in contents
            assert "list_features" in contents
        elif relative_path == Path("src/health/redis.py"):
            assert "def build_health_router" in contents
            assert "register_redis_health" in contents
        elif relative_path == Path("src/modules/free/cache/redis/routers/redis.py"):
            assert (
                'APIRouter(prefix="/redis"' in contents or "APIRouter(prefix='/redis'" in contents
            )
            for route in ("/metadata", "/ping", "/client"):
                tokens = (
                    f"@router.get('{route}'",
                    f'@router.get("{route}"',
                )
                assert any(
                    token in contents for token in tokens
                ), f"FastAPI router should expose {route}"


def test_nestjs_generation_outputs_configuration(
    generator: RedisModuleGenerator, tmp_path: Path
) -> None:
    output_dir, config, _context = _render(generator, "nestjs", tmp_path)

    nest_cfg = config["generation"]["variants"]["nestjs"]
    nest_expected = {output_dir / Path(entry["output"]) for entry in nest_cfg.get("files", [])}

    # NestJS generation moves `*.health.ts` artefacts into `src/health/`.
    nest_expected.discard(output_dir / "src/modules/free/cache/redis/redis.health.ts")
    nest_expected.add(output_dir / "src/health/redis.health.ts")

    for artefact in nest_expected:
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated NestJS file {artefact} is empty"

        relative_path = artefact.relative_to(output_dir)
        if relative_path == Path("src/modules/free/cache/redis/configuration.ts"):
            assert 'registerAs("redis"' in contents or "registerAs('redis'" in contents
            assert "const buildUrl" in contents
        elif relative_path == Path("src/modules/free/cache/redis/redis.service.ts"):
            for expected_feature in (
                "class RedisService",
                "implements OnModuleInit",
                "OnModuleInit, OnModuleDestroy",
                "async onModuleInit",
                "async ping",
                "async describeClient",
                "describeCache()",
                "DB_REDIS_VENDOR_MODULE",
                "new Redis",
            ):
                assert expected_feature in contents, f"Redis service missing {expected_feature}"
        elif relative_path == Path("src/modules/free/cache/redis/redis.module.ts"):
            assert "@Module" in contents
            assert "ConfigModule.forFeature" in contents
            assert "RedisController" in contents
            assert "RedisService" in contents
        elif relative_path == Path("src/modules/free/cache/redis/redis.controller.ts"):
            assert (
                "@Controller('redis')" in contents or '@Controller("redis")' in contents
            ), "Redis controller should expose redis route"
            for route in ("metadata", "ping", "client"):
                assert (
                    f"@Get('{route}')" in contents or f'@Get("{route}")' in contents
                ), f"Redis controller missing {route} route"
            assert "ServiceUnavailableException" in contents
        elif relative_path == Path("src/modules/free/cache/redis/index.ts"):
            assert "export { default as redisConfiguration }" in contents
        elif relative_path == Path("src/modules/free/cache/redis/redis.validation.ts"):
            assert "redisValidationSchema" in contents
            assert "Joi.object" in contents


def test_vendor_metadata_masks_password(
    generator: RedisModuleGenerator,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir, config, base_context = _render(generator, "fastapi", tmp_path)

    vendor_root = output_dir / ".rapidkit" / "vendor" / config["name"] / config["version"]
    vendor_client = vendor_root / base_context["rapidkit_vendor_client_relative"]

    spec = importlib.util.spec_from_file_location("redis_vendor_client", vendor_client)
    assert spec and spec.loader, "Vendor runtime spec should be loadable"

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setenv(
        "REDIS_URL",
        f"redis://user:secret@cache.internal:{MASKED_PORT}/{MASKED_DB}",
    )
    monkeypatch.setenv("REDIS_PRECONNECT", "true")
    monkeypatch.setenv("REDIS_CONNECT_RETRIES", str(MASKED_ATTEMPTS))
    monkeypatch.setenv("REDIS_CACHE_TTL", str(MASKED_TTL))

    metadata = module.get_redis_metadata()

    assert metadata["url"] == f"redis://user:***@cache.internal:{MASKED_PORT}/{MASKED_DB}"

    connection = metadata["connection"]
    assert connection["host"] == "cache.internal"
    assert connection["port"] == MASKED_PORT
    assert connection["db"] == MASKED_DB
    assert connection["use_tls"] is False

    retry = metadata["retry"]
    assert retry["preconnect"] is True
    assert retry["attempts"] == MASKED_ATTEMPTS
    assert retry["backoff_base"] == module.DEFAULTS["connect_backoff_base"]

    assert metadata["cache_ttl"] == MASKED_TTL
