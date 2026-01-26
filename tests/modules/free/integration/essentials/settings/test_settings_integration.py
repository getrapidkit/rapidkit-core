"""Integration tests for the Settings module runtime."""

import importlib.util
import inspect
import os
from importlib import import_module

import pytest

SETTINGS_AVAILABLE = importlib.util.find_spec("core.settings") is not None

pytestmark = [
    pytest.mark.integration,
    pytest.mark.core_integration,
    pytest.mark.skipif(
        not SETTINGS_AVAILABLE,
        reason="Settings module is not present in the core runtime",
    ),
]

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None


def test_imports() -> None:
    module = import_module("core.settings")
    expected_symbols = {
        "Settings",
        "get_settings",
        "settings",
        "settings_dependency",
        "configure_fastapi_app",
        "Field",
        "BaseSettings",
    }

    missing = [name for name in expected_symbols if not hasattr(module, name)]
    assert not missing, f"Missing expected exports: {missing}"


def test_settings_singleton() -> None:
    module = import_module("core.settings")
    get_settings = module.get_settings

    settings_one = get_settings()
    settings_two = get_settings()

    assert settings_one is settings_two


def test_settings_has_required_fields() -> None:
    from core.settings import settings  # type: ignore[import]

    assert hasattr(settings, "PROJECT_NAME")
    assert hasattr(settings, "VERSION")
    assert hasattr(settings, "ENV")
    assert hasattr(settings, "DEBUG")

    assert isinstance(settings.PROJECT_NAME, str)
    assert isinstance(settings.VERSION, str)
    assert isinstance(settings.ENV, str)
    assert isinstance(settings.DEBUG, bool)


@pytest.mark.parametrize("value,expected", [("true", True), ("false", False)])
def test_settings_environment_parsing(value: str, expected: bool) -> None:
    from core.settings import Settings  # type: ignore[import]

    original = os.environ.get("DEBUG")
    try:
        os.environ["DEBUG"] = value
        test_settings = Settings()
        assert test_settings.DEBUG is expected
    finally:
        if original is not None:
            os.environ["DEBUG"] = original
        else:
            os.environ.pop("DEBUG", None)


def test_settings_dependency_function() -> None:
    from core.settings import Settings, settings_dependency  # type: ignore[import]

    resolved = settings_dependency()
    assert isinstance(resolved, Settings)


def test_configure_fastapi_app_signature() -> None:
    from core.settings import configure_fastapi_app  # type: ignore[import]

    params = inspect.signature(configure_fastapi_app).parameters
    assert "app" in params


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
def test_fastapi_integration() -> None:
    from core.settings import Settings, configure_fastapi_app  # type: ignore[import]
    from fastapi import FastAPI

    app = FastAPI()
    resolved = configure_fastapi_app(app)

    assert isinstance(resolved, Settings)
    assert hasattr(app.state, "settings")


def test_settings_module_exports() -> None:
    module = import_module("core.settings")

    expected = [
        "Settings",
        "get_settings",
        "settings",
        "settings_dependency",
        "Field",
        "BaseSettings",
    ]
    for name in expected:
        assert hasattr(module, name), f"Missing export: {name}"


def test_settings_refresh() -> None:
    from core.settings import get_settings  # type: ignore[import]

    instance = get_settings()
    instance.refresh()
    assert instance is get_settings()
