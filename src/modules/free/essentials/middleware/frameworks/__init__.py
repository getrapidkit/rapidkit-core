"""Framework plugins for middleware module."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
from typing import Dict, Iterable, Optional, Type

from modules.shared.frameworks import FrameworkPlugin, PluginRegistry

from .fastapi import FastAPIDDDPlugin, FastAPIPlugin, FastAPIStandardPlugin
from .nestjs import NestJSPlugin, NestJSStandardPlugin

PLUGIN_ENTRYPOINT_GROUP = "rapidkit.modules.free.essentials.middleware.plugins"

_REGISTRY: PluginRegistry = PluginRegistry(entry_point_group=PLUGIN_ENTRYPOINT_GROUP)
_BUILTIN_PLUGINS: tuple[Type[FrameworkPlugin], ...] = (
    FastAPIPlugin,
    FastAPIStandardPlugin,
    FastAPIDDDPlugin,
    NestJSPlugin,
    NestJSStandardPlugin,
)


def register_plugin(plugin_class: Type[FrameworkPlugin]) -> None:
    """Register a framework plugin for this module."""

    _REGISTRY.register(plugin_class)


def refresh_plugin_registry(*, auto_discover: bool = True) -> None:
    """Reset registry contents and repopulate built-in and external plugins."""

    _REGISTRY.refresh(builtins=_BUILTIN_PLUGINS, auto_discover=auto_discover)


def discover_external_plugins(
    entry_points_iterable: Optional[Iterable[importlib_metadata.EntryPoint]] = None,
) -> list[str]:
    """Discover external plugins using provided entry points (primarily for tests)."""

    return _REGISTRY.discover(entry_points=entry_points_iterable)


def get_plugin(framework_name: str) -> FrameworkPlugin:
    """Return the plugin instance for a given framework name."""

    return _REGISTRY.get(framework_name)


def list_available_plugins() -> Dict[str, str]:
    """Return mapping of plugin name to display name."""

    return _REGISTRY.list_available()


def get_plugin_class(framework_name: str) -> Type[FrameworkPlugin]:
    """Return the plugin class for a given framework name."""

    return _REGISTRY.get_class(framework_name)


def is_plugin_available(framework_name: str) -> bool:
    """Return True if a plugin is registered for the requested name."""

    return _REGISTRY.is_available(framework_name)


def validate_all_plugins() -> Dict[str, list[str]]:
    """Run validation across all registered plugins."""

    return _REGISTRY.validate_all()


refresh_plugin_registry(auto_discover=False)

__all__ = [
    "FrameworkPlugin",
    "register_plugin",
    "refresh_plugin_registry",
    "discover_external_plugins",
    "get_plugin",
    "get_plugin_class",
    "list_available_plugins",
    "is_plugin_available",
    "validate_all_plugins",
]
