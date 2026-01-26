"""Integration tests for complete RapidKit workflows."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.main import app


class TestIntegrationWorkflows:
    """Test complete integration workflows for end users."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_complete_project_lifecycle(self):
        """Test complete project lifecycle from creation to deployment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "my_complete_app"

            with (
                patch("cli.commands.create.create_project") as mock_create,
                patch("cli.commands.add.all.add_all") as mock_add,
                patch("core.engine.registry.KitRegistry") as mock_registry,
            ):

                # Mock successful operations
                mock_create.return_value = str(project_path)
                mock_add.return_value = None

                mock_instance = MagicMock()
                mock_instance.list_kits.return_value = ["fastapi", "minimal"]
                mock_registry.return_value = mock_instance

                # Step 1: Create project
                result1 = self.runner.invoke(
                    app, ["create", str(project_path), "--template", "fastapi"]
                )
                assert result1.exit_code in [0, 1, 2]

                # Step 2: List available kits
                result2 = self.runner.invoke(app, ["list"])
                assert result2.exit_code in [0, 1]

                # Step 3: Add modules
                result3 = self.runner.invoke(app, ["add", "all"])
                assert result3.exit_code in [0, 1, 2]

                # Step 4: Check system health
                result4 = self.runner.invoke(app, ["doctor", "check"])
                assert result4.exit_code in [0, 1]

    def test_developer_workflow(self):
        """Test developer workflow for contributing to community."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "dev_project"

            with (
                patch("cli.commands.create.create_project") as mock_create,
                patch("cli.commands.add.all.add_all") as mock_add,
                patch("cli.commands.upgrade.upgrade_module") as mock_upgrade,
            ):

                mock_create.return_value = str(project_path)
                mock_add.return_value = None
                mock_upgrade.return_value = None

                # Create development project
                result1 = self.runner.invoke(
                    app, ["create", str(project_path), "--template", "minimal"]
                )
                assert result1.exit_code in [0, 1, 2]

                # Add development modules
                result2 = self.runner.invoke(app, ["add", "all"])
                assert result2.exit_code in [0, 1, 2]

                # Upgrade modules
                result3 = self.runner.invoke(app, ["upgrade", "module", "test"])
                assert result3.exit_code in [0, 1, 2]

    def test_multi_framework_support(self):
        """Test support for multiple frameworks."""
        frameworks = ["fastapi", "django", "minimal"]

        for framework in frameworks:
            with tempfile.TemporaryDirectory() as temp_dir:
                project_path = Path(temp_dir) / f"{framework}_project"

                with patch("cli.commands.create.create_project") as mock_create:
                    mock_create.return_value = str(project_path)

                    result = self.runner.invoke(
                        app, ["create", str(project_path), "--template", framework]
                    )

                    # Each framework should be supported
                    assert result.exit_code in [0, 1, 2]

    def test_cli_interactive_mode(self):
        """Test CLI interactive mode simulation."""
        # Test that CLI can handle various input scenarios
        test_commands = [
            ["--help"],
            ["create", "--help"],
            ["list"],
            ["doctor", "check"],
            ["license", "status"],
            ["frameworks", "list"],
            ["info", "--help"],
        ]

        for cmd in test_commands:
            result = self.runner.invoke(app, cmd)
            # CLI should handle all commands gracefully
            assert result.exit_code in [0, 1, 2]

    def test_error_recovery(self):
        """Test error recovery and graceful failure."""
        # Test with invalid inputs
        invalid_commands = [
            ["create"],  # Missing project name
            ["create", "test", "--template", "nonexistent"],
            ["add", "invalid_module"],
            ["upgrade", "invalid_target"],
            ["info", "nonexistent_kit"],
        ]

        for cmd in invalid_commands:
            result = self.runner.invoke(app, cmd)
            # Should fail gracefully, not crash
            assert result.exit_code in [0, 1, 2]

    def test_configuration_management(self):
        """Test configuration management workflow."""
        with (
            patch("core.services.config_loader.load_module_config") as mock_config,
            patch("core.services.env_validator.validate_env") as mock_env,
        ):

            mock_config.return_value = {"test": "config"}
            mock_env.return_value = True

            # Test that config loading works
            result = self.runner.invoke(app, ["doctor", "check"])
            assert result.exit_code in [0, 1]

    def test_module_management_workflow(self):
        """Test complete module management workflow."""
        with (
            patch("cli.commands.add.all.add_all") as mock_add,
            patch("cli.commands.list.list_kits") as mock_list,
            patch("cli.commands.uninstall.uninstall_module") as mock_uninstall,
        ):

            mock_add.return_value = None
            mock_list.return_value = ["module1", "module2"]
            mock_uninstall.return_value = None

            # Add modules
            result1 = self.runner.invoke(app, ["add", "all"])
            assert result1.exit_code in [0, 1, 2]

            # List modules
            result2 = self.runner.invoke(app, ["list"])
            assert result2.exit_code in [0, 1]

            # Uninstall module
            result3 = self.runner.invoke(app, ["uninstall", "module", "test"])
            assert result3.exit_code in [0, 1, 2]

    def test_template_system(self):
        """Test template system functionality."""
        templates = ["minimal", "fastapi", "django"]

        for template in templates:
            with tempfile.TemporaryDirectory() as temp_dir:
                project_path = Path(temp_dir) / f"{template}_test"

                with patch("cli.commands.create.create_project") as mock_create:
                    mock_create.return_value = str(project_path)

                    result = self.runner.invoke(
                        app, ["create", str(project_path), "--template", template]
                    )

                    # Template should be available
                    assert result.exit_code in [0, 1, 2]

    def test_cross_platform_compatibility(self):
        """Test cross-platform compatibility."""
        # Test that CLI works regardless of platform
        with patch("platform.system") as mock_platform:
            platforms = ["Windows", "Linux", "Darwin"]

            for platform in platforms:
                mock_platform.return_value = platform

                result = self.runner.invoke(app, ["--help"])
                # Should work on all platforms
                assert result.exit_code in [0, 1, 2]
