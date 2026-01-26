# src/core/services/override_contracts/__init__.py
"""Override contracts for safe module customization.

This package provides decorators and mixins for creating upgrade-safe
customizations of RapidKit modules.
"""

from __future__ import annotations

import logging
from types import ModuleType
from typing import Type, TypeVar, Union

from .decorators import (
    apply_overrides,
    get_override_registry,
    override_method,
    override_setting,
    safe_override,
)
from .mixins import (
    ConfigurableOverrideMixin,
    OverrideMixin,
    SettingOverrideMixin,
    ValidationOverrideMixin,
)

LOGGER = logging.getLogger(__name__)

__all__ = [
    # Decorators
    "override_method",
    "override_setting",
    "safe_override",
    "apply_overrides",
    "get_override_registry",
    # Mixins
    "OverrideMixin",
    "SettingOverrideMixin",
    "ConfigurableOverrideMixin",
    "ValidationOverrideMixin",
    # Module integration
    "load_module_overrides",
    "apply_module_overrides",
]


def load_module_overrides(module_name: str) -> None:
    """Load override contracts from a module's overrides.py file.

    This function attempts to import and execute a module's overrides.py file,
    which should contain decorator-based override definitions.

    Args:
        module_name: Name of the module to load overrides for (e.g., 'settings')
    """
    try:
        # Try to import the module's overrides
        import importlib

        importlib.import_module(f"modules.free.essentials.{module_name}.overrides")

        # The act of importing executes any decorators at module level
        # No additional action needed - decorators register themselves

    except (ImportError, ModuleNotFoundError):
        # No overrides file for this module - that's fine
        pass
    except Exception as exc:  # noqa: BLE001 - defensive guard against user overrides
        # Log but don't fail - overrides are optional
        LOGGER.warning("Failed to load overrides for module %s: %s", module_name, exc)


_T = TypeVar("_T")


def apply_module_overrides(
    target: Union[Type[_T], ModuleType], module_name: str
) -> Union[Type[_T], ModuleType]:
    """Apply overrides for a specific module to a target class.

    Args:
        target_class: The class to apply overrides to
        module_name: Name of the module providing the overrides

    Returns:
        The class with overrides applied
    """
    load_module_overrides(module_name)

    if isinstance(target, ModuleType):
        LOGGER.debug(
            "No class binding supplied for module %s; loaded overrides without applying.",
            module_name,
        )
        return target

    return apply_overrides(target)
