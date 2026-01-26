from pathlib import Path

import pytest

from modules.free.essentials.logging.generate import LoggingModuleGenerator


@pytest.fixture(scope="module")
def generator() -> LoggingModuleGenerator:
    return LoggingModuleGenerator()


def _render(
    generator: LoggingModuleGenerator, framework: str, target_dir: Path
) -> tuple[Path, dict]:
    if framework == "fastapi":
        pytest.importorskip("fastapi")

    config = generator.load_module_config()
    base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
    renderer = generator.create_renderer()
    jinja_env = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
    if jinja_env is None:
        pytest.skip("jinja2 is required to render Logging templates")

    generator.generate_vendor_files(config, target_dir, renderer, base_context)
    generator.generate_variant_files(framework, target_dir, renderer, base_context)

    return target_dir, config


def test_fastapi_generation_creates_runtime(
    generator: LoggingModuleGenerator, tmp_path: Path
) -> None:
    output_dir, config = _render(generator, "fastapi", tmp_path)

    project_logging = output_dir / "src/modules/free/essentials/logging/logging.py"
    project_health = output_dir / "src/health/logging.py"
    vendor_root = output_dir / ".rapidkit" / "vendor" / config["name"] / config["version"]
    vendor_logging = vendor_root / "src/modules/free/essentials/logging/logging.py"

    assert project_logging.exists(), "FastAPI wrapper should be generated"
    assert project_health.exists(), "FastAPI health endpoint should be generated"
    assert vendor_logging.exists(), "Vendor logging runtime should be materialised"
    vendor_config = vendor_root / "nestjs" / "configuration.js"
    assert vendor_config.exists(), "Vendor NestJS configuration should be generated"
    assert vendor_config.read_text().strip(), "Vendor configuration should not be empty"

    router_path = output_dir / "src/modules/free/essentials/logging/routers/logging.py"
    assert router_path.exists(), "FastAPI router should be generated"
    router_src = router_path.read_text()
    assert (
        'APIRouter(prefix="/logging"' in router_src or "APIRouter(prefix='/logging'" in router_src
    ), "Logging router should expose /logging namespace"
    for method, route in (("get", "/"), ("post", "/refresh"), ("post", "/level/")):
        tokens = (
            f"@router.{method}('{route}",
            f'@router.{method}("{route}',
        )
        assert any(
            token in router_src for token in tokens
        ), f"Expected {method.upper()} {route} handler"

    health_path = output_dir / "src/health/logging.py"
    health_src = health_path.read_text()
    # health router may be generated directly or provided via a vendor-backed shim
    assert (
        "collect_logging_health" in health_src
        or "Project shim exposing vendor health helpers for logging" in health_src
        or "build_health_router" in health_src
    )
    assert "logging_health_check" in health_src or "register_logging_health" in health_src

    config_path = output_dir / "src/modules/free/essentials/logging/config/logging.yaml"
    assert config_path.exists(), "FastAPI configuration YAML should be generated"
    config_payload = config_path.read_text()
    assert "logging:" in config_payload
    assert "level:" in config_payload


def test_nestjs_generation_creates_typescript_module(
    generator: LoggingModuleGenerator, tmp_path: Path
) -> None:
    output_dir, _ = _render(generator, "nestjs", tmp_path)

    config_dir = output_dir / "src/modules/free/essentials/logging"
    expected_files = {
        "configuration.ts",
        "index.ts",
        "logging.controller.ts",
        "logging.module.ts",
        "logging.service.ts",
        "validation.ts",
        "logging.interceptor.ts",
    }

    generated = {path.name for path in config_dir.glob("*.ts")}
    assert expected_files.issubset(
        generated
    ), "NestJS configuration artefacts should all be generated"

    health_file = output_dir / "src/health/logging.health.ts"
    assert health_file.exists(), "Expected canonical NestJS health artefact under src/health"
    assert health_file.read_text().strip(), "Generated health file should not be empty"

    controller_src = (config_dir / "logging.controller.ts").read_text()
    assert (
        "@Controller('logging')" in controller_src or '@Controller("logging")' in controller_src
    ), "Logging controller should expose logging route"
    assert (
        "@Get()" in controller_src
    ), "Logging controller should expose root configuration endpoint"
    assert "@Get('health')" in controller_src or '@Get("health")' in controller_src

    module_src = (config_dir / "logging.module.ts").read_text()
    assert "@Module" in module_src
    assert "LoggingController" in module_src
    assert "LoggingService" in module_src
    assert "ConfigModule.forFeature" in module_src

    service_src = (config_dir / "logging.service.ts").read_text()
    assert "get configuration" in service_src
    assert "getMetadata()" in service_src
    assert "updateLoggerLevel" in service_src

    integration_spec = (
        output_dir / "tests/modules/integration/essentials/logging/logging.integration.spec.ts"
    )
    assert integration_spec.exists(), "NestJS integration spec should be generated"
    spec_src = integration_spec.read_text()
    assert "describe('LoggingModule" in spec_src
