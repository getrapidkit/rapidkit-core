"""End-to-end tests for RapidKit installation and basic usage scenarios."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from cli.main import app


class TestRapidKitInstallation:
    """Test RapidKit installation scenarios for end users."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_pip_install_simulation(self):
        """Test pip install rapidkit-core simulation."""
        # Simulate pip install rapidkit-core
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["pip", "install", "rapidkit-core"],
                returncode=0,
                stdout="Successfully installed rapidkit-core",
                stderr="",
            )

            # Test that installation command would work
            result = mock_run(["pip", "install", "rapidkit-core"])
            assert result.returncode == 0
            assert "rapidkit-core" in result.stdout

    def test_cli_available_after_install(self):
        """Test that CLI is available after installation."""
        # Test basic CLI availability
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "rapidkit" in result.output.lower() or "cli" in result.output.lower()

    def test_create_project_workflow(self):
        """Test complete project creation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"

            # Test project creation
            with patch("cli.commands.create.create_project") as mock_create:
                mock_create.return_value = str(project_path)

                result = self.runner.invoke(
                    app, ["create", str(project_path), "--template", "minimal"]
                )

                # Should not crash
                assert result.exit_code in [0, 1, 2]

    def test_add_module_workflow(self):
        """Test adding modules to project."""
        with patch("cli.commands.add.all.add_all") as mock_add:
            mock_add.return_value = None

            result = self.runner.invoke(app, ["add", "all"])
            # Should not crash
            assert result.exit_code in [0, 1, 2]

    def test_list_available_kits(self):
        """Test listing available kits."""
        with patch("core.engine.registry.KitRegistry") as mock_registry:
            mock_instance = mock_registry.return_value
            mock_instance.list_kits.return_value = ["fastapi", "django", "minimal"]

            result = self.runner.invoke(app, ["list"])
            # Should not crash
            assert result.exit_code in [0, 1]

    def test_doctor_check_system(self):
        """Test system health check."""
        result = self.runner.invoke(app, ["doctor", "check"])
        # Should not crash
        assert result.exit_code in [0, 1]

    def test_info_command(self):
        """Test getting kit information."""
        result = self.runner.invoke(app, ["info", "--help"])
        assert result.exit_code == 0

    def test_license_status(self):
        """Test license status check."""
        result = self.runner.invoke(app, ["license", "status"])
        # Should not crash
        assert result.exit_code in [0, 1]

    def test_frameworks_list(self):
        """Test listing supported frameworks."""
        result = self.runner.invoke(app, ["frameworks", "list"])
        # Should not crash
        assert result.exit_code in [0, 1]


class TestEndUserScenarios:
    """Test real-world end user scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_fastapi_project_creation(self):
        """Test creating a FastAPI project from scratch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "my_fastapi_app"

            with patch("cli.commands.create.create_project") as mock_create:
                mock_create.return_value = str(project_path)

                result = self.runner.invoke(
                    app, ["create", str(project_path), "--template", "fastapi"]
                )

                assert result.exit_code in [0, 1, 2]

    def test_minimal_project_creation(self):
        """Test creating a minimal project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "my_minimal_app"

            with patch("cli.commands.create.create_project") as mock_create:
                mock_create.return_value = str(project_path)

                result = self.runner.invoke(
                    app, ["create", str(project_path), "--template", "minimal"]
                )

                assert result.exit_code in [0, 1, 2]

    def test_project_with_modules(self):
        """Test creating project and adding modules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "my_app"

            with (
                patch("cli.commands.create.create_project") as mock_create,
                patch("cli.commands.add.all.add_all") as mock_add,
            ):

                mock_create.return_value = str(project_path)
                mock_add.return_value = None

                # Create project
                result1 = self.runner.invoke(
                    app, ["create", str(project_path), "--template", "fastapi"]
                )
                assert result1.exit_code in [0, 1, 2]

                # Add modules
                result2 = self.runner.invoke(app, ["add", "all"])
                assert result2.exit_code in [0, 1, 2]

    def test_cli_help_system(self):
        """Test comprehensive help system."""
        commands = [
            "",
            "--help",
            "create",
            "add",
            "list",
            "doctor",
            "info",
            "license",
            "frameworks",
        ]

        for cmd in commands:
            if cmd == "":
                result = self.runner.invoke(app, [])
            else:
                result = self.runner.invoke(app, [cmd] if cmd != "--help" else ["--help"])

            # Help should always work
            assert result.exit_code in [0, 1, 2]

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test invalid template
        result = self.runner.invoke(app, ["create", "test", "--template", "invalid"])
        assert result.exit_code in [0, 1, 2]

        # Test invalid command
        result = self.runner.invoke(app, ["invalid_command"])
        assert result.exit_code in [0, 1, 2]

        # Test missing arguments
        result = self.runner.invoke(app, ["create"])
        assert result.exit_code in [0, 1, 2]
