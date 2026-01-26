# src/core/services/override_contracts/decorators.py
"""Decorators for safe module overrides.

These decorators allow users to override module methods and settings
in ways that survive module updates.
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast


class _BoundClassMethod:
    """Wrapper preserving classmethod binding semantics for stored originals."""

    def __init__(self, descriptor: classmethod, owner: Type) -> None:
        self._descriptor = descriptor
        self._owner = owner

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        bound = self._descriptor.__get__(None, self._owner)
        return bound(*args, **kwargs)

    def __get__(self, obj: Any, cls: Optional[Type] = None) -> Any:
        target = cls or self._owner
        return self._descriptor.__get__(None, target)


class _StoredClassMethod:
    """Descriptor that returns a rebinding wrapper for original classmethods."""

    def __init__(self, descriptor: classmethod) -> None:
        self._descriptor = descriptor

    def __get__(self, obj: Any, cls: Optional[Type] = None) -> _BoundClassMethod:
        owner = cls or type(obj)
        return _BoundClassMethod(self._descriptor, owner)


F = TypeVar("F", bound=Callable[..., Any])


class OverrideRegistry:
    """Registry for tracking method and setting overrides."""

    def __init__(self) -> None:
        self.method_overrides: Dict[str, Callable] = {}
        self.setting_overrides: Dict[str, Any] = {}

    def register_method_override(self, original_name: str, override_func: Callable) -> None:
        """Register a method override."""
        self.method_overrides[original_name] = override_func

    def register_setting_override(self, setting_name: str, override_value: Any) -> None:
        """Register a setting override."""
        self.setting_overrides[setting_name] = override_value

    def get_method_override(self, original_name: str) -> Optional[Callable]:
        """Get a registered method override."""
        return self.method_overrides.get(original_name)

    def get_setting_override(self, setting_name: str) -> Optional[Any]:
        """Get a registered setting override."""
        return self.setting_overrides.get(setting_name)


# Global registry instance
_override_registry = OverrideRegistry()


def override_method(original_method: Union[str, Callable]) -> Callable[[F], F]:
    """Decorator to override a module method safely.

    Args:
        original_method: Name of the method to override, or the method itself

    Example:
        @override_method("Settings.load_config")
        def custom_load_config(self):
            # Custom implementation
            config = super().load_config()
            config.update({"custom_setting": True})
            return config
    """

    def decorator(func: F) -> F:
        method_name = (
            original_method if isinstance(original_method, str) else original_method.__name__
        )
        _override_registry.register_method_override(method_name, func)

        # Mark the function as an override for introspection
        metadata = cast(Any, func)
        metadata._is_override = True
        metadata._override_target = method_name

        return func

    return decorator


def override_setting(setting_name: str, setting_value: Any = None) -> Callable[[F], F]:
    """Decorator to override a module setting safely.

    Args:
        setting_name: Name of the setting to override
        setting_value: Value to override with (if not provided, decorated function return value is used)

    Example:
        @override_setting("Settings.DEBUG_MODE")
        def custom_debug_mode():
            return os.getenv("MY_DEBUG", "false").lower() == "true"
    """

    def decorator(func: F) -> F:
        if setting_value is not None:
            # Direct value override
            _override_registry.register_setting_override(setting_name, setting_value)
        else:
            # Function-based override
            _override_registry.register_setting_override(setting_name, func)

        # Mark the function as a setting override
        metadata = cast(Any, func)
        metadata._is_setting_override = True
        metadata._override_setting = setting_name

        return func

    return decorator


def safe_override(target_class: Type, method_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator for safe method overrides with automatic conflict detection.

    Args:
        target_class: The class containing the method to override
        method_name: Name of the method to override (defaults to decorated function name)

    Example:
        class CustomSettings(Settings):
            @safe_override(Settings, "load_config")
            def load_config(self):
                config = super().load_config()
                config["custom"] = True
                return config
    """

    def decorator(func: F) -> F:
        actual_method_name = method_name or func.__name__

        # Check if target method exists
        if not hasattr(target_class, actual_method_name):
            raise ValueError(f"Method '{actual_method_name}' not found in {target_class.__name__}")

        # Store override information
        metadata = cast(Any, func)
        metadata._safe_override_target = target_class
        metadata._safe_override_method = actual_method_name

        # Register in global registry
        registry_key = f"{target_class.__name__}.{actual_method_name}"
        _override_registry.register_method_override(registry_key, func)

        return func

    return decorator


def get_override_registry() -> OverrideRegistry:
    """Get the global override registry."""
    return _override_registry


def _find_descriptor(target_class: Type, attribute: str) -> Optional[Any]:
    """Locate the descriptor for an attribute in a class hierarchy."""

    for ancestor in target_class.__mro__:
        namespace = getattr(ancestor, "__dict__", {})
        if attribute in namespace:
            return namespace[attribute]
    return None


def apply_overrides(target_class: Type) -> Type:
    """Apply registered overrides to a class.

    This function should be called after class definition to apply
    any registered overrides.

    Args:
        target_class: The class to apply overrides to

    Returns:
        The class with overrides applied
    """
    registry = get_override_registry()

    # Apply method overrides
    for override_key, override_func in registry.method_overrides.items():
        if "." in override_key:
            target_class_name, method_name = override_key.split(".", 1)
            if target_class_name in [cls.__name__ for cls in target_class.__mro__]:
                if hasattr(target_class, method_name):
                    # Store original method on class
                    original_method = getattr(target_class, method_name)
                    setattr(target_class, f"_original_{method_name}", original_method)

                    # Apply override
                    setattr(target_class, method_name, override_func)

    # Apply setting overrides
    for setting_key, override_value in registry.setting_overrides.items():
        if "." in setting_key:
            target_class_name, setting_name = setting_key.split(".", 1)
            if target_class_name in [cls.__name__ for cls in target_class.__mro__]:
                # Store original value if it exists as class attribute
                if hasattr(target_class, setting_name):
                    original_value = getattr(target_class, setting_name)
                    descriptor = _find_descriptor(target_class, setting_name)
                    if isinstance(descriptor, classmethod):
                        stored_original = _StoredClassMethod(descriptor)
                    else:
                        stored_original = original_value
                    setattr(target_class, f"_original_{setting_name}", stored_original)

                # Apply override as class attribute
                if callable(override_value):
                    # For callable overrides, set as class method
                    setattr(target_class, setting_name, classmethod(override_value))
                else:
                    # For value overrides, set as class attribute
                    setattr(target_class, setting_name, override_value)

    return target_class
