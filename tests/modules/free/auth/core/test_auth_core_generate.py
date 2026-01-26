import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

from modules.free.auth.core.generate import AuthCoreModuleGenerator


@pytest.fixture(scope="module")
def generator() -> AuthCoreModuleGenerator:
    return AuthCoreModuleGenerator()


def _render(
    generator: AuthCoreModuleGenerator,
    framework: str,
    target_dir: Path,
) -> tuple[Path, Mapping[str, Any], dict[str, Any]]:
    config: Mapping[str, Any] = generator.load_module_config()
    base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, target_dir, renderer, base_context)
    generator.generate_variant_files(framework, target_dir, renderer, base_context)

    return target_dir, config, base_context


def test_fastapi_generation_produces_runtime_and_health(
    generator: AuthCoreModuleGenerator, tmp_path: Path
) -> None:
    output_dir, config, base_context = _render(generator, "fastapi", tmp_path)

    runtime_path = output_dir / "src/modules/free/auth/core/auth/core.py"
    dependencies_path = output_dir / "src/modules/free/auth/core/auth/dependencies.py"
    health_path = output_dir / "src/health/auth_core.py"
    aggregator_path = output_dir / "src/health/__init__.py"

    assert runtime_path.exists(), "FastAPI runtime should be generated"
    assert dependencies_path.exists(), "FastAPI dependency helpers should be generated"
    assert health_path.exists(), "FastAPI health shim should be generated"
    assert aggregator_path.exists(), "Health aggregator should be materialised"

    contents = aggregator_path.read_text(encoding="utf-8")
    assert (
        "register_auth_core_health" in contents
    ), "Health aggregator should include Auth Core hook"

    vendor_root = output_dir / ".rapidkit" / "vendor" / config["name"] / config["version"]
    vendor_runtime = vendor_root / base_context["rapidkit_vendor_python_relative"]
    vendor_health = vendor_root / base_context["rapidkit_vendor_health_relative"]

    assert vendor_runtime.exists(), "Vendor runtime should be persisted"
    assert vendor_health.exists(), "Vendor health metadata should be persisted"

    spec = importlib.util.spec_from_file_location("auth_core_vendor", vendor_runtime)
    assert spec and spec.loader, "Vendor runtime should be importable"

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    defaults = module.DEFAULTS
    assert defaults["issuer"] == base_context["auth_core_defaults"]["issuer"]


def test_nestjs_generation_produces_scaffolds(
    generator: AuthCoreModuleGenerator, tmp_path: Path
) -> None:
    output_dir, config, base_context = _render(generator, "nestjs", tmp_path)

    service_path = output_dir / "src/modules/free/auth/core/auth-core.service.ts"
    module_path = output_dir / "src/modules/free/auth/core/auth-core.module.ts"
    controller_path = output_dir / "src/modules/free/auth/core/auth-core.controller.ts"
    index_path = output_dir / "src/modules/free/auth/core/index.ts"
    validation_path = output_dir / "src/modules/free/auth/core/config/auth-core.validation.ts"
    tsconfig_path = output_dir / "tsconfig.json"
    package_path = output_dir / "package.json"

    assert service_path.exists(), "NestJS service should be generated"
    assert module_path.exists(), "NestJS module should be generated"
    assert controller_path.exists(), "NestJS controller should be generated"
    assert index_path.exists(), "NestJS index export should be generated"
    assert validation_path.exists(), "NestJS validation helpers should be generated"

    assert tsconfig_path.exists(), "NestJS generation should scaffold tsconfig.json"
    assert package_path.exists(), "NestJS generation should scaffold package.json"

    tsconfig = json.loads(tsconfig_path.read_text(encoding="utf-8"))
    compiler_options = tsconfig.get("compilerOptions", {})
    assert compiler_options.get("emitDecoratorMetadata") is True
    assert compiler_options.get("target") == "ES2020"

    package_data = json.loads(package_path.read_text(encoding="utf-8"))
    dependencies = package_data.get("dependencies", {})
    dev_dependencies = package_data.get("devDependencies", {})
    assert "@nestjs/common" in dependencies
    assert "typescript" in dev_dependencies

    controller_src = controller_path.read_text(encoding="utf-8")
    assert (
        "@Controller('auth/core')" in controller_src or '@Controller("auth/core")' in controller_src
    ), "Auth Core controller should mount auth/core routes"
    assert "@Get('metadata')" in controller_src or '@Get("metadata")' in controller_src
    assert "@Get('features')" in controller_src or '@Get("features")' in controller_src
    assert "@Get('health')" in controller_src or '@Get("health")' in controller_src

    service_src = service_path.read_text(encoding="utf-8")
    assert "metadata():" in service_src
    assert "health():" in service_src

    module_src = module_path.read_text(encoding="utf-8")
    assert "AuthCoreService" in module_src
    assert "AUTH_CORE_CONFIG" in module_src

    vendor_root = output_dir / ".rapidkit" / "vendor" / config["name"] / config["version"]
    vendor_config = vendor_root / "nestjs/configuration.js"
    assert vendor_config.exists(), "NestJS vendor configuration should be persisted"
    contents = vendor_config.read_text(encoding="utf-8")
    assert "module.exports" in contents
    assert "tokenTtlSeconds" in contents
