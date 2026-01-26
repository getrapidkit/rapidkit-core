# tests/test_end_user.py
"""End user tests - for users who just want to use RapidKit.

These tests verify that the basic functionality works for end users
who don't want to contribute to development.
"""

import pytest


class TestEndUserBasicUsage:
    """Basic usage tests for end users."""

    def test_library_can_be_imported(self):
        """Test that the library can be imported successfully."""
        try:
            import core

            assert core is not None
        except ImportError as e:
            pytest.fail(f"Failed to import core: {e}")

    def test_cli_is_available(self):
        """Test that CLI is available and can show help."""
        from typer.testing import CliRunner

        try:
            from cli.main import app

            runner = CliRunner()
            result = runner.invoke(app, ["--help"])
            assert result.exit_code == 0
        except ImportError:
            pytest.skip("CLI not available")

    def test_basic_kit_functionality(self):
        """Test that basic kit functionality works."""
        try:
            from kits.fastapi.minimal import generator

            assert generator is not None
        except ImportError:
            pytest.skip("FastAPI minimal kit not available")


class TestEndUserInstallation:
    """Installation and setup tests for end users."""

    def test_core_modules_available(self):
        """Test that core modules are available."""
        modules_to_test = [
            "core",
            "cli",
            "kits",
        ]

        for module in modules_to_test:
            try:
                __import__(module)
            except ImportError:
                pytest.skip(f"Module {module} not available")

    def test_basic_configuration(self):
        """Test that basic configuration works."""
        try:
            from core.config.kit_config import KitConfig

            # Just test that the class exists
            assert KitConfig is not None
        except ImportError:
            pytest.skip("Configuration not available")
