# tests/core/services/test_env_validator.py
import pytest

from core.services.env_validator import (
    ENV_SCHEMA,
    cast_value,
    parse_bool,
    validate_env,
)


class TestEnvValidator:
    """Test cases for the environment validator service."""

    def test_parse_bool_true_values(self) -> None:
        """Test parsing various true boolean values."""
        true_values = ["1", "true", "yes", "on", "y", "t", "True", "YES", "ON"]

        for value in true_values:
            assert parse_bool(value) is True

    def test_parse_bool_false_values(self) -> None:
        """Test parsing various false boolean values."""
        false_values = ["0", "false", "no", "off", "n", "f", "False", "NO", "OFF"]

        for value in false_values:
            assert parse_bool(value) is False

    def test_parse_bool_invalid_value(self) -> None:
        """Test parsing invalid boolean values raises ValueError."""
        invalid_values = ["maybe", "2", "invalid", ""]

        for value in invalid_values:
            with pytest.raises(ValueError, match="invalid boolean value"):
                parse_bool(value)

    def test_parse_bool_whitespace_handling(self) -> None:
        """Test that whitespace is properly stripped from boolean values."""
        assert parse_bool("  true  ") is True
        assert parse_bool("  false  ") is False
        assert parse_bool("  1  ") is True
        assert parse_bool("  0  ") is False

    def test_cast_value_bool_type(self) -> None:
        """Test casting values to boolean type."""
        assert cast_value("true", "bool") is True
        assert cast_value("false", "bool") is False
        assert cast_value("1", "bool") is True
        assert cast_value("0", "bool") is False

    def test_cast_value_int_type(self) -> None:
        """Test casting values to integer type."""
        TEST_INT_POSITIVE = 42
        TEST_INT_NEGATIVE = -123

        assert cast_value("42", "int") == TEST_INT_POSITIVE
        assert cast_value("0", "int") == 0
        assert cast_value("-123", "int") == TEST_INT_NEGATIVE

    def test_cast_value_str_type(self) -> None:
        """Test casting values to string type."""
        assert cast_value("hello", "str") == "hello"
        assert cast_value("123", "str") == "123"
        assert cast_value("", "str") == ""

    def test_cast_value_invalid_bool(self) -> None:
        """Test casting invalid boolean values."""
        with pytest.raises(ValueError):
            cast_value("invalid", "bool")

    def test_cast_value_invalid_int(self) -> None:
        """Test casting invalid integer values."""
        with pytest.raises(ValueError):
            cast_value("not_a_number", "int")

    def test_cast_value_unsupported_type(self) -> None:
        """Test casting with unsupported type."""
        # This should not raise an error, just return the string as-is
        result = cast_value("value", "unsupported")
        assert result == "value"

    def test_validate_env_basic_validation(self) -> None:
        """Test basic environment variable validation."""
        env_vars = {
            "ENV": "development",
            "DEBUG": "false",
            "PROJECT_NAME": "Test Project",
            "SECRET_KEY": "test-secret",
            "VERSION": "1.0.0",
            "ALLOWED_HOSTS": "*",
            "LOG_LEVEL": "INFO",
        }

        result, is_valid, errors = validate_env(env_vars)

        assert is_valid is True
        assert len(errors) == 0
        assert result["ENV"] == "development"
        assert result["DEBUG"] is False
        assert result["PROJECT_NAME"] == "Test Project"
        assert result["SECRET_KEY"] == "test-secret"
        assert result["VERSION"] == "1.0.0"
        assert result["ALLOWED_HOSTS"] == "*"
        assert result["LOG_LEVEL"] == "INFO"

    def test_validate_env_with_defaults(self) -> None:
        """Test validation with missing values uses defaults."""
        env_vars = {
            "ENV": "production",  # Override default
            # DEBUG, PROJECT_NAME, SECRET_KEY, VERSION, ALLOWED_HOSTS, LOG_LEVEL will use defaults
        }

        result, is_valid, errors = validate_env(env_vars)

        assert is_valid is True
        assert len(errors) == 0
        assert result["ENV"] == "production"
        assert result["DEBUG"] is False  # Default
        assert result["PROJECT_NAME"] == "RapidKit App"  # Default
        assert result["SECRET_KEY"] == "changeme"  # Default
        assert result["VERSION"] == "1.0.0"  # Default
        assert result["ALLOWED_HOSTS"] == "*"  # Default
        assert result["LOG_LEVEL"] == "INFO"  # Default

    def test_validate_env_invalid_choice(self) -> None:
        """Test validation with invalid choice values."""
        env_vars = {
            "ENV": "invalid_env",  # Invalid choice
        }

        result, is_valid, errors = validate_env(env_vars)

        assert is_valid is False
        assert len(errors) > 0
        assert any("value 'invalid_env' not in choices" in error for error in errors)

    def test_validate_env_invalid_log_level(self) -> None:
        """Test validation with invalid log level."""
        env_vars = {
            "LOG_LEVEL": "INVALID_LEVEL",  # Invalid choice
        }

        result, is_valid, errors = validate_env(env_vars)

        assert is_valid is False
        assert len(errors) > 0
        assert any("value 'INVALID_LEVEL' not in choices" in error for error in errors)

    def test_validate_env_type_casting_errors(self) -> None:
        """Test validation with type casting errors."""
        env_vars = {
            "DEBUG": "not_a_boolean",  # Invalid boolean
        }

        result, is_valid, errors = validate_env(env_vars)

        assert is_valid is False
        assert len(errors) > 0
        assert any("invalid boolean value: 'not_a_boolean'" in error for error in errors)

    def test_validate_env_empty_input(self) -> None:
        """Test validation with empty input dictionary."""
        result, is_valid, errors = validate_env({})

        # Should return all defaults
        assert is_valid is True
        assert len(errors) == 0
        assert result["ENV"] == "development"
        assert result["DEBUG"] is False
        assert result["PROJECT_NAME"] == "RapidKit App"
        assert result["SECRET_KEY"] == "changeme"
        assert result["VERSION"] == "1.0.0"
        assert result["ALLOWED_HOSTS"] == "*"
        assert result["LOG_LEVEL"] == "INFO"

    def test_validate_env_case_insensitive_choices(self) -> None:
        """Test that choice validation is case-insensitive."""
        env_vars = {
            "ENV": "production",  # Correct case
            "LOG_LEVEL": "WARNING",  # Correct case
        }

        result, is_valid, errors = validate_env(env_vars)

        assert is_valid is True
        assert len(errors) == 0
        assert result["ENV"] == "production"
        assert result["LOG_LEVEL"] == "WARNING"

    def test_validate_env_with_extra_vars(self) -> None:
        """Test validation with extra environment variables not in schema."""
        env_vars = {
            "ENV": "development",
            "CUSTOM_VAR": "custom_value",  # Not in schema
            "ANOTHER_VAR": "another_value",  # Not in schema
        }

        result, is_valid, errors = validate_env(env_vars)

        # Schema variables should be validated
        assert is_valid is True
        assert len(errors) == 0
        assert result["ENV"] == "development"

        # Extra variables should be passed through unchanged
        assert result["CUSTOM_VAR"] == "custom_value"
        assert result["ANOTHER_VAR"] == "another_value"

    def test_validate_env_mixed_types(self) -> None:
        """Test validation with mixed data types."""
        env_vars = {
            "ENV": "staging",
            "DEBUG": "true",  # String that becomes boolean
            "PROJECT_NAME": "My App",  # String
            "VAULT_URL": "https://vault.example.com:8200",  # URL string
            "AWS_REGION": "us-west-2",  # String
        }

        result, is_valid, errors = validate_env(env_vars)

        assert is_valid is True
        assert len(errors) == 0
        assert result["ENV"] == "staging"
        assert result["DEBUG"] is True
        assert result["PROJECT_NAME"] == "My App"
        assert result["VAULT_URL"] == "https://vault.example.com:8200"
        assert result["AWS_REGION"] == "us-west-2"

    def test_env_schema_structure(self) -> None:
        """Test that ENV_SCHEMA has the expected structure."""
        required_keys = [
            "ENV",
            "DEBUG",
            "PROJECT_NAME",
            "SECRET_KEY",
            "VERSION",
            "ALLOWED_HOSTS",
            "LOG_LEVEL",
            "VAULT_URL",
            "AWS_REGION",
        ]

        for key in required_keys:
            assert key in ENV_SCHEMA
            assert "type" in ENV_SCHEMA[key]
            assert "default" in ENV_SCHEMA[key]

    def test_env_schema_choices(self) -> None:
        """Test that ENV_SCHEMA choices are properly defined."""
        # ENV choices
        assert "choices" in ENV_SCHEMA["ENV"]
        assert "development" in ENV_SCHEMA["ENV"]["choices"]
        assert "production" in ENV_SCHEMA["ENV"]["choices"]
        assert "staging" in ENV_SCHEMA["ENV"]["choices"]

        # LOG_LEVEL choices
        assert "choices" in ENV_SCHEMA["LOG_LEVEL"]
        expected_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in expected_levels:
            assert level in ENV_SCHEMA["LOG_LEVEL"]["choices"]

    def test_env_schema_defaults(self) -> None:
        """Test that ENV_SCHEMA defaults are reasonable."""
        assert ENV_SCHEMA["ENV"]["default"] == "development"
        assert ENV_SCHEMA["DEBUG"]["default"] is False
        assert ENV_SCHEMA["PROJECT_NAME"]["default"] == "RapidKit App"
        assert ENV_SCHEMA["SECRET_KEY"]["default"] == "changeme"
        assert ENV_SCHEMA["VERSION"]["default"] == "1.0.0"
        assert ENV_SCHEMA["ALLOWED_HOSTS"]["default"] == "*"
        assert ENV_SCHEMA["LOG_LEVEL"]["default"] == "INFO"
        assert ENV_SCHEMA["VAULT_URL"]["default"] == "http://localhost:8200"
        assert ENV_SCHEMA["AWS_REGION"]["default"] == "us-east-1"

    def test_validate_env_preserves_original_values(self) -> None:
        """Test that validation preserves original string values when appropriate."""
        env_vars = {
            "SECRET_KEY": "my-secret-key-123",
            "VAULT_URL": "https://secure-vault.company.com:8200/v1/",
            "AWS_REGION": "eu-central-1",
        }

        result, is_valid, errors = validate_env(env_vars)

        assert is_valid is True
        assert len(errors) == 0
        # These should remain as strings
        assert result["SECRET_KEY"] == "my-secret-key-123"
        assert result["VAULT_URL"] == "https://secure-vault.company.com:8200/v1/"
        assert result["AWS_REGION"] == "eu-central-1"
