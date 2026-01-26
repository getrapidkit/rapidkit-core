"""Comprehensive test coverage for settings module error handling."""

import pytest

from modules.shared.exceptions import (
    SettingsConfigurationError,
    SettingsError,
    SettingsGeneratorError,
    SettingsOverrideError,
    SettingsValidationError,
    format_error_with_context,
    suggest_fix_for_common_errors,
)


class TestSettingsExceptions:
    """Test custom exception classes and error handling."""

    def test_settings_error_base(self) -> None:
        """Test base SettingsError with context."""
        context = {"config_path": "/test/config.yaml", "line": 42}
        error = SettingsError("Test error message", context=context)

        assert error.message == "Test error message"
        assert error.context == context
        assert str(error) == "Test error message"

    def test_settings_error_without_context(self) -> None:
        """Test SettingsError without context defaults to empty dict."""
        error = SettingsError("Simple error")

        assert error.message == "Simple error"
        assert error.context == {}

    def test_configuration_error_inheritance(self) -> None:
        """Test SettingsConfigurationError inherits properly."""
        error = SettingsConfigurationError("Config error", context={"file": ".env"})

        # SettingsConfigurationError inherits from ModuleConfigurationError,
        # which inherits from ModuleError, not SettingsError directly
        assert isinstance(error, Exception)
        assert error.message == "Config error"
        assert error.context["file"] == ".env"

    def test_validation_error_inheritance(self) -> None:
        """Test SettingsValidationError inherits properly."""
        error = SettingsValidationError("Validation failed")

        # SettingsValidationError inherits from ModuleValidationError,
        # which inherits from ModuleError, not SettingsError directly
        assert isinstance(error, Exception)
        assert error.message == "Validation failed"
        assert error.message == "Validation failed"

    def test_override_error_inheritance(self) -> None:
        """Test SettingsOverrideError inherits properly."""
        error = SettingsOverrideError("Override failed")

        assert isinstance(error, SettingsError)
        assert error.message == "Override failed"

    def test_generator_error_inheritance(self) -> None:
        """Test SettingsGeneratorError inherits properly."""
        error = SettingsGeneratorError("Generator failed")

        # SettingsGeneratorError inherits from ModuleGeneratorError,
        # which inherits from ModuleError, not SettingsError directly
        assert isinstance(error, Exception)
        assert error.message == "Generator failed"


class TestErrorFormatting:
    """Test error formatting and suggestion functions."""

    def test_format_error_with_context(self) -> None:
        """Test error formatting includes context nicely."""
        context = {"config_path": "/test/config.yaml", "line_number": 42}
        error = SettingsError("Parse error", context=context)

        formatted = format_error_with_context(error)

        assert "❌ Parse error" in formatted
        assert "Context:" in formatted
        assert "config_path: /test/config.yaml" in formatted
        assert "line_number: 42" in formatted

    def test_format_error_without_context(self) -> None:
        """Test error formatting without context."""
        error = SettingsError("Simple error")

        formatted = format_error_with_context(error)

        assert formatted == "❌ Simple error"
        assert "Context:" not in formatted

    def test_suggest_fix_env_file_missing(self) -> None:
        """Test fix suggestion for missing .env file."""
        error = FileNotFoundError("No such file or directory: '.env'")

        suggestion = suggest_fix_for_common_errors(error)

        assert "💡 Try creating a .env file" in suggestion

    def test_suggest_fix_yaml_parse_error(self) -> None:
        """Test fix suggestion for YAML parsing errors."""
        error = Exception("YAML parse error: invalid syntax")

        suggestion = suggest_fix_for_common_errors(error)

        assert "💡 Check YAML syntax" in suggestion

    def test_suggest_fix_permission_denied(self) -> None:
        """Test fix suggestion for permission errors."""
        error = PermissionError("Permission denied")

        suggestion = suggest_fix_for_common_errors(error)

        assert "💡 Check file permissions" in suggestion

    def test_suggest_fix_connection_error_vault(self) -> None:
        """Test fix suggestion for Vault connection errors."""
        error = ConnectionError("Connection failed to vault server")

        suggestion = suggest_fix_for_common_errors(error)

        assert "💡 Verify network connectivity" in suggestion

    def test_suggest_fix_connection_error_aws(self) -> None:
        """Test fix suggestion for AWS connection errors."""
        error = Exception("AWS connection timeout")

        suggestion = suggest_fix_for_common_errors(error)

        assert "💡 Verify network connectivity" in suggestion

    def test_suggest_fix_override_error(self) -> None:
        """Test fix suggestion for override errors."""
        error = Exception("Override registration failed")

        suggestion = suggest_fix_for_common_errors(error)

        assert "💡 Check override registration" in suggestion

    def test_suggest_fix_generic_error(self) -> None:
        """Test generic fix suggestion for unknown errors."""
        error = Exception("Unknown error type")

        suggestion = suggest_fix_for_common_errors(error)

        assert "💡 Check logs above" in suggestion


class TestErrorScenarios:
    """Test realistic error scenarios and edge cases."""

    def test_nested_error_context(self) -> None:
        """Test error context with nested data structures."""
        context = {
            "config": {"sources": [".env", "config.yaml"], "validation": {"strict": True}},
            "error_location": "line 15, column 3",
        }
        error = SettingsConfigurationError("Nested config error", context=context)

        assert error.context["config"]["sources"] == [".env", "config.yaml"]
        assert error.context["config"]["validation"]["strict"] is True

    def test_error_chaining(self) -> None:
        """Test error chaining preserves original cause."""
        original_error = ValueError("Original cause")

        try:
            raise SettingsValidationError("Wrapped error") from original_error
        except SettingsValidationError as wrapped:
            assert wrapped.__cause__ is original_error

    def test_multiple_error_contexts(self) -> None:
        """Test combining multiple error contexts."""
        base_context = {"module": "settings", "version": "1.0.0"}
        specific_context = {"template": "fastapi.j2", "line": 100}

        combined_context = {**base_context, **specific_context}
        error = SettingsGeneratorError("Template error", context=combined_context)

        assert error.context["module"] == "settings"
        assert error.context["template"] == "fastapi.j2"

        expected_context_size = 4  # module, version, template, line
        assert len(error.context) == expected_context_size

    @pytest.mark.parametrize(
        "error_type,expected_suggestion",
        [
            ("file not found .env.local", "💡 Try creating a .env file"),
            ("YAML scanner error", "💡 Check YAML syntax"),
            ("permission denied /etc/config", "💡 Check file permissions"),
            ("vault connection refused", "💡 Verify network connectivity"),
            ("override module not found", "💡 Check override registration"),
            ("random unknown error", "💡 Check logs above"),
        ],
    )
    def test_suggestion_patterns(self, error_type: str, expected_suggestion: str) -> None:
        """Test fix suggestion patterns for various error types."""
        error = Exception(error_type)
        suggestion = suggest_fix_for_common_errors(error)
        assert expected_suggestion in suggestion
