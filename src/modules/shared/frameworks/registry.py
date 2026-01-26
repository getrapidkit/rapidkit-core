"""Reusable plugin registry for framework-aware modules."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import logging
from dataclasses import dataclass, field
from typing import Iterable, List, MutableMapping, Optional, Type, cast

from .base import FrameworkPlugin

logger = logging.getLogger(__name__)  # pylint: disable=E1101


@dataclass
class PluginRegistry:
    """Registry that manages framework plugins."""

    entry_point_group: Optional[str] = None
    _plugins: MutableMapping[str, Type[FrameworkPlugin]] = field(default_factory=dict)

    def register(self, plugin_class: Type[FrameworkPlugin]) -> None:
        """Register a plugin class by its declared name."""

        try:
            instance = plugin_class()
            plugin_name = instance.name
        except (TypeError, AttributeError, ValueError) as exc:
            raise ValueError(f"Failed to instantiate plugin to read name: {exc}") from exc

        existing = self._plugins.get(plugin_name)
        if existing is not None and existing is not plugin_class:
            raise ValueError(
                "Plugin '%s' is already registered by %s.%s"
                % (
                    plugin_name,
                    existing.__module__,
                    existing.__name__,
                )
            )

        self._plugins[plugin_name] = plugin_class
        logger.debug("Registered framework plugin: %s", plugin_name)

    def get(self, framework_name: str) -> FrameworkPlugin:
        """Return an instantiated plugin for the provided name."""

        plugin_class = self._plugins.get(framework_name)
        if plugin_class is None:
            available = list(self._plugins.keys())
            raise ValueError(
                f"Unknown framework '{framework_name}'. Available frameworks: {available}"
            )

        try:
            return plugin_class()
        except (TypeError, AttributeError, ValueError) as exc:
            raise RuntimeError(f"Failed to instantiate plugin '{framework_name}': {exc}") from exc

    def list_available(self) -> dict[str, str]:
        """Return mapping of registered plugin names to display names."""

        result: dict[str, str] = {}
        for name, plugin_class in self._plugins.items():
            try:
                result[name] = plugin_class().display_name
            except (TypeError, AttributeError, ValueError):
                result[name] = name
        return result

    def get_class(self, framework_name: str) -> Type[FrameworkPlugin]:
        """Return the underlying plugin class without instantiating."""

        plugin_class = self._plugins.get(framework_name)
        if plugin_class is None:
            available = list(self._plugins.keys())
            raise ValueError(
                f"Unknown framework '{framework_name}'. Available frameworks: {available}"
            )
        return plugin_class

    def is_available(self, framework_name: str) -> bool:
        """Return True if the framework plugin is registered."""

        return framework_name in self._plugins

    def validate_all(self) -> dict[str, List[str]]:
        """Return validation results for every registered plugin."""

        results: dict[str, List[str]] = {}
        for name, plugin_class in self._plugins.items():
            try:
                plugin_instance = plugin_class()
                results[name] = plugin_instance.validate_requirements()
            except (TypeError, AttributeError, ValueError) as exc:
                results[name] = [f"Plugin instantiation failed: {exc}"]
        return results

    def discover(
        self, *, entry_points: Optional[Iterable[importlib_metadata.EntryPoint]] = None
    ) -> List[str]:
        """Load external plugin classes, returning successfully registered names."""

        if self.entry_point_group is None and entry_points is None:
            return []

        registered: List[str] = []

        if entry_points is None:
            try:
                raw_entry_points = importlib_metadata.entry_points()
            except (ImportError, RuntimeError, ValueError) as exc:  # pragma: no cover
                logger.debug("Failed to load entry points: %s", exc)
                return []

            if self.entry_point_group is None:
                return []

            if hasattr(raw_entry_points, "select"):
                entry_points = cast(
                    Iterable[importlib_metadata.EntryPoint],
                    raw_entry_points.select(group=self.entry_point_group),
                )
            else:  # pragma: no cover - legacy interface
                legacy_points = raw_entry_points.get(self.entry_point_group, ())
                entry_points = cast(Iterable[importlib_metadata.EntryPoint], legacy_points)

        for entry_point in entry_points or []:
            try:
                plugin_class = entry_point.load()
            except (ImportError, AttributeError, ValueError) as exc:  # pragma: no cover
                logger.warning(
                    "Skipping settings plugin '%s' due to import error: %s", entry_point, exc
                )
                continue

            if not isinstance(plugin_class, type) or not issubclass(plugin_class, FrameworkPlugin):
                logger.warning(
                    "Entry point '%s' did not resolve to a FrameworkPlugin subclass", entry_point
                )
                continue

            try:
                self.register(plugin_class)
            except ValueError as exc:
                logger.warning("Skipping duplicate plugin '%s': %s", plugin_class.__name__, exc)
                continue

            registered.append(plugin_class.__name__)

        return registered

    def reset(self) -> None:
        """Clear current registrations."""

        self._plugins.clear()

    def refresh(
        self, *, builtins: Iterable[Type[FrameworkPlugin]] = (), auto_discover: bool = True
    ) -> None:
        """Reset and repopulate the registry."""

        self.reset()
        for plugin_class in builtins:
            self.register(plugin_class)

        if auto_discover:
            self.discover()


__all__ = ["FrameworkPlugin", "PluginRegistry"]
