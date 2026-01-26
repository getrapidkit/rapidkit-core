# pyright: reportMissingImports=false
"""Framework plugin registry for the Session module."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
from typing import Dict, Iterable, Optional, Type

from modules.shared.frameworks import FrameworkPlugin, PluginRegistry

from .fastapi import FastAPIPlugin
from .nestjs import NestJSPlugin

PLUGIN_ENTRYPOINT_GROUP = "rapidkit.modules.free.auth.session.plugins"

_REGISTRY: PluginRegistry = PluginRegistry(entry_point_group=PLUGIN_ENTRYPOINT_GROUP)
_BUILTIN_PLUGINS: tuple[Type[FrameworkPlugin], ...] = (FastAPIPlugin, NestJSPlugin)


def register_plugin(plugin_class: Type[FrameworkPlugin]) -> None:
    """Register a framework plugin for the Session module."""

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


def get_plugin_class(framework_name: str) -> Type[FrameworkPlugin]:
    """Return the plugin class for the provided framework name."""

    return _REGISTRY.get_class(framework_name)


def is_plugin_available(framework_name: str) -> bool:
    """Report whether a plugin is registered for the given name."""

    return _REGISTRY.is_available(framework_name)


def validate_all_plugins() -> Dict[str, list[str]]:
    """Run requirement validation across all registered plugins."""

    return _REGISTRY.validate_all()


def get_plugin_info(framework_name: str) -> Optional[Dict[str, object]]:
    """Return metadata describing a registered plugin, if available."""

    if not _REGISTRY.is_available(framework_name):
        return None

    plugin = _REGISTRY.get(framework_name)
    return {
        "name": plugin.name,
        "language": plugin.language,
        "display_name": plugin.display_name,
        "dependencies": plugin.get_dependencies(),
        "dev_dependencies": plugin.get_dev_dependencies(),
        "documentation_urls": plugin.get_documentation_urls(),
        "validation_errors": plugin.validate_requirements(),
    }


refresh_plugin_registry()


__all__ = [
    "FrameworkPlugin",
    "register_plugin",
    "refresh_plugin_registry",
    "discover_external_plugins",
    "get_plugin",
    "list_available_plugins",
    "get_plugin_class",
    "is_plugin_available",
    "validate_all_plugins",
    "get_plugin_info",
]
