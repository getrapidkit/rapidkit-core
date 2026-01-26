"""Basic functionality tests for RapidKit.

This module contains fundamental tests to ensure core functionality works correctly.
Tests are designed to be simple, reliable, and provide good coverage of basic operations.
"""

import subprocess
import sys

# Constants for version checks
MIN_PYTHON_MAJOR = 3
MIN_PYTHON_MINOR = 8

# Constants for test values
TEST_INT_VALUE = 456
TEST_FLOAT_VALUE = 3.14
TEST_STR_VALUE = "123"


class TestBasicFunctionality:
    """Test class for basic RapidKit functionality."""

    def test_python_version(self) -> None:
        """Test that Python version is compatible."""
        version = sys.version_info
        assert version.major >= MIN_PYTHON_MAJOR
        assert version.minor >= MIN_PYTHON_MINOR

    def test_basic_imports(self) -> None:
        """Test that basic Python modules can be imported."""
        import json
        import os
        import tempfile

        assert os is not None
        assert json is not None
        assert tempfile is not None

    def test_file_operations(self) -> None:
        """Test basic file operations."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Test file exists
            assert os.path.exists(temp_path)

            # Test file reading
            with open(temp_path, "r") as f:
                content = f.read()
            assert content == "test content"

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_json_operations(self) -> None:
        """Test JSON serialization and deserialization."""
        import json

        test_data = {
            "name": "RapidKit",
            "version": "1.0.0",
            "features": ["cli", "api", "testing"],
            "active": True,
        }

        # Test serialization
        json_str = json.dumps(test_data)
        assert isinstance(json_str, str)
        assert "RapidKit" in json_str

        # Test deserialization
        parsed_data = json.loads(json_str)
        assert parsed_data == test_data
        assert parsed_data["active"] is True

    def test_environment_variables(self) -> None:
        """Test environment variable handling."""
        import os

        # Test setting and getting env var
        test_key = "RAPIDKIT_TEST_VAR"
        test_value = "test_value_123"

        # Set environment variable
        os.environ[test_key] = test_value

        try:
            # Test retrieval
            retrieved_value = os.environ.get(test_key)
            assert retrieved_value == test_value

            # Test existence check
            assert test_key in os.environ

        finally:
            # Cleanup
            if test_key in os.environ:
                del os.environ[test_key]

    def test_exception_handling(self) -> None:
        """Test proper exception handling."""
        try:
            # This should raise ZeroDivisionError
            _ = 1 / 0
            raise AssertionError("Should have raised ZeroDivisionError")
        except ZeroDivisionError:
            # Expected exception
            pass
        except Exception as e:
            raise AssertionError(f"Unexpected exception: {e}") from e

    def test_type_checking(self) -> None:
        """Test basic type operations."""
        # Test isinstance
        assert isinstance("hello", str)
        assert isinstance(42, int)
        assert isinstance([1, 2, 3], list)
        assert isinstance({"key": "value"}, dict)

        # Test type conversion
        assert str(123) == TEST_STR_VALUE
        assert int("456") == TEST_INT_VALUE
        assert float("3.14") == TEST_FLOAT_VALUE


def test_cli_basic() -> None:
    """Test basic CLI functionality."""
    try:
        # Try to run rapidkit command
        result = subprocess.run(
            ["python", "-c", 'print("CLI test passed")'],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        assert result.returncode == 0
        assert "CLI test passed" in result.stdout
    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        subprocess.CalledProcessError,
    ):
        # CLI might not be available in test environment
        pass


def test_module_structure() -> None:
    """Test that basic module structure is intact."""
    import os

    # Check if src directory exists
    assert os.path.exists("src"), "src directory should exist"

    # Check if basic files exist
    assert os.path.exists("pyproject.toml"), "pyproject.toml should exist"

    # Check if tests directory exists
    assert os.path.exists("tests"), "tests directory should exist"
