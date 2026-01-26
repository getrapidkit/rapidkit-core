"""Additional test coverage for settings module components."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from modules.free.essentials.settings.generate import (
    GeneratorError,
    _infer_vendor_relative,
    build_base_context,
    load_module_config,
)
from modules.shared.exceptions import (
    SettingsConfigurationError,
    SettingsError,
    SettingsOverrideError,
    SettingsValidationError,
    format_error_with_context,
    suggest_fix_for_common_errors,
)
from modules.shared.generator import TemplateRenderer

GENERATOR_ERROR_EXIT_CODE = 2
DEFAULT_GENERATOR_EXIT_CODE = 1
MIN_BASE_CONTEXT_FIELDS = 3


class TestExceptionsCoverage:
    """Test exception classes and error handling utilities."""

    def test_settings_error_basic(self):
        """Test basic SettingsError functionality."""
        error = SettingsError("Test message")
        assert error.message == "Test message"
        assert error.context == {}

    def test_settings_error_with_context(self):
        """Test SettingsError with context."""
        context = {"file": "config.yaml", "line": 42}
        error = SettingsError("Parse error", context=context)
        assert error.context == context

    def test_configuration_error(self):
        """Test SettingsConfigurationError."""
        error = SettingsConfigurationError("Config error")
        # SettingsConfigurationError inherits from ModuleConfigurationError, not SettingsError directly
        assert isinstance(error, Exception)
        assert error.message == "Config error"

    def test_validation_error(self):
        """Test SettingsValidationError."""
        error = SettingsValidationError("Validation failed")
        # SettingsValidationError inherits from ModuleValidationError, not SettingsError directly
        assert isinstance(error, Exception)
        assert error.message == "Validation failed"

    def test_override_error(self):
        """Test SettingsOverrideError."""
        error = SettingsOverrideError("Override failed")
        assert isinstance(error, SettingsError)

    def test_format_error_with_context(self):
        """Test error formatting."""
        error = SettingsError("Test error", context={"key": "value"})
        formatted = format_error_with_context(error)
        assert "❌ Test error" in formatted
        assert "key: value" in formatted

    def test_format_error_without_context(self):
        """Test error formatting without context."""
        error = SettingsError("Simple error")
        formatted = format_error_with_context(error)
        assert formatted == "❌ Simple error"

    def test_suggest_fix_env_file(self):
        """Test fix suggestion for env file errors."""
        error = FileNotFoundError("No such file: .env")
        suggestion = suggest_fix_for_common_errors(error)
        assert "💡 Try creating a .env file" in suggestion

    def test_suggest_fix_yaml_error(self):
        """Test fix suggestion for YAML errors."""
        error = Exception("YAML parse error")
        suggestion = suggest_fix_for_common_errors(error)
        assert "💡 Check YAML syntax" in suggestion

    def test_suggest_fix_permission_error(self):
        """Test fix suggestion for permission errors."""
        error = PermissionError("Permission denied")
        suggestion = suggest_fix_for_common_errors(error)
        assert "💡 Check file permissions" in suggestion

    def test_suggest_fix_generic_error(self):
        """Test generic fix suggestion."""
        error = Exception("Unknown error")
        suggestion = suggest_fix_for_common_errors(error)
        assert "💡 Check logs above" in suggestion


class TestGeneratorCoverage:
    """Test generator components for better coverage."""

    def test_generator_error_creation(self):
        """Test GeneratorError creation."""
        error = GeneratorError("Test error", exit_code=GENERATOR_ERROR_EXIT_CODE)
        assert error.message == "Test error"
        assert error.exit_code == GENERATOR_ERROR_EXIT_CODE
        assert error.context["exit_code"] == GENERATOR_ERROR_EXIT_CODE

    def test_generator_error_with_context(self):
        """Test GeneratorError with additional context."""
        context = {"template": "test.j2"}
        error = GeneratorError("Template error", context=context)
        assert error.context["template"] == "test.j2"
        assert error.context["exit_code"] == DEFAULT_GENERATOR_EXIT_CODE

    def test_template_renderer_initialization(self):
        """Test TemplateRenderer initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = Path(temp_dir)
            renderer = TemplateRenderer(template_root)
            # Should initialize without error
            assert renderer is not None
            assert renderer.template_root == template_root.resolve()

    def test_template_renderer_fallback(self):
        """Test template renderer fallback mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = Path(temp_dir)
            import modules.shared.generator as generator_mod

            with patch.object(generator_mod, "JinjaEnvironment", None):
                renderer = TemplateRenderer(template_root)
                assert renderer.jinja_env is None

    def test__infer_vendor_relative_default(self):
        """Test inferring vendor settings path with default."""
        config = {}
        path = _infer_vendor_relative(config)
        assert path == "src/modules/free/essentials/settings/settings.py"

    def test__infer_vendor_relative_configured(self):
        """Test inferring vendor settings path from config."""
        config = {
            "generation": {
                "vendor": {
                    "files": [{"template": "settings.py.j2", "relative": "custom/settings.py"}]
                }
            }
        }
        path = _infer_vendor_relative(config)
        assert path == "custom/settings.py"

    def test_build_base_context_defaults(self):
        """Test building base context with defaults."""
        config = {}
        context = build_base_context(config)

        assert context["rapidkit_vendor_module"] == "settings"
        assert context["rapidkit_vendor_version"] == "0.0.0"
        assert "rapidkit_vendor_relative_path" in context

    def test_build_base_context_configured(self):
        """Test building base context with configured values."""
        config = {"name": "custom_settings", "version": "2.1.0"}
        context = build_base_context(config)

        assert context["rapidkit_vendor_module"] == "custom_settings"
        assert context["rapidkit_vendor_version"] == "2.1.0"


class TestOverridesCoverage:
    """Test override functions coverage."""

    def test_override_imports_available(self):
        """Test that override functions can be imported."""
        from modules.free.essentials.settings.overrides import (
            _append_extra_dotenv_sources,
            _refresh_with_observability,
            _relaxed_production_validation,
        )

        # Functions should be available
        assert callable(_append_extra_dotenv_sources)
        assert callable(_relaxed_production_validation)
        assert callable(_refresh_with_observability)

    def test_split_env_list_function(self):
        """Test internal _split_env_list function."""
        from modules.free.essentials.settings.overrides import _split_env_list

        # Test empty input
        assert _split_env_list(None) == ()
        assert _split_env_list("") == ()

        # Test single value
        assert _split_env_list("single") == ("single",)

        # Test multiple values
        assert _split_env_list("one,two,three") == ("one", "two", "three")

        # Test with spaces
        assert _split_env_list("one, two , three") == ("one", "two", "three")

    def test_coerce_iterable_function(self):
        """Test internal _coerce_iterable function."""
        from modules.free.essentials.settings.overrides import _coerce_iterable

        # Test tuple input
        assert _coerce_iterable((1, 2, 3)) == (1, 2, 3)

        # Test list input
        assert _coerce_iterable([1, 2, 3]) == (1, 2, 3)

        # Test other iterable
        assert _coerce_iterable({"a", "b"}) == ("a", "b") or _coerce_iterable({"a", "b"}) == (
            "b",
            "a",
        )


class TestErrorScenarios:
    """Test error scenarios for better coverage."""

    def test_load_config_file_missing(self):
        """Test load_module_config with missing file."""
        import sys

        settings_generate = sys.modules.get("modules.free.essentials.settings.generate")
        assert settings_generate is not None

        with (
            patch.object(settings_generate, "MODULE_ROOT", Path("/nonexistent")),
            pytest.raises(FileNotFoundError),
        ):
            load_module_config()

    def test_template_renderer_missing_template(self):
        """Test template rendering with missing template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = Path(temp_dir)
            renderer = TemplateRenderer(template_root)

            # Create a non-existent template path
            fake_path = Path("/nonexistent/template.j2")

            # Should raise an error when trying to render
            with pytest.raises((FileNotFoundError, Exception)):
                renderer.render(fake_path, {})

    def test_template_renderer_fallback_mode(self):
        """Test template renderer in fallback mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = Path(temp_dir)
            import modules.shared.generator as generator_mod

            with patch.object(generator_mod, "JinjaEnvironment", None):
                renderer = TemplateRenderer(template_root)

            # Create a temporary template file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
                f.write("Hello {{ name }}!")
                template_path = Path(f.name)

            try:
                result = renderer.render(template_path, {"name": "World"})
                assert result == "Hello World!"
            finally:
                template_path.unlink()

    def test_main_function_error_handling(self):
        """Test main function error scenarios."""
        from modules.free.essentials.settings.generate import main

        # Test with insufficient arguments
        with patch("sys.argv", ["generate.py"]):
            with pytest.raises(GeneratorError) as exc_info:
                main()
            assert exc_info.value.exit_code == GENERATOR_ERROR_EXIT_CODE

    def test_write_file_function(self):
        """Test write_file function."""
        from modules.shared.generator import write_file

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "subdir" / "test.txt"
            content = "Test content"

            # Should create directories and file
            write_file(test_file, content)

            assert test_file.exists()
            assert test_file.read_text() == content


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_configurations(self):
        """Test handling of empty configurations."""
        # Empty config should not break context building
        context = build_base_context({})
        assert isinstance(context, dict)
        assert len(context) >= MIN_BASE_CONTEXT_FIELDS

    def test_malformed_environment_variables(self):
        """Test handling of malformed environment variables."""
        from modules.free.essentials.settings.overrides import _split_env_list

        # Test various malformed inputs
        assert _split_env_list(",,") == ()
        assert _split_env_list(",a,") == ("a",)
        assert _split_env_list("  ,  ,  ") == ()

    def test_context_preservation(self):
        """Test that error context is preserved."""
        original_context = {"file": "test.yaml", "line": 42}
        error = SettingsError("Test", context=original_context)

        # Context should be preserved
        assert error.context is original_context
        assert error.context["file"] == "test.yaml"

    def test_error_chaining(self):
        """Test error chaining works correctly."""
        original = ValueError("Original error")

        try:
            raise SettingsConfigurationError("Wrapped error") from original
        except SettingsConfigurationError as wrapped:
            assert wrapped.__cause__ is original
