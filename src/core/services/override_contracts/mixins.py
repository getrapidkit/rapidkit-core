# src/core/services/override_contracts/mixins.py
"""Mixin classes for safe module overrides.

These mixins provide base classes that can be extended to customize
module behavior in upgrade-safe ways.
"""

import inspect
from typing import Any, Dict

from .decorators import get_override_registry


class OverrideMixin:
    """Base mixin for classes that support method overrides.

    Classes inheriting from this mixin can have their methods
    overridden using the override decorators.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Initialize subclass with override support."""
        super().__init_subclass__(**kwargs)

        # Store original methods for overridden methods
        cls._store_original_methods()

    @classmethod
    def _store_original_methods(cls) -> None:
        """Store original versions of overridden methods."""
        # Find the first non-mixin base class
        base_class = None
        for base in cls.__mro__[1:]:  # Skip self
            if not issubclass(base, OverrideMixin):
                base_class = base
                break

        if base_class is None:
            return

        # Check each method in the subclass
        for attr_name in dir(cls):
            if not attr_name.startswith("_") and callable(getattr(cls, attr_name)):
                # If this method is defined in this class (not inherited)
                if attr_name in cls.__dict__ and hasattr(base_class, attr_name):
                    base_method = getattr(base_class, attr_name)

                    # Store original method if not already stored
                    original_attr = f"_original_{attr_name}"
                    if not hasattr(cls, original_attr):
                        setattr(cls, original_attr, base_method)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Initialize base classes first to establish original methods
        # Find the first non-mixin base class
        for base in self.__class__.__mro__[1:]:  # Skip self
            if not issubclass(base, OverrideMixin) and hasattr(base, "__init__"):
                base.__init__(self, *args, **kwargs)
                break

        # Then apply registry-based overrides
        self._apply_registry_overrides()

    def _apply_registry_overrides(self) -> None:
        """Apply any registered overrides to this instance."""
        registry = get_override_registry()

        # Apply method overrides
        for override_key, override_func in registry.method_overrides.items():
            if "." in override_key:
                target_class_name, method_name = override_key.split(".", 1)
                if target_class_name in [cls.__name__ for cls in self.__class__.__mro__]:
                    if hasattr(self, method_name):
                        # Store original method if not already stored
                        if not hasattr(self, f"_original_{method_name}"):
                            original_method = getattr(self, method_name)
                            setattr(self, f"_original_{method_name}", original_method)

                        # Apply override - bind to this instance
                        bound_override = override_func.__get__(self, self.__class__)
                        setattr(self, method_name, bound_override)

    def call_original(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call the original version of an overridden method.

        Args:
            method_name: Name of the method to call the original version of
            *args: Arguments to pass to the original method
            **kwargs: Keyword arguments to pass to the original method

        Returns:
            Result of calling the original method

        Raises:
            AttributeError: If no original method exists
        """
        original_method_name = f"_original_{method_name}"
        if not hasattr(self, original_method_name):
            raise AttributeError(f"No original method '{method_name}' found")

        original_method = getattr(self, original_method_name)
        return original_method(*args, **kwargs)


class SettingOverrideMixin:
    """Mixin for classes that support setting overrides.

    This mixin allows settings to be overridden using the override_setting decorator.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._load_setting_overrides()

    def _load_setting_overrides(self) -> None:
        """Load any registered setting overrides."""
        registry = get_override_registry()
        class_name = self.__class__.__name__

        # Apply setting overrides
        for setting_key, override_value in registry.setting_overrides.items():
            if setting_key.startswith(f"{class_name}."):
                setting_name = setting_key.split(".", 1)[1]

                # Store original value if it exists
                if hasattr(self, setting_name):
                    original_value = getattr(self, setting_name)
                    setattr(self, f"_original_{setting_name}", original_value)

                # Apply override
                if callable(override_value):
                    # Function-based override
                    computed_value = override_value()
                    setattr(self, setting_name, computed_value)
                else:
                    # Direct value override
                    setattr(self, setting_name, override_value)

    def get_original_setting(self, setting_name: str) -> Any:
        """Get the original value of an overridden setting.

        Args:
            setting_name: Name of the setting

        Returns:
            Original value of the setting

        Raises:
            AttributeError: If no original setting exists
        """
        original_setting_name = f"_original_{setting_name}"
        if not hasattr(self, original_setting_name):
            raise AttributeError(f"No original setting '{setting_name}' found")

        return getattr(self, original_setting_name)


class ConfigurableOverrideMixin(OverrideMixin, SettingOverrideMixin):
    """Combined mixin for both method and setting overrides.

    This mixin provides full override capabilities for configuration classes.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Initialize both parent mixins
        OverrideMixin.__init__(self)
        SettingOverrideMixin.__init__(self)

        # Call any additional initialization
        super().__init__(*args, **kwargs)

    def get_override_info(self) -> Dict[str, Any]:
        """Get information about applied overrides.

        Returns:
            Dictionary containing information about method and setting overrides
        """
        info: Dict[str, Any] = {"method_overrides": [], "setting_overrides": []}

        # Check for method overrides
        for attr_name in dir(self):
            if attr_name.startswith("_original_"):
                original_name = attr_name[10:]  # Remove "_original_" prefix
                info["method_overrides"].append({"method": original_name, "has_override": True})

        # Check for setting overrides
        registry = get_override_registry()
        class_name = self.__class__.__name__

        for setting_key in registry.setting_overrides:
            if setting_key.startswith(f"{class_name}."):
                setting_name = setting_key.split(".", 1)[1]
                info["setting_overrides"].append({"setting": setting_name, "has_override": True})

        return info


class ValidationOverrideMixin(OverrideMixin):
    """Mixin for validation classes with override support.

    This mixin adds validation for override compatibility.
    """

    def validate_overrides(self) -> Dict[str, Any]:
        """Validate that applied overrides are compatible.

        Returns:
            Dictionary with validation results
        """
        results: Dict[str, Any] = {"valid": True, "warnings": [], "errors": []}

        # Check method signature compatibility
        for attr_name in dir(self):
            if attr_name.startswith("_original_"):
                method_name = attr_name[10:]
                original_method = getattr(self, attr_name)
                current_method = getattr(self, method_name)

                # Check if signatures are compatible
                try:
                    original_sig = inspect.signature(original_method)
                    current_sig = inspect.signature(current_method)

                    if len(original_sig.parameters) != len(current_sig.parameters):
                        results["warnings"].append(
                            f"Method '{method_name}' signature changed: "
                            f"{len(original_sig.parameters)} -> {len(current_sig.parameters)} parameters"
                        )
                except (ValueError, TypeError):
                    results["warnings"].append(
                        f"Could not validate signature for method '{method_name}'"
                    )

        return results
