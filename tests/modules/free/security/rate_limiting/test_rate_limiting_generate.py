import asyncio
import json
import os
import sys
from importlib import import_module, util as import_util
from pathlib import Path

import pytest

from modules.free.security.rate_limiting import generate as rate_generate


@pytest.fixture(scope="module")
def rate_limiting_runtime(tmp_path_factory: pytest.TempPathFactory):
    generator = rate_generate.RateLimitingModuleGenerator()
    renderer = generator.create_renderer()
    jinja_env = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
    if jinja_env is None:
        pytest.skip("jinja2 is required to render Rate Limiting templates")

    config = generator.load_module_config()
    base_context = generator.apply_base_context_overrides(generator.build_base_context(config))

    target_dir = tmp_path_factory.mktemp("rate_limiting_generated")
    generator.generate_vendor_files(config, target_dir, renderer, base_context)

    vendor_cfg = config["generation"]["vendor"]
    runtime_rel = None
    for entry in vendor_cfg.get("files", []):
        if not isinstance(entry, dict):
            continue
        rel = entry.get("relative")
        if isinstance(rel, str) and rel.endswith("/rate_limiting.py"):
            runtime_rel = rel
            break
    assert runtime_rel is not None, "Vendor runtime relative path not found in module.yaml"

    runtime_path = (
        target_dir
        / ".rapidkit"
        / "vendor"
        / base_context["rapidkit_vendor_module"]
        / str(base_context["rapidkit_vendor_version"])
        / runtime_rel
    )
    assert runtime_path.exists(), f"Expected generated vendor runtime at {runtime_path}"

    spec = import_util.spec_from_file_location("rapidkit_test_rate_limiting_runtime", runtime_path)
    if spec is None or spec.loader is None:
        pytest.fail("Unable to load generated rate limiting runtime module")
    module = import_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("variant", ["fastapi", "nestjs"], ids=["fastapi", "nestjs"])
def test_generator_materialises_expected_artifacts(tmp_path: Path, variant: str) -> None:
    generator = rate_generate.RateLimitingModuleGenerator()
    renderer = generator.create_renderer()
    jinja_env = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
    if jinja_env is None:
        pytest.skip("jinja2 is required to render Rate Limiting templates")

    config = generator.load_module_config()
    base_context = generator.apply_base_context_overrides(generator.build_base_context(config))

    target_dir = tmp_path / "generated"
    target_dir.mkdir()

    generator.generate_vendor_files(config, target_dir, renderer, base_context)
    generator.generate_variant_files(variant, target_dir, renderer, base_context)

    vendor_cfg = config["generation"]["vendor"]
    vendor_root = Path(vendor_cfg.get("root", ".rapidkit/vendor"))
    module_name = base_context["rapidkit_vendor_module"]
    version = str(base_context["rapidkit_vendor_version"])

    expected_vendor_files = {
        target_dir / vendor_root / module_name / version / Path(entry["relative"])
        for entry in vendor_cfg.get("files", [])
    }

    for vendor_path in expected_vendor_files:
        assert vendor_path.exists(), f"Expected vendor artefact {vendor_path} to be generated"
        contents = vendor_path.read_text().strip()
        assert contents, f"Vendor artefact {vendor_path} is empty"

        if vendor_path.as_posix().endswith(
            "src/modules/free/security/rate_limiting/rate_limiting.py"
        ):
            for symbol in (
                "class RateLimiter",
                "class RateLimiterConfig",
                "class MemoryRateLimitBackend",
                "class RedisRateLimitBackend",
                "def configure_rate_limiter",
            ):
                assert symbol in contents
        elif "/src/health/" in vendor_path.as_posix():
            assert "RATE_LIMITING_FEATURES" in contents
            assert "build_health_snapshot" in contents
            assert "render_health_snapshot" in contents
        elif vendor_path.name == "rate_limiting_types.py":
            assert "class RateLimiterHealthSnapshot" in contents
            assert "def as_dict" in contents
        elif vendor_path.suffix == ".js":
            assert "module.exports" in contents
            assert "loadConfiguration" in contents

    frameworks = import_module("modules.free.security.rate_limiting.frameworks")
    plugin = frameworks.get_plugin(variant)
    output_paths = plugin.get_output_paths()

    for logical_name, output_path in output_paths.items():
        artefact_path = target_dir / output_path
        assert (
            artefact_path.exists()
        ), f"Expected {variant} artefact {logical_name} at {artefact_path} to be generated"
        contents = artefact_path.read_text().strip()
        assert contents, f"Generated artefact {artefact_path} is empty"

        if logical_name == "integration_test":
            if variant == "fastapi":
                assert "test_rate_limiter_memory_backend_enforces_limits" in contents
            else:
                assert "RateLimitingHealthModule" in contents
                assert "RateLimitingModule" in contents
        elif variant == "fastapi":
            if logical_name == "runtime_wrapper":
                assert "refresh_vendor_module" in contents
                assert "configure_rate_limiter" in contents
                assert "apply_module_overrides" in contents
            elif logical_name == "dependencies":
                assert "RateLimitDependency" in contents
                assert "rate_limit_dependency" in contents
                assert "_resolve_identity" in contents
            elif logical_name == "router":
                assert "APIRouter" in contents
                assert "probe_rate_limit" in contents
            elif logical_name == "metadata_routes":
                assert "register_rate_limiting_routes" in contents
                assert "RATE_LIMITING_FEATURES" in contents
            elif logical_name == "health_routes":
                # canonicalised health output may contain shared helpers or the
                # variant-level registration helpers — accept either.
                assert (
                    "register_rate_limiting_health" in contents
                    or "build_health_snapshot" in contents
                )
                # router-style handler may be present, otherwise shared helpers
                assert (
                    "rate_limiting_health_check" in contents or "build_health_snapshot" in contents
                )
            elif logical_name == "shared_health_runtime":
                assert "build_health_snapshot" in contents
                assert "RATE_LIMITING_FEATURES" in contents
            elif logical_name == "shared_types":
                assert "class RateLimiterHealthSnapshot" in contents
            elif logical_name == "config_yaml":
                assert "rate_limiting:" in contents
                assert "backend:" in contents
                assert "default_rule" in contents
        elif variant == "nestjs":
            if logical_name == "controller":
                assert (
                    "@Controller('security/rate-limiting')" in contents
                    or '@Controller("security/rate-limiting")' in contents
                )
                assert "@Get('metadata')" in contents or '@Get("metadata")' in contents
                assert "@Get('health')" in contents or '@Get("health")' in contents
            elif logical_name == "service":
                assert "class RateLimitingService" in contents
                assert "async consume(options" in contents
                assert "toHeaders" in contents
            elif logical_name == "guard":
                assert "class RateLimitingGuard" in contents
                assert "HttpException" in contents
                assert "HttpStatus.TOO_MANY_REQUESTS" in contents
                assert "RATE_LIMIT_RULE_METADATA_KEY" in contents
            elif logical_name == "module":
                assert "@Module" in contents
                assert "RateLimitingController" in contents
                assert "RateLimitingGuard" in contents
            elif logical_name == "configuration":
                assert "registerAs" in contents
                assert "rateLimitingConfiguration" in contents
            elif logical_name == "health_controller":
                assert "RateLimitingHealthController" in contents
                assert "@Get('rate-limiting')" in contents or '@Get("rate-limiting")' in contents
            elif logical_name == "health_module":
                assert "RateLimitingHealthModule" in contents
                assert "RateLimitingModule" in contents
            elif logical_name == "shared_health_runtime":
                assert "build_health_snapshot" in contents
                assert "RATE_LIMITING_FEATURES" in contents
            elif logical_name == "shared_types":
                assert "class RateLimiterHealthSnapshot" in contents


def test_rate_limiting_generator_entrypoint() -> None:
    module = import_module("modules.free.security.rate_limiting.generate")
    assert module


def test_rate_limiter_enforces_limits_in_memory(rate_limiting_runtime) -> None:
    RateLimiterConfig = rate_limiting_runtime.RateLimiterConfig
    RateLimiter = rate_limiting_runtime.RateLimiter

    config = RateLimiterConfig(default_limit=2, default_window=20)
    limiter = RateLimiter(config)

    async def _exercise() -> tuple[bool, bool, bool]:
        first = await limiter.consume(
            identity="client", method="GET", path="/", raise_on_failure=False
        )
        second = await limiter.consume(
            identity="client", method="GET", path="/", raise_on_failure=False
        )
        third = await limiter.consume(
            identity="client", method="GET", path="/", raise_on_failure=False
        )
        return first.allowed, second.allowed, third.allowed

    first_allowed, second_allowed, third_allowed = asyncio.run(_exercise())

    assert first_allowed is True
    assert second_allowed is True
    assert third_allowed is False


def test_load_rate_limiter_config_from_environment(
    monkeypatch: pytest.MonkeyPatch,
    rate_limiting_runtime,
) -> None:
    load_rate_limiter_config = rate_limiting_runtime.load_rate_limiter_config

    expected_limit = 42
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("RATE_LIMIT_DEFAULT_LIMIT", str(expected_limit))
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "memory")
    monkeypatch.setenv(
        "RATE_LIMIT_RULES_JSON",
        json.dumps(
            [
                {
                    "name": "login",
                    "limit": 5,
                    "window_seconds": 60,
                    "routes": ["/auth/login"],
                    "methods": ["POST"],
                }
            ]
        ),
    )

    config = load_rate_limiter_config(env=os.environ)

    assert config.enabled is False
    assert config.default_limit == expected_limit
    assert any(rule.name == "login" for rule in config.rules)


def test_configure_rate_limiter_singleton_resolves(
    monkeypatch: pytest.MonkeyPatch,
    rate_limiting_runtime,
) -> None:
    RateLimiterConfig = rate_limiting_runtime.RateLimiterConfig
    RateLimitExceeded = rate_limiting_runtime.RateLimitExceeded
    configure_rate_limiter = rate_limiting_runtime.configure_rate_limiter
    get_rate_limiter = rate_limiting_runtime.get_rate_limiter

    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
    config = RateLimiterConfig(default_limit=10, default_window=10)
    limiter = configure_rate_limiter(config)
    assert get_rate_limiter() is limiter
    with pytest.raises(RateLimitExceeded):
        asyncio.run(
            limiter.consume(
                identity="ratelimited",
                method="GET",
                path="/",
                rule_name=None,
                raise_on_failure=True,
                cost=config.default_limit + 1,
            )
        )


def test_generate_nestjs_variant_materialises_routes(tmp_path: Path) -> None:
    generator = rate_generate.RateLimitingModuleGenerator()
    config = generator.load_module_config()
    renderer = generator.create_renderer()
    base_context = generator.apply_base_context_overrides(generator.build_base_context(config))

    generator.generate_vendor_files(config, tmp_path, renderer, base_context)
    generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)

    controller_file = (
        tmp_path / "src/modules/free/security/rate_limiting/rate-limiting.controller.ts"
    )
    module_file = tmp_path / "src/modules/free/security/rate_limiting/rate-limiting.module.ts"
    service_file = tmp_path / "src/modules/free/security/rate_limiting/rate-limiting.service.ts"
    guard_file = tmp_path / "src/modules/free/security/rate_limiting/rate-limiting.guard.ts"
    configuration_file = (
        tmp_path / "src/modules/free/security/rate_limiting/rate-limiting.configuration.ts"
    )
    health_controller_file = tmp_path / "src/health/rate-limiting-health.controller.ts"
    health_module_file = tmp_path / "src/health/rate-limiting-health.module.ts"
    integration_test_file = (
        tmp_path / "tests/modules/integration/security/rate_limiting.integration.spec.ts"
    )

    for artefact in (
        controller_file,
        module_file,
        service_file,
        guard_file,
        configuration_file,
        health_controller_file,
        health_module_file,
        integration_test_file,
    ):
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} is empty"

    controller_src = controller_file.read_text()
    assert (
        "@Controller('security/rate-limiting')" in controller_src
        or '@Controller("security/rate-limiting")' in controller_src
    ), "Rate limiting controller should expose security/rate-limiting routes"
    assert "@Get('metadata')" in controller_src or '@Get("metadata")' in controller_src
    assert "@Get('features')" in controller_src or '@Get("features")' in controller_src
    assert "@Get('health')" in controller_src or '@Get("health")' in controller_src

    module_src = module_file.read_text()
    assert "@Module" in module_src
    assert "RateLimitingController" in module_src

    service_src = service_file.read_text()
    assert "class RateLimitingService" in service_src

    configuration_src = configuration_file.read_text()
    assert "rateLimitingConfiguration" in configuration_src
    assert "registerAs" in configuration_src

    health_controller_src = health_controller_file.read_text()
    assert "RateLimitingHealthController" in health_controller_src
    assert (
        "@Get('rate-limiting')" in health_controller_src
        or '@Get("rate-limiting")' in health_controller_src
    )

    health_module_src = health_module_file.read_text()
    assert "RateLimitingHealthModule" in health_module_src
    assert "RateLimitingModule" in health_module_src

    integration_test_src = integration_test_file.read_text()
    assert "RateLimitingHealthModule" in integration_test_src
    assert "RateLimitingModule" in integration_test_src
