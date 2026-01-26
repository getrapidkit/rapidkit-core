"""Integration tests for the Notifications module runtime."""

from __future__ import annotations

import importlib.util
from importlib import import_module

import pytest

try:
    from fastapi import FastAPI, status
    from fastapi.testclient import TestClient
except (RuntimeError, ModuleNotFoundError) as exc:  # pragma: no cover - optional dependency
    message = str(exc).lower()
    missing_name = getattr(exc, "name", "")
    if "fastapi" in message or missing_name == "fastapi":
        pytest.skip(
            "fastapi is required for notifications integration tests", allow_module_level=True
        )
    if "httpx" in message or missing_name == "httpx":
        pytest.skip("httpx is required for FastAPI TestClient", allow_module_level=True)
    raise


def _safe_find_spec(module_name: str):
    try:
        return importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        return None


NOTIFICATIONS_AVAILABLE = (
    _safe_find_spec("modules.free.communication.notifications.core.notifications") is not None
)
DEFAULT_SMTP_PORT = 587

pytestmark = [
    pytest.mark.integration,
    pytest.mark.core_integration,
    pytest.mark.skipif(
        not NOTIFICATIONS_AVAILABLE,
        reason="Notifications module is not present in the core runtime",
    ),
]


def _build_app() -> FastAPI:
    """Build FastAPI app with notifications module."""
    module = import_module("modules.free.communication.notifications.core.notifications")
    get_notification_manager = module.get_notification_manager

    app = FastAPI(title="Notifications Integration Test")
    app.state.notification_manager = get_notification_manager()
    return app


def test_exports_available() -> None:
    """Test that all required exports are available."""
    module = import_module("modules.free.communication.notifications.core.notifications")

    email_config = module.EmailConfig
    email_service = module.EmailService
    notification_manager = module.NotificationManager
    register_notifications = module.register_notifications
    get_notification_manager = module.get_notification_manager

    assert email_config is not None
    assert email_service is not None
    assert notification_manager is not None
    assert callable(register_notifications)
    assert callable(get_notification_manager)


def test_email_config_initialization() -> None:
    """Test EmailConfig dataclass initialization."""
    from modules.free.communication.notifications.core.notifications import EmailConfig

    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=DEFAULT_SMTP_PORT,
        smtp_user="test@example.com",
        smtp_password="password",
        from_email="noreply@example.com",
        from_name="Test App",
    )

    assert config.smtp_host == "smtp.example.com"
    assert config.smtp_port == DEFAULT_SMTP_PORT
    assert config.smtp_user == "test@example.com"
    assert config.from_email == "noreply@example.com"


def test_email_service_creation() -> None:
    """Test EmailService can be instantiated."""
    from modules.free.communication.notifications.core.notifications import (
        EmailConfig,
        EmailService,
    )

    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=DEFAULT_SMTP_PORT,
        smtp_user="test@example.com",
        smtp_password="password",
        from_email="noreply@example.com",
        from_name="Test App",
    )

    service = EmailService(config)
    assert service is not None
    assert service.config == config


def test_notification_manager_creation() -> None:
    """Test NotificationManager can be instantiated."""
    from modules.free.communication.notifications.core.notifications import (
        EmailConfig,
        NotificationManager,
    )

    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=DEFAULT_SMTP_PORT,
        smtp_user="test@example.com",
        smtp_password="password",
        from_email="noreply@example.com",
        from_name="Test App",
    )

    manager = NotificationManager(config)
    assert manager is not None
    assert manager.email_service is not None


def test_register_notifications_health_route() -> None:
    """Test that health endpoint is available after registration."""
    try:
        health_spec = importlib.util.find_spec("src.health.notifications")
    except ModuleNotFoundError:
        health_spec = None
    if health_spec is None:
        pytest.skip("Notifications health module not present in runtime")

    health_module = import_module("src.health.notifications")
    register_notifications_health = health_module.register_notifications_health

    app = FastAPI(title="Health Test")
    register_notifications_health(app)

    client = TestClient(app)
    response = client.get("/health/notifications")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload.get("status") == "ok"
    assert payload.get("module") == "notifications"
    assert "version" in payload
    assert "checked_at" in payload


def test_notification_manager_has_methods() -> None:
    """Test that NotificationManager has required methods."""
    from modules.free.communication.notifications.core.notifications import (
        EmailConfig,
        NotificationManager,
    )

    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=DEFAULT_SMTP_PORT,
        smtp_user="test@example.com",
        smtp_password="password",
        from_email="noreply@example.com",
        from_name="Test App",
    )

    manager = NotificationManager(config)

    # Check for expected async methods
    assert hasattr(manager, "send_email")
    assert callable(manager.send_email)


@pytest.mark.asyncio
async def test_get_notification_manager_singleton() -> None:
    """Test that get_notification_manager returns same instance."""
    from modules.free.communication.notifications.core.notifications import get_notification_manager

    manager1 = get_notification_manager()
    manager2 = get_notification_manager()

    assert manager1 is manager2


def test_module_exports_pydantic_models() -> None:
    """Test that Pydantic models are exported."""
    module = import_module("modules.free.communication.notifications.core.notifications")

    email_message = module.EmailMessage
    notification = module.Notification

    assert email_message is not None
    assert notification is not None

    # Test model instantiation
    msg = email_message(
        to="test@example.com",
        subject="Test",
        body="Test body",
    )

    assert msg.to == "test@example.com"
    assert msg.subject == "Test"
