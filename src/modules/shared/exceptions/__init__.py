"""Shared error handling for all modules."""

from __future__ import annotations

from typing import Any, Dict, Optional


class ModuleError(Exception):
    """Base exception for module-related errors."""

    def __init__(self, message: str, *, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class ModuleConfigurationError(ModuleError):
    """Configuration file or environment variable errors."""


class ModuleValidationError(ModuleError):
    """Module validation errors."""


class ModuleGeneratorError(ModuleError):
    """Module template generation errors."""


# Settings-specific aliases for backward compatibility
class SettingsError(ModuleError):
    """Base exception for settings-related errors."""


class SettingsConfigurationError(ModuleConfigurationError):
    """Configuration file or environment variable errors."""


class SettingsValidationError(ModuleValidationError):
    """Settings validation errors."""


class SettingsGeneratorError(ModuleGeneratorError):
    """Settings template generation errors."""


class SettingsOverrideError(SettingsError):
    """Override registration or application errors."""


def format_error_with_context(error: ModuleError) -> str:
    """Format error message with helpful context information."""
    lines = [f"❌ {error.message}"]

    if error.context:
        lines.append("Context:")
        for key, value in error.context.items():
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)


def suggest_fix_for_common_errors(error: Exception) -> str:
    """Provide fix suggestions for common error patterns."""
    error_msg = str(error).lower()

    if "file not found" in error_msg or "no such file" in error_msg:
        return "💡 Try creating a .env file or checking the file path"

    if "yaml" in error_msg or "parsing" in error_msg:
        return "💡 Check YAML syntax - ensure proper indentation and valid structure"

    if "permission" in error_msg:
        return "💡 Check file permissions or run with appropriate privileges"

    if "connection" in error_msg or "network" in error_msg:
        return "💡 Verify network connectivity and authentication credentials"

    if "override" in error_msg:
        return "💡 Check override registration - ensure module is properly imported"

    return "💡 Check logs above for detailed error information"
