# pyright: reportMissingImports=false
"""Framework plugin registry for the Email module."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
from typing import Dict, Iterable, Optional, Type

from modules.shared.frameworks import FrameworkPlugin, PluginRegistry

from .fastapi import FastAPIDDDPlugin, FastAPIPlugin, FastAPIStandardPlugin
from .nestjs import NestJSPlugin, NestJSStandardPlugin

PLUGIN_ENTRYPOINT_GROUP = "rapidkit.modules.free.communication.email.plugins"

_REGISTRY: PluginRegistry = PluginRegistry(entry_point_group=PLUGIN_ENTRYPOINT_GROUP)
_BUILTIN_PLUGINS: tuple[Type[FrameworkPlugin], ...] = (
    FastAPIPlugin,
    FastAPIStandardPlugin,
    FastAPIDDDPlugin,
    NestJSPlugin,
    NestJSStandardPlugin,
)


def register_plugin(plugin_class: Type[FrameworkPlugin]) -> None:
    """Register a framework plugin for the Email module."""

    _REGISTRY.register(plugin_class)


def refresh_plugin_registry(*, auto_discover: bool = True) -> None:
    """Reset registry contents and repopulate built-in and external plugins."""

    _REGISTRY.refresh(builtins=_BUILTIN_PLUGINS, auto_discover=auto_discover)


def discover_external_plugins(
    entry_points_iterable: Optional[Iterable[importlib_metadata.EntryPoint]] = None,
) -> list[str]:
    """Discover external plugins using provided entry points (primarily for testing)."""

    return _REGISTRY.discover(entry_points=entry_points_iterable)


def get_plugin(framework_name: str) -> FrameworkPlugin:
    """Return an instantiated plugin for the framework name."""

    return _REGISTRY.get(framework_name)


def list_available_plugins() -> Dict[str, str]:
    """Return mapping of registered plugin names to display names."""

    return _REGISTRY.list_available()


refresh_plugin_registry(auto_discover=False)
