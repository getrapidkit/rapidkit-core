"""Tests for OAuth module framework plugins and registry helpers."""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Mapping

import pytest

from modules.free.auth.oauth.frameworks import (
    discover_external_plugins,
    get_plugin,
    list_available_plugins,
    refresh_plugin_registry,
    register_plugin,
)
from modules.free.auth.oauth.frameworks.fastapi import FastAPIPlugin as OAuthFastAPIPlugin
from modules.free.auth.oauth.frameworks.nestjs import NestJSPlugin as OAuthNestJSPlugin
from modules.free.auth.passwordless.frameworks.fastapi import (
    FastAPIPlugin as PasswordlessFastAPIPlugin,
)
from modules.free.auth.passwordless.frameworks.nestjs import (
    NestJSPlugin as PasswordlessNestJSPlugin,
)
from modules.free.auth.session.frameworks.fastapi import FastAPIPlugin as SessionFastAPIPlugin
from modules.free.auth.session.frameworks.nestjs import NestJSPlugin as SessionNestJSPlugin
from modules.shared.frameworks import FrameworkPlugin


@pytest.fixture(autouse=True)
def reset_oauth_registry() -> Iterator[None]:
    """Ensure each test works with a clean registry state."""

    refresh_plugin_registry(auto_discover=False)
    yield
    refresh_plugin_registry(auto_discover=False)


@pytest.mark.parametrize(
    "framework,plugin_cls,template_key,output_key",
    (
        ("fastapi", OAuthFastAPIPlugin, "oauth", "oauth"),
        ("nestjs", OAuthNestJSPlugin, "service", "service"),
    ),
)
def test_builtin_plugins_registered(
    framework: str, plugin_cls: type[FrameworkPlugin], template_key: str, output_key: str
) -> None:
    plugin = get_plugin(framework)

    assert isinstance(plugin, plugin_cls)
    assert plugin.name == framework
    assert template_key in plugin.get_template_mappings()
    assert output_key in plugin.get_output_paths()
    assert plugin.validate_requirements() == []

    base_context = {"rapidkit_vendor_configuration_relative": "vendor/config.json"}
    context = plugin.get_context_enrichments(base_context)
    assert context["framework"] == framework
    assert context["framework_display_name"].lower() == framework
    if framework == "nestjs":
        assert context["vendor_configuration_relative"] == "vendor/config.json"
    else:
        assert "vendor_configuration_relative" not in context


def test_list_available_plugins_exposes_display_names() -> None:
    assert list_available_plugins() == {"fastapi": "FastAPI", "nestjs": "NestJS"}


class DummyPlugin(FrameworkPlugin):
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def language(self) -> str:
        return "python"

    @property
    def display_name(self) -> str:
        return "Dummy"

    def get_template_mappings(self) -> Dict[str, str]:
        return {}

    def get_output_paths(self) -> Dict[str, str]:
        return {}

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return dict(base_context)

    def validate_requirements(self) -> List[str]:
        return []


def test_register_plugin_allows_new_frameworks() -> None:
    register_plugin(DummyPlugin)

    plugin = get_plugin("dummy")
    assert isinstance(plugin, DummyPlugin)


class DuplicateFastAPIPlugin(DummyPlugin):
    @property
    def name(self) -> str:
        return "fastapi"


def test_register_plugin_rejects_duplicate_names() -> None:
    with pytest.raises(ValueError):
        register_plugin(DuplicateFastAPIPlugin)


class BadConstructorPlugin(FrameworkPlugin):
    def __init__(self, foo: str) -> None:  # pragma: no cover - instantiation should fail
        self.foo = foo

    @property
    def name(self) -> str:
        return "bad"

    @property
    def language(self) -> str:
        return "python"

    @property
    def display_name(self) -> str:
        return "Bad"

    def get_template_mappings(self) -> Dict[str, str]:
        return {}

    def get_output_paths(self) -> Dict[str, str]:
        return {}

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return dict(base_context)

    def validate_requirements(self) -> List[str]:
        return []


def test_register_plugin_surfaces_instantiation_errors() -> None:
    with pytest.raises(ValueError):
        register_plugin(BadConstructorPlugin)


class StubEntryPoint:
    def __init__(self, obj: Any) -> None:
        self._obj = obj

    def load(self) -> Any:
        return self._obj


class ExternalPlugin(FrameworkPlugin):
    @property
    def name(self) -> str:
        return "external"

    @property
    def language(self) -> str:
        return "python"

    @property
    def display_name(self) -> str:
        return "External"

    def get_template_mappings(self) -> Dict[str, str]:
        return {"sample": "template.j2"}

    def get_output_paths(self) -> Dict[str, str]:
        return {"sample": "src/sample.py"}

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {**base_context, "framework": "external"}

    def validate_requirements(self) -> List[str]:
        return []


def test_discover_external_plugins_registers_valid_classes() -> None:
    registered = discover_external_plugins(
        entry_points_iterable=[StubEntryPoint(ExternalPlugin), StubEntryPoint(object)]
    )

    assert registered == ["ExternalPlugin"]
    plugin = get_plugin("external")
    assert isinstance(plugin, ExternalPlugin)


@pytest.mark.parametrize(
    "plugin_cls,template_mapping,output_mapping,context_expectations",
    (
        (
            PasswordlessFastAPIPlugin,
            {
                "passwordless": "templates/variants/fastapi/passwordless.py.j2",
                "passwordless_types": "templates/base/passwordless_types.py.j2",
                "routes": "templates/variants/fastapi/passwordless_routes.py.j2",
                "config": "templates/variants/fastapi/passwordless_config.yaml.j2",
                "integration_tests": "templates/tests/integration/test_passwordless_integration.j2",
            },
            {
                "passwordless": "src/modules/free/auth/passwordless/passwordless.py",
                "passwordless_types": "src/modules/free/auth/passwordless/passwordless_types.py",
                "routes": "src/modules/free/auth/passwordless/routers/passwordless.py",
                "config": "config/passwordless.yaml",
                "integration_tests": "tests/modules/integration/auth/passwordless/test_passwordless_integration.py",
            },
            {
                "framework": "fastapi",
                "framework_display_name": "FastAPI",
                "language": "python",
                "module_class_name": "Passwordless",
                "auth_methods": ["email", "sms", "magic_link"],
                "token_expiry": 900,
                "rate_limiting": True,
            },
        ),
        (
            PasswordlessNestJSPlugin,
            {
                "configuration": "templates/variants/nestjs/configuration.ts.j2",
                "service": "templates/variants/nestjs/passwordless.service.ts.j2",
                "module": "templates/variants/nestjs/passwordless.module.ts.j2",
                "controller": "templates/variants/nestjs/passwordless.controller.ts.j2",
                "index": "templates/variants/nestjs/index.ts.j2",
                "validation": "templates/variants/nestjs/validation.ts.j2",
                "health": "templates/variants/nestjs/passwordless.health.ts.j2",
                "routes": "templates/variants/nestjs/passwordless.routes.ts.j2",
                "tests": "templates/variants/nestjs/passwordless.spec.ts.j2",
            },
            {
                "configuration": "src/modules/free/auth/passwordless/configuration.ts",
                "service": "src/modules/free/auth/passwordless/passwordless.service.ts",
                "module": "src/modules/free/auth/passwordless/passwordless.module.ts",
                "controller": "src/modules/free/auth/passwordless/passwordless.controller.ts",
                "index": "src/modules/free/auth/passwordless/index.ts",
                "validation": "src/modules/free/auth/passwordless/config/passwordless.validation.ts",
                "health": "src/health/passwordless.health.ts",
                "routes": "src/modules/free/auth/passwordless/passwordless.routes.ts",
                "tests": "test/passwordless/passwordless.spec.ts",
            },
            {
                "framework": "nestjs",
                "framework_display_name": "NestJS",
                "language": "typescript",
                "module_class_name": "Passwordless",
                "module_kebab": "passwordless",
                "auth_methods": ["email", "sms", "magic_link"],
                "token_expiry": 900,
                "rate_limiting": True,
            },
        ),
        (
            SessionFastAPIPlugin,
            {
                "session": "templates/variants/fastapi/session.py.j2",
                "session_types": "templates/base/session_types.py.j2",
                "routes": "templates/variants/fastapi/session_routes.py.j2",
                "config": "templates/variants/fastapi/session_config.yaml.j2",
                "integration_tests": "templates/tests/integration/test_session_integration.j2",
            },
            {
                "session": "src/modules/free/auth/session/session.py",
                "session_types": "src/modules/free/auth/session/session_types.py",
                "routes": "src/modules/free/auth/session/routers/session.py",
                "config": "config/session.yaml",
                "integration_tests": "tests/modules/integration/auth/session/test_session_integration.py",
            },
            {
                "framework": "fastapi",
                "framework_display_name": "FastAPI",
                "language": "python",
                "module_class_name": "Session",
                "session_backends": ["redis", "database", "memory"],
                "secure_cookies": True,
                "csrf_protection": True,
                "session_timeout": 3600,
            },
        ),
        (
            SessionNestJSPlugin,
            {
                "configuration": "templates/variants/nestjs/configuration.ts.j2",
                "service": "templates/variants/nestjs/session.service.ts.j2",
                "module": "templates/variants/nestjs/session.module.ts.j2",
                "controller": "templates/variants/nestjs/session.controller.ts.j2",
                "index": "templates/variants/nestjs/index.ts.j2",
                "validation": "templates/variants/nestjs/validation.ts.j2",
                "health": "templates/variants/nestjs/session.health.ts.j2",
                "routes": "templates/variants/nestjs/session.routes.ts.j2",
                "tests": "templates/variants/nestjs/session.spec.ts.j2",
            },
            {
                "configuration": "src/modules/free/auth/session/configuration.ts",
                "service": "src/modules/free/auth/session/session.service.ts",
                "module": "src/modules/free/auth/session/session.module.ts",
                "controller": "src/modules/free/auth/session/session.controller.ts",
                "index": "src/modules/free/auth/session/index.ts",
                "validation": "src/modules/free/auth/session/config/session.validation.ts",
                "health": "src/health/session.health.ts",
                "routes": "src/modules/free/auth/session/session.routes.ts",
                "tests": "test/session/session.spec.ts",
            },
            {
                "framework": "nestjs",
                "framework_display_name": "NestJS",
                "language": "typescript",
                "module_class_name": "Session",
                "module_kebab": "session",
                "session_backends": ["redis", "database", "memory"],
                "secure_cookies": True,
                "csrf_protection": True,
                "session_timeout": 3600,
            },
        ),
    ),
)
def test_other_auth_plugins_share_expected_traits(
    plugin_cls: type[FrameworkPlugin],
    template_mapping: Dict[str, str],
    output_mapping: Dict[str, str],
    context_expectations: Dict[str, Any],
) -> None:
    plugin = plugin_cls()

    assert plugin.get_template_mappings() == template_mapping
    assert plugin.get_output_paths() == output_mapping
    assert plugin.validate_requirements() == []

    base_context = {"rapidkit_vendor_configuration_relative": "vendor/config.json"}
    context = plugin.get_context_enrichments(base_context)

    for key, value in context_expectations.items():
        assert context[key] == value

    if context["framework"] == "nestjs":
        assert context["vendor_configuration_relative"] == "vendor/config.json"
    else:
        assert "vendor_configuration_relative" not in context


def test_get_plugin_rejects_unknown_framework() -> None:
    with pytest.raises(ValueError):
        get_plugin("unknown")
