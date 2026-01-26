# pyright: reportMissingImports=false
"""Test suite for middleware module generator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from modules.free.essentials.middleware import generate  # type: ignore[import]
from modules.free.essentials.middleware.frameworks import (  # type: ignore[import]
    get_plugin,
    list_available_plugins,
)


def test_generator_entrypoint() -> None:
    """Smoky assertion ensuring generator is importable."""
    module_root = Path(__file__).resolve().parents[3]
    assert module_root.exists()


def test_generate_fastapi_variant(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that FastAPI variant generates correctly."""
    pytest.importorskip("fastapi")
    with tempfile.TemporaryDirectory() as tmpdir:
        original_argv = sys.argv
        try:

            def _no_bump(config, **unused):
                if unused:
                    next(iter(unused.items()))
                return dict(config), False

            monkeypatch.setattr(generate, "ensure_version_consistency", _no_bump)
            sys.argv = ["generate", "fastapi", tmpdir]
            module_generator = generate.MiddlewareModuleGenerator()
            renderer = module_generator.create_renderer()
            jinja_env = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
            if jinja_env is None:
                pytest.skip("jinja2 is required to render Middleware templates")

            generate.main()

            # Check generated files exist
            middleware_file = (
                Path(tmpdir)
                / "src"
                / "modules"
                / "free"
                / "essentials"
                / "middleware"
                / "middleware.py"
            )
            shared_health_file = (
                Path(tmpdir)
                / "src"
                / "modules"
                / "free"
                / "essentials"
                / "middleware"
                / "middleware_health.py"
            )
            health_file = Path(tmpdir) / "src" / "health" / "middleware.py"
            test_file = (
                Path(tmpdir)
                / "tests"
                / "modules"
                / "free"
                / "essentials"
                / "middleware"
                / "test_middleware_integration.py"
            )
            config_file = (
                Path(tmpdir)
                / "src"
                / "modules"
                / "free"
                / "essentials"
                / "middleware"
                / "config"
                / "middleware.yaml"
            )

            assert middleware_file.exists(), "middleware.py should be generated"
            assert (
                not shared_health_file.exists()
            ), "legacy src/core/middleware_health.py should not be generated under canonical policy"
            assert health_file.exists(), "src/health/middleware.py should be generated"
            assert test_file.exists(), "test file should be generated"
            assert config_file.exists(), "Configuration file should be generated"

            config_content = yaml.safe_load(config_file.read_text())
            assert isinstance(config_content, dict)
            assert config_content.get("middleware"), "Middleware configuration should have root key"

            vendor_root = (
                Path(tmpdir)
                / ".rapidkit"
                / "vendor"
                / "middleware"
                / generate.load_module_config()["version"]
            )
            vendor_config = vendor_root / "middleware" / "nestjs" / "configuration.js"
            assert vendor_config.exists(), "Vendor NestJS configuration should be generated"
            assert vendor_config.read_text().strip(), "Vendor configuration should not be empty"

            # Check content
            content = middleware_file.read_text()
            assert "ProcessTimeMiddleware" in content
            assert "ServiceHeaderMiddleware" in content
            assert "register_middleware" in content

            # Import the generated runtime to ensure it is loadable
            import importlib

            # Ensure package inits exist so import_module works with modules namespace
            package_parts = [
                Path(tmpdir) / "src",
                Path(tmpdir) / "src" / "modules",
                Path(tmpdir) / "src" / "modules" / "free",
                Path(tmpdir) / "src" / "modules" / "free" / "essentials",
                Path(tmpdir) / "src" / "modules" / "free" / "essentials" / "middleware",
            ]

            src_root = Path(tmpdir) / "src"
            for pkg in package_parts:
                pkg.mkdir(parents=True, exist_ok=True)
                init_file = pkg / "__init__.py"
                if not init_file.exists():
                    init_file.write_text("", encoding="utf-8")

            sys.path.insert(0, str(src_root))
            for name in [
                "src",
                "src.modules",
                "modules",
                "modules.free",
                "modules.free.essentials",
                "modules.free.essentials.middleware",
            ]:
                sys.modules.pop(name, None)
            try:
                module = importlib.import_module("modules.free.essentials.middleware.middleware")
            finally:
                sys.path.pop(0)
                for name in (
                    "modules.free.essentials.middleware.middleware",
                    "modules.free.essentials.middleware",
                    "modules.free.essentials",
                    "modules.free",
                    "modules",
                ):
                    sys.modules.pop(name, None)

            assert hasattr(module, "ProcessTimeMiddleware")
            assert hasattr(module, "register_middleware")

            router_file = (
                Path(tmpdir)
                / "src"
                / "modules"
                / "free"
                / "essentials"
                / "middleware"
                / "routers"
                / "middleware.py"
            )
            assert router_file.exists(), "FastAPI middleware router should be generated"
            router_src = router_file.read_text()
            assert (
                'APIRouter(prefix="/middleware"' in router_src
                or "APIRouter(prefix='/middleware'" in router_src
            ), "Middleware router should expose /middleware namespace"
            assert '@router.get("/"' in router_src or "@router.get('/'" in router_src

        finally:
            sys.argv = original_argv


def test_generate_nestjs_variant(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure NestJS variant emits service/controller/module artefacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_argv = sys.argv
        try:

            def _no_bump(config, **unused):
                if unused:
                    next(iter(unused.items()))
                return dict(config), False

            monkeypatch.setattr(generate, "ensure_version_consistency", _no_bump)
            sys.argv = ["generate", "nestjs", tmpdir]
            module_generator = generate.MiddlewareModuleGenerator()
            renderer = module_generator.create_renderer()
            jinja_env = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
            if jinja_env is None:
                pytest.skip("jinja2 is required to render Middleware templates")

            generate.main()

            service_file = Path(tmpdir) / "src/modules/free/essentials/middleware/service.ts"
            controller_file = Path(tmpdir) / "src/modules/free/essentials/middleware/controller.ts"
            module_file = Path(tmpdir) / "src/modules/free/essentials/middleware/module.ts"
            config_file = Path(tmpdir) / "src/modules/free/essentials/middleware/configuration.ts"
            health_indicator = Path(tmpdir) / "src/health/middleware.health.ts"
            integration_spec = (
                Path(tmpdir)
                / "tests"
                / "modules"
                / "integration"
                / "essentials"
                / "middleware"
                / "middleware.integration.spec.ts"
            )

            assert service_file.exists(), "NestJS service should be generated"
            assert controller_file.exists(), "NestJS controller should be generated"
            assert module_file.exists(), "NestJS module should be generated"
            assert config_file.exists(), "NestJS configuration should be generated"
            assert health_indicator.exists(), "NestJS health indicator should be generated"
            assert integration_spec.exists(), "NestJS integration spec should be generated"

            controller_src = controller_file.read_text()
            assert (
                '@Controller("middleware")' in controller_src
                or "@Controller('middleware')" in controller_src
            )
            assert "MiddlewareController" in controller_src
            assert "@Get()" in controller_src
            assert "@Get('health')" in controller_src or '@Get("health")' in controller_src
            assert "this.service.describe()" in controller_src

            module_src = module_file.read_text()
            assert "MiddlewareModule" in module_src
            assert "@Module" in module_src
            assert "MiddlewareService" in module_src
            assert "getHandlers" in module_src
            assert "consumer.apply(...handlers)" in module_src
            assert "ConfigModule" in module_src

            service_src = service_file.read_text()
            assert "getMetadata" in service_src
            assert "getStatus" in service_src
            assert "loadVendorConfiguration" in service_src
            assert "registerMiddlewareFactory" in service_src
            assert "createProcessTimeMiddleware" in service_src
            assert "createCorsMiddleware" in service_src
            assert "getHandlers" in service_src
            assert "ConfigService" in service_src

            config_src = config_file.read_text()
            assert (
                "registerAs('middleware'" in config_src or 'registerAs("middleware"' in config_src
            )

            spec_src = integration_spec.read_text()
            assert "MiddlewareModule (Integration)" in spec_src

        finally:
            sys.argv = original_argv


def test_framework_plugin_available() -> None:
    """Test that FastAPI plugin is registered."""
    plugins = list_available_plugins()
    assert "fastapi" in plugins
    assert "nestjs" in plugins


def test_plugin_template_mappings() -> None:
    """Test plugin returns correct template mappings."""
    plugin = get_plugin("fastapi")
    assert plugin is not None

    mappings = plugin.get_template_mappings()
    assert "module" in mappings
    # Some modules centralise project-level health into a shared vendor-backed shim
    # so a 'health' variant template may be absent; ensure vendor/base health is
    # present (health_runtime) or the variant-level mapping exists.
    assert "health" in mappings or "health_runtime" in mappings
    assert "integration_tests" in mappings
    assert "config" in mappings

    nest_plugin = get_plugin("nestjs")
    assert nest_plugin is not None
    nest_mappings = nest_plugin.get_template_mappings()
    # Health may be supplied via vendor payload rather than a variant template
    assert {"service", "controller", "module", "config", "integration_tests"}.issubset(
        nest_mappings
    )


def test_plugin_output_paths() -> None:
    """Test plugin returns correct output paths."""
    plugin = get_plugin("fastapi")
    assert plugin is not None

    paths = plugin.get_output_paths()
    assert paths["module"] == "src/modules/free/essentials/middleware/middleware.py"
    assert paths["health_runtime"] == "src/health/middleware.py"
    assert paths["health"] == "src/health/middleware.py"
    assert (
        paths["integration_tests"]
        == "tests/modules/free/essentials/middleware/test_middleware_integration.py"
    )
    assert paths["config"] == "src/modules/free/essentials/middleware/config/middleware.yaml"

    nest_plugin = get_plugin("nestjs")
    assert nest_plugin is not None
    nest_paths = nest_plugin.get_output_paths()
    assert nest_paths["service"] == "src/modules/free/essentials/middleware/service.ts"
    assert nest_paths["controller"] == "src/modules/free/essentials/middleware/controller.ts"
    assert nest_paths["module"] == "src/modules/free/essentials/middleware/module.ts"
    assert nest_paths["config"] == "src/modules/free/essentials/middleware/configuration.ts"
    assert nest_paths["health"] == "src/health/middleware.health.ts"
    assert (
        nest_paths["integration_tests"]
        == "tests/modules/integration/essentials/middleware/middleware.integration.spec.ts"
    )


def test_module_config_loads() -> None:
    """Test that module.yaml loads correctly."""

    config = generate.load_module_config()
    assert config["name"] == "middleware"
    assert "version" in config
    assert config["tier"] == "free"
    assert config["status"] in ("active", "stable")
