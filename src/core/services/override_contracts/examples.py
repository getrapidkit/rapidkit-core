# src/core/services/override_contracts/examples.py
"""Examples of using override contracts for safe module customization.

This module demonstrates how to use the override decorators and mixins
to customize module behavior in upgrade-safe ways.
"""

from typing import Any, Dict, cast

from .decorators import override_method, override_setting
from .mixins import ConfigurableOverrideMixin


# Example 1: Using decorators for method overrides
class CustomSettings:
    """Example of a custom settings class using override decorators."""

    def __init__(self) -> None:
        self.debug_mode = False
        self.database_url = "sqlite:///default.db"

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from various sources."""
        return {"debug": self.debug_mode, "database_url": self.database_url, "app_name": "MyApp"}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration."""
        return isinstance(config, dict) and "app_name" in config


# Override examples using decorators
@override_setting("CustomSettings.debug_mode")
def custom_debug_mode() -> bool:
    """Custom debug mode logic."""
    import os

    return os.getenv("MYAPP_DEBUG", "false").lower() == "true"


@override_method("CustomSettings.load_config")
def custom_load_config(self: CustomSettings) -> Dict[str, Any]:
    """Custom config loading with additional settings."""
    config = self.load_config()  # Call original
    config.update({"custom_feature": True, "environment": "production"})
    return config


# Example 2: Using mixins for class-based overrides
class BaseService:
    """Base service class."""

    def __init__(self) -> None:
        self.timeout = 30
        self.retries = 3

    def make_request(self, url: str) -> Dict[str, Any]:
        """Make an HTTP request."""
        return {"url": url, "timeout": self.timeout, "retries": self.retries, "status": "success"}


class CustomService(BaseService, ConfigurableOverrideMixin):
    """Custom service using override mixin."""

    def make_request(self, url: str) -> Dict[str, Any]:
        """Custom request logic with logging."""
        # Call the original method using the mixin method
        result = cast(Dict[str, Any], self.call_original("make_request", url))
        result["logged"] = True
        result["custom_header"] = "X-Custom-Service"
        return result


# Example 3: Complete override example
class SettingsManager(ConfigurableOverrideMixin):
    """Settings manager with full override support."""

    def __init__(self) -> None:
        super().__init__()
        self.app_name = "DefaultApp"
        self.version = "1.0.0"
        self.features = ["basic"]

    def get_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        return {"app_name": self.app_name, "version": self.version, "features": self.features}

    def validate_settings(self) -> bool:
        """Validate current settings."""
        settings = self.get_settings()
        return (
            isinstance(settings.get("app_name"), str)
            and isinstance(settings.get("version"), str)
            and isinstance(settings.get("features"), list)
        )


# Apply overrides to classes
# apply_overrides(CustomService)  # Not needed with mixins
# apply_overrides(SettingsManager)  # Not needed with mixins


# Example usage function
def demonstrate_overrides() -> None:
    """Demonstrate how overrides work."""

    print("=== Override Contracts Demo ===\n")

    # Example 1: Custom Settings with decorators
    print("1. Custom Settings with decorators:")
    settings = CustomSettings()
    config = settings.load_config()
    print(f"Config: {config}")
    print(f"Debug mode: {settings.debug_mode}")
    print()

    # Example 2: Custom Service with mixins
    print("2. Custom Service with mixins:")
    service = CustomService()
    result = service.make_request("https://api.example.com")
    print(f"Request result: {result}")
    print(f"Override info: {service.get_override_info()}")
    print()

    # Example 3: Settings Manager with full overrides
    print("3. Settings Manager with full overrides:")
    manager = SettingsManager()
    settings_dict = manager.get_settings()
    print(f"Settings: {settings_dict}")
    print(f"Validation: {manager.validate_settings()}")
    print(f"Override info: {manager.get_override_info()}")
    print()

    print("=== Demo Complete ===")


if __name__ == "__main__":
    demonstrate_overrides()
