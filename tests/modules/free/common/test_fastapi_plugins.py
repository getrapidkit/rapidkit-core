"""Shared coverage tests for FastAPI framework plugins across free modules."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Dict, Iterable

import pytest

BASE_CONTEXT: Dict[str, str] = {
    "rapidkit_vendor_relative_path": "src/vendor/runtime.py",
    "rapidkit_vendor_configuration_relative": "config/vendor.yaml",
    "rapidkit_vendor_health_relative": "src/vendor/health.py",
    "rapidkit_vendor_types_relative": "src/vendor/types.py",
    "fastapi_config_relative": "config/runtime.yaml",
    "fastapi_test_relative": "tests/runtime_test.py",
}

FASTAPI_CASES = [
    (
        "modules.free.auth.passwordless.frameworks.fastapi",
        (
            "src/modules/free/auth/passwordless",
            "src/modules/free/auth/passwordless/routers",
            "config",
            "tests/modules/integration/auth/passwordless",
            "src/health",
        ),
        {"auth_methods", "token_expiry", "rate_limiting"},
    ),
    (
        "modules.free.auth.session.frameworks.fastapi",
        (
            "src/modules/free/auth/session",
            "src/modules/free/auth/session/routers",
            "config",
            "tests/modules/integration/auth/session",
            "src/health",
        ),
        {"session_backends", "csrf_protection", "session_timeout"},
    ),
    (
        "modules.free.auth.oauth.frameworks.fastapi",
        (
            "src/modules/free/auth/oauth",
            "src/modules/free/auth/oauth/routers",
            "config",
            "tests/modules/integration/auth/oauth",
            "src/health",
        ),
        {"oauth_providers", "jwt_support", "state_management"},
    ),
    (
        "modules.free.users.users_core.frameworks.fastapi",
        (
            "src/modules/free/users/users_core",
            "src/modules/free/users/users_core/core/users",
            "src/modules/free/users/users_core/config",
            "tests/modules/free/users/users_core",
            "src/health",
        ),
        {"vendor_runtime_relative", "vendor_configuration_relative", "integration_test_relative"},
    ),
    (
        "modules.free.users.users_profiles.frameworks.fastapi",
        (
            "src/modules/free/users/users_profiles",
            "src/modules/free/users/users_profiles/core/users/profiles",
            "config/users",
            "tests/modules/integration/users",
            "src/health",
        ),
        {"vendor_runtime_relative", "config_relative", "integration_test_relative"},
    ),
]


@pytest.mark.parametrize("module_path, expected_paths, expected_context_keys", FASTAPI_CASES)
def test_fastapi_plugins_cover_generation(
    module_path: str,
    expected_paths: Iterable[str],
    expected_context_keys: Iterable[str],
    tmp_path: Path,
) -> None:
    module = importlib.import_module(module_path)
    plugin = module.FastAPIPlugin()

    context = plugin.get_context_enrichments(dict(BASE_CONTEXT))
    for key in expected_context_keys:
        assert key in context

    assert plugin.name == "fastapi"
    assert plugin.language == "python"
    assert plugin.display_name == "FastAPI"
    assert plugin.get_template_mappings()
    assert plugin.get_output_paths()
    assert plugin.validate_requirements() == []

    plugin.pre_generation_hook(tmp_path)
    for relative in expected_paths:
        assert (tmp_path / relative).exists()

    health_init = tmp_path / "src" / "health" / "__init__.py"
    assert health_init.exists()

    plugin.post_generation_hook(tmp_path)

    if hasattr(plugin, "get_documentation_urls"):
        urls = plugin.get_documentation_urls()  # type: ignore[attr-defined]
        assert isinstance(urls, dict)
    if hasattr(plugin, "get_dependencies"):
        deps = plugin.get_dependencies()  # type: ignore[attr-defined]
        assert isinstance(deps, list)
    if hasattr(plugin, "get_dev_dependencies"):
        dev_deps = plugin.get_dev_dependencies()  # type: ignore[attr-defined]
        assert isinstance(dev_deps, list)
