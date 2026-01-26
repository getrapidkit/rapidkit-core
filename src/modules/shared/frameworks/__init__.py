"""Shared framework plugin infrastructure."""

from .base import FrameworkPlugin
from .registry import PluginRegistry

__all__ = ["FrameworkPlugin", "PluginRegistry"]
