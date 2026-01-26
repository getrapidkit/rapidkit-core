"""Framework plugin registry for the Ai Assistant module."""

from __future__ import annotations

from modules.shared.frameworks import FrameworkPlugin, PluginRegistry

from .fastapi import FastAPIDDDPlugin, FastAPIPlugin, FastAPIStandardPlugin
from .nestjs import NestJSPlugin, NestJSStandardPlugin

PLUGIN_ENTRYPOINT_GROUP = "rapidkit.ai_assistant.plugins"

_REGISTRY = PluginRegistry(entry_point_group=PLUGIN_ENTRYPOINT_GROUP)
_BUILTIN_PLUGINS = (
    FastAPIPlugin,
    FastAPIStandardPlugin,
    FastAPIDDDPlugin,
    NestJSPlugin,
    NestJSStandardPlugin,
)


def register_plugin(plugin_class: type[FrameworkPlugin]) -> None:
    """Register an additional framework plugin."""

    _REGISTRY.register(plugin_class)


def refresh_plugin_registry(*, auto_discover: bool = True) -> None:
    """Refresh registry contents and re-register built-in implementations."""

    _REGISTRY.refresh(builtins=_BUILTIN_PLUGINS, auto_discover=auto_discover)


def get_plugin(framework_name: str) -> FrameworkPlugin:
    """Return an instantiated plugin for the framework identifier."""

    return _REGISTRY.get(framework_name)


def list_available_plugins() -> dict[str, str]:
    """Return available plugins mapped to their display names."""

    return _REGISTRY.list_available()


refresh_plugin_registry(auto_discover=False)


__all__ = [
    "FrameworkPlugin",
    "register_plugin",
    "refresh_plugin_registry",
    "get_plugin",
    "list_available_plugins",
]
