"""Test suite for notifications module generator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

from modules.free.communication.notifications import generate


def test_generator_entrypoint() -> None:
    """Smoky assertion ensuring generator is importable."""
    module_root = Path(__file__).resolve().parents[3]
    assert module_root.exists()


def test_generate_fastapi_variant() -> None:
    """Test that FastAPI variant generates correctly."""
    from modules.free.communication.notifications.generate import main as generate_main

    with tempfile.TemporaryDirectory() as tmpdir:
        original_argv = sys.argv
        try:
            sys.argv = ["generate", "fastapi", tmpdir]
            generate_main()

            # Check generated files exist
            notifications_file = (
                Path(tmpdir)
                / "src"
                / "modules"
                / "free"
                / "communication"
                / "notifications"
                / "core"
                / "notifications.py"
            )
            routes_file = (
                Path(tmpdir)
                / "src"
                / "modules"
                / "free"
                / "communication"
                / "notifications"
                / "routers"
                / "notifications.py"
            )
            health_file = Path(tmpdir) / "src" / "health" / "notifications.py"
            test_file = (
                Path(tmpdir)
                / "tests"
                / "modules"
                / "free"
                / "integration"
                / "notifications"
                / "test_notifications_integration.py"
            )

            assert notifications_file.exists(), "notifications.py should be generated"
            assert routes_file.exists(), "routers/notifications.py should be generated"
            assert health_file.exists(), "src/health/notifications.py should be generated"
            assert test_file.exists(), "test file should be generated"

            # Check content
            content = notifications_file.read_text()
            assert "EmailService" in content
            assert "NotificationManager" in content
            assert "register_notifications" in content

        finally:
            sys.argv = original_argv


def test_generate_nestjs_variant() -> None:
    """Test that NestJS variant generates correctly."""
    from modules.free.communication.notifications.generate import main as generate_main

    with tempfile.TemporaryDirectory() as tmpdir:
        original_argv = sys.argv
        try:
            sys.argv = ["generate", "nestjs", tmpdir]
            generate_main()

            # Check generated files exist
            base = Path(tmpdir) / "src" / "modules" / "free" / "communication" / "notifications"
            service_file = base / "notifications.service.ts"
            controller_file = base / "notifications.controller.ts"
            module_file = base / "notifications.module.ts"
            config_file = Path(tmpdir) / "nestjs" / "notifications.config.js"

            for artefact in (service_file, controller_file, module_file, config_file):
                assert artefact.exists(), f"Expected artefact {artefact} to be generated"
                assert (
                    artefact.read_text().strip()
                ), f"Generated file {artefact} should not be empty"

            # Check content
            content = service_file.read_text()
            assert "EmailService" in content
            assert "NotificationManager" in content

            controller_src = controller_file.read_text()
            assert (
                "@Controller('notifications')" in controller_src
                or '@Controller("notifications")' in controller_src
            ), "Controller should mount notifications routes"
            assert "@Get('metadata')" in controller_src or '@Get("metadata")' in controller_src
            assert "@Post('send')" in controller_src or '@Post("send")' in controller_src

            module_src = module_file.read_text()
            assert "@Module" in module_src
            assert "NotificationsController" in module_src

        finally:
            sys.argv = original_argv


def test_framework_plugin_available() -> None:
    """Test that framework plugins are registered."""
    from modules.free.communication.notifications.frameworks import list_available_plugins

    plugins = list_available_plugins()
    assert "fastapi" in plugins
    assert "nestjs" in plugins


def test_fastapi_plugin_template_mappings() -> None:
    """Test FastAPI plugin returns correct template mappings."""
    from modules.free.communication.notifications.frameworks import get_plugin

    plugin = get_plugin("fastapi")
    assert plugin is not None

    mappings = plugin.get_template_mappings()
    assert {"runtime", "routes", "integration_tests"}.issubset(mappings.keys())


def test_fastapi_plugin_output_paths() -> None:
    """Test FastAPI plugin returns correct output paths."""
    from modules.free.communication.notifications.frameworks import get_plugin

    plugin = get_plugin("fastapi")
    assert plugin is not None

    paths = plugin.get_output_paths()
    assert paths["runtime"] == "src/modules/free/communication/notifications/core/notifications.py"
    assert (
        paths["routes"] == "src/modules/free/communication/notifications/routers/notifications.py"
    )
    assert paths["health"] == "src/health/notifications.py"
    assert (
        paths["integration_tests"]
        == "tests/modules/free/integration/notifications/test_notifications_integration.py"
    )


def test_nestjs_plugin_template_mappings() -> None:
    """Test NestJS plugin returns correct template mappings."""
    from modules.free.communication.notifications.frameworks import get_plugin

    plugin = get_plugin("nestjs")
    assert plugin is not None

    mappings = plugin.get_template_mappings()
    assert {"service", "controller", "module", "config"}.issubset(mappings.keys())


def test_nestjs_plugin_output_paths() -> None:
    """Test NestJS plugin returns correct output paths."""
    from modules.free.communication.notifications.frameworks import get_plugin

    plugin = get_plugin("nestjs")
    assert plugin is not None

    paths = plugin.get_output_paths()
    assert (
        paths["service"] == "src/modules/free/communication/notifications/notifications.service.ts"
    )
    assert (
        paths["controller"]
        == "src/modules/free/communication/notifications/notifications.controller.ts"
    )
    assert paths["module"] == "src/modules/free/communication/notifications/notifications.module.ts"
    assert paths["config"] == "nestjs/notifications.config.js"


def test_module_config_loads() -> None:
    """Test that module.yaml loads correctly."""
    from modules.free.communication.notifications.generate import load_module_config

    config = load_module_config()
    assert config["name"] == "notifications"
    assert "version" in config
    assert config["tier"] == "free"
    assert config["status"] in ("active", "stable")
    assert "communication" in config.get("tags", [])


def test_generate_variants_produce_expected_outputs(tmp_path: Path) -> None:
    """Ensure notifications generator renders vendor, FastAPI, and NestJS artefacts."""

    generator = generate.NotificationsModuleGenerator()
    renderer = generator.create_renderer()
    jinja_available = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
    if jinja_available is None:
        pytest.skip("jinja2 is required to render Notifications templates")

    config = generator.load_module_config()
    base_context = generator.build_base_context(config)

    generator.generate_vendor_files(config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
    )
    vendor_runtime_path = vendor_root / "runtime" / "communication" / "notifications.py"
    vendor_types_path = vendor_root / "runtime" / "communication" / "notifications_types.py"
    vendor_config_path = vendor_root / "notifications" / "nestjs" / "configuration.js"
    vendor_expected = {
        vendor_runtime_path,
        vendor_types_path,
        vendor_config_path,
    }
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated vendor file {artefact} is empty"

    runtime_src = vendor_runtime_path.read_text()
    for token in (
        "def list_notification_features",
        "def describe_notifications",
        "def get_notifications_metadata",
        "__all__",
    ):
        assert token in runtime_src, f"Vendor runtime missing {token}"

    types_src = vendor_types_path.read_text()
    for token in (
        "class NotificationProviderSnapshot",
        "class NotificationsHealthSnapshot",
        "def as_dict",
    ):
        assert token in types_src, f"Vendor types missing {token}"

    config_src = vendor_config_path.read_text()
    for token in ("function loadConfiguration", "module.exports"):
        assert token in config_src, f"Vendor configuration missing {token}"

    generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    fastapi_base = tmp_path / "src" / "modules" / "free" / "communication" / "notifications"
    fastapi_runtime_path = fastapi_base / "core" / "notifications.py"
    fastapi_routes_path = fastapi_base / "routers" / "notifications.py"
    fastapi_health_path = tmp_path / "src" / "health" / "notifications.py"
    fastapi_expected = {
        fastapi_runtime_path,
        fastapi_routes_path,
        fastapi_health_path,
        tmp_path
        / "tests"
        / "modules"
        / "free"
        / "integration"
        / "notifications"
        / "test_notifications_integration.py",
    }
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated FastAPI file {artefact} is empty"

    runtime_src = fastapi_runtime_path.read_text()
    for token in (
        "class EmailService",
        "class NotificationManager",
        "async def send_notification",
        "async def verify_connection",
        "def register_notifications",
        "def get_notification_manager",
        "def get_email_service",
        "__all__",
    ):
        assert token in runtime_src, f"FastAPI runtime missing {token}"

    health_src = fastapi_health_path.read_text()
    for token in (
        "def build_health_router",
        "register_notifications_health",
        "refresh_vendor_module",
    ):
        assert token in health_src, f"FastAPI health shim missing {token}"

    router_src = fastapi_routes_path.read_text()
    assert any(
        token in router_src
        for token in (
            'APIRouter(prefix="/notifications"',
            "APIRouter(prefix='/notifications'",
        )
    ), "FastAPI router should expose /notifications namespace"
    fastapi_routes = {
        "/metadata": "get",
        "/features": "get",
        "/send": "post",
        "/verify-email": "post",
    }
    for route, method in fastapi_routes.items():
        tokens = (
            f"@router.{method}('{route}'",
            f'@router.{method}("{route}"',
        )
        assert any(token in router_src for token in tokens), f"FastAPI router should expose {route}"

    generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)
    nest_root = tmp_path / "src" / "modules" / "free" / "communication" / "notifications"
    nest_service_path = nest_root / "notifications.service.ts"
    nest_controller_path = nest_root / "notifications.controller.ts"
    nest_module_path = nest_root / "notifications.module.ts"
    nest_config_path = tmp_path / "nestjs" / "notifications.config.js"
    nest_expected = {
        nest_service_path,
        nest_controller_path,
        nest_module_path,
        nest_config_path,
    }
    for artefact in nest_expected:
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated NestJS file {artefact} is empty"

    service_src = nest_service_path.read_text()
    for token in (
        "export const NOTIFICATIONS_EMAIL_CONFIG",
        "export const NOTIFICATIONS_TEMPLATE_OPTIONS",
        "export const NOTIFICATIONS_PROVIDER_OVERRIDES",
        "export class EmailService",
        "async sendTemplatedEmail",
        "async verifyConnection",
        "export class NotificationManager",
        "async sendNotification",
        "private async dispatchEmailNotification",
        "export function describeNotifications",
        "export function listNotificationFeatures",
        "HealthCheckNotifications",
    ):
        assert token in service_src, f"NestJS service missing {token}"

    controller_src = nest_controller_path.read_text()
    assert (
        "@Controller('notifications')" in controller_src
        or '@Controller("notifications")' in controller_src
    ), "NestJS controller should mount notifications route"
    for decorator in (
        "@Get('metadata')",
        "@Get('features')",
        "@Get('health')",
        "@Post('send')",
        "@Post('verify-email')",
    ):
        counterpart = decorator.replace("'", '"')
        assert (
            decorator in controller_src or counterpart in controller_src
        ), f"Expected {decorator} handler"
    for token in (
        "describeNotifications",
        "listNotificationFeatures",
        "NOTIFICATIONS_PROVIDER_OVERRIDES",
    ):
        assert token in controller_src, f"NestJS controller missing {token}"

    module_src = nest_module_path.read_text()
    for token in (
        "export class NotificationsModule",
        "@Module",
        "NOTIFICATIONS_EMAIL_CONFIG",
        "NOTIFICATIONS_TEMPLATE_OPTIONS",
        "NOTIFICATIONS_PROVIDER_OVERRIDES",
        "NOTIFICATIONS_EMAIL_TRANSPORT",
        "static register",
    ):
        assert token in module_src, f"NestJS module missing {token}"
    for token in ("ConfigModule", "ConfigService"):
        assert token in module_src, f"NestJS module missing {token}"

    config_src = nest_config_path.read_text()
    for token in ("module.exports", "loadConfiguration"):
        assert token in config_src, f"NestJS configuration missing {token}"
