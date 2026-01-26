"""Tests for module path resolver logic."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from core.services import module_path_resolver
from core.services.config_loader import MODULES_PATH


@pytest.fixture(autouse=True)
def clear_registry_cache() -> None:
    module_path_resolver._get_registry_for_tier.cache_clear()


class DummyRegistry:
    def __init__(self, modules: Dict[str, Dict[str, Any]]) -> None:
        self._modules = modules

    def get_module(self, slug: str) -> Optional[Dict[str, Any]]:
        return self._modules.get(slug)


def test_resolve_free_module_uses_templates_path() -> None:
    module_dir = module_path_resolver.resolve_module_directory(
        MODULES_PATH, "free/essentials/settings"
    )

    expected = MODULES_PATH / "free" / "essentials" / "settings"
    assert module_dir == expected
    assert module_dir.exists()


def test_resolve_module_directory_direct_hit(tmp_path: Path) -> None:
    module_dir = tmp_path / "analytics"
    module_dir.mkdir()

    resolved = module_path_resolver.resolve_module_directory(tmp_path, "analytics")

    assert resolved == module_dir


def test_resolve_module_directory_uses_registry_templates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = DummyRegistry({"auth": {"templates_path": "core/auth"}})
    monkeypatch.setattr(module_path_resolver, "_get_registry_for_tier", lambda _tier: registry)

    target_dir = tmp_path / "free/essentials/auth"
    target_dir.mkdir(parents=True)

    resolved = module_path_resolver.resolve_module_directory(tmp_path, "free/auth")

    assert resolved == target_dir


def test_resolve_module_directory_registry_nested_slug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = DummyRegistry({"essentials": {"templates_path": "essentials"}})
    monkeypatch.setattr(module_path_resolver, "_get_registry_for_tier", lambda _tier: registry)

    target_dir = tmp_path / "free/essentials"
    target_dir.mkdir(parents=True)

    resolved = module_path_resolver.resolve_module_directory(tmp_path, "free/essentials/settings")

    assert resolved == target_dir


def test_resolve_module_directory_fallback_walk(tmp_path: Path) -> None:
    nested_dir = tmp_path / "free/insights/reports"
    nested_dir.mkdir(parents=True)

    resolved = module_path_resolver.resolve_module_directory(tmp_path, "free/insights/reports")

    assert resolved == nested_dir


def test_resolve_missing_module_defaults_to_candidate(tmp_path: Path) -> None:
    modules_root = tmp_path / "modules"
    modules_root.mkdir()

    result = module_path_resolver.resolve_module_directory(modules_root, "free/nonexistent")
    expected = modules_root / "free" / "nonexistent"

    assert result == expected
    assert not result.exists()
