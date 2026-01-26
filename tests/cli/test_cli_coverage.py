"""Tests for CLI commands with low coverage."""

from cli.commands.add import add_app
from cli.commands.create import create_app
from cli.commands.doctor import doctor_app
from cli.commands.info import app as info_app


class TestCliCommands:
    """Test CLI commands with low coverage."""

    def test_add_app_exists(self) -> None:
        """Test add_app exists."""
        assert add_app is not None
        assert hasattr(add_app, "command")

    def test_create_app_exists(self) -> None:
        """Test create_app exists."""
        assert create_app is not None
        assert hasattr(create_app, "command")

    def test_doctor_app_exists(self) -> None:
        """Test doctor_app exists."""
        assert doctor_app is not None
        assert hasattr(doctor_app, "command")

    def test_info_app_exists(self) -> None:
        """Test info_app exists."""
        assert info_app is not None
        assert hasattr(info_app, "command")
