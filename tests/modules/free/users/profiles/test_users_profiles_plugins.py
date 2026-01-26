"""Plugin tests for Users Profiles module."""

from __future__ import annotations

import importlib
from pathlib import Path


def _load_frameworks_module():
    return importlib.import_module("modules.free.users.users_profiles.frameworks")


def test_fastapi_plugin_pre_generation(tmp_path: Path) -> None:
    frameworks = _load_frameworks_module()
    frameworks.refresh_plugin_registry(auto_discover=False)
    plugin = frameworks.get_plugin("fastapi")

    plugin.pre_generation_hook(tmp_path)

    health_init = (tmp_path / "src" / "health" / "__init__.py").read_text(encoding="utf-8")
    assert "register_users_profiles_health" in health_init
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "users"
        / "users_profiles"
        / "core"
        / "users"
        / "profiles"
    ).is_dir()


def test_nestjs_plugin_pre_generation(tmp_path: Path) -> None:
    frameworks = _load_frameworks_module()
    frameworks.refresh_plugin_registry(auto_discover=False)
    plugin = frameworks.get_plugin("nestjs")

    plugin.pre_generation_hook(tmp_path)

    assert (
        tmp_path / "src" / "modules" / "free" / "users" / "users_profiles" / "users_profiles"
    ).is_dir()
    assert plugin.get_dependencies(), "nestjs plugin should declare dependencies"
