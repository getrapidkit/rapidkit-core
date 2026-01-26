"""Framework plugins for db_postgres module."""

from __future__ import annotations

from typing import Dict, Optional, Type

from modules.shared.frameworks import FrameworkPlugin, PluginRegistry

from .fastapi import FastAPIPlugin
from .nestjs import NestJSPlugin

_BUILTIN_PLUGINS: tuple[Type[FrameworkPlugin], ...] = (FastAPIPlugin, NestJSPlugin)
_REGISTRY: PluginRegistry = PluginRegistry(
    entry_point_group="rapidkit.modules.free.database.db_postgres.plugins"
)


def register_plugin(plugin_class: Type[FrameworkPlugin]) -> None:
    """Register a framework plugin for this module."""
    _REGISTRY.register(plugin_class)


def refresh_plugin_registry(*, auto_discover: bool = True) -> None:
    """Reset registry contents and repopulate built-in and external plugins."""
    _REGISTRY.refresh(builtins=_BUILTIN_PLUGINS, auto_discover=auto_discover)


def get_plugin(framework_name: str) -> Optional[FrameworkPlugin]:
    """Get framework plugin by name."""
    if not _REGISTRY.is_available(framework_name):
        refresh_plugin_registry(auto_discover=False)
    return _REGISTRY.get(framework_name) if _REGISTRY.is_available(framework_name) else None


def list_available_plugins() -> Dict[str, FrameworkPlugin]:
    """List all available framework plugins."""
    if len(_REGISTRY._plugins) == 0:
        refresh_plugin_registry(auto_discover=False)
    return {name: _REGISTRY.get(name) for name in _REGISTRY._plugins}
