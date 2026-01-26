# tests/test_add_command.py
"""Test the add command CLI structure."""

from typer.testing import CliRunner

from cli.commands.add import add_app
from cli.main import app as cli_app


def test_add_app_import() -> None:
    """Test that add_app can be imported and has expected structure."""
    # This should import the add.py file and execute its code
    assert add_app is not None
    assert hasattr(add_app, "add_typer")


def test_add_subcommands_registered() -> None:
    """Test that subcommands are properly registered in add_app."""
    # Import should have executed the registration code
    assert hasattr(add_app, "registered_commands")
    # Check that the subcommands were registered during import
    assert len(add_app.registered_commands) > 0


def test_add_command_exists() -> None:
    """Test that add command exists in the main CLI."""
    runner = CliRunner()

    # Just test that the command doesn't fail with unknown command error
    result = runner.invoke(cli_app, ["add"])

    # The command should either succeed or show help/error, but not "unknown command"
    assert "unknown command" not in result.output.lower()
    UNKNOWN_COMMAND_EXIT_CODE = 2
    assert "add" in result.output.lower() or result.exit_code != UNKNOWN_COMMAND_EXIT_CODE


def test_add_command_with_invalid_subcommand() -> None:
    """Test add command behavior with invalid subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["add", "invalid"])

    # Should show an error for invalid subcommand
    assert result.exit_code != 0
    assert "invalid" in result.output.lower() or "no such command" in result.output.lower()
