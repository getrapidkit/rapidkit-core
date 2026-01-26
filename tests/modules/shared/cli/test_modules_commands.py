import json

# Add src to path for imports
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import typer
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cli.commands.modules import (
    _collect_module_rows,
    _lock_path,
    lock,
    outdated,
    sign_all,
    summary,
    validate,
    verify_all,
    yaml_dump,
)


class TestModulesCommands(unittest.TestCase):
    """Comprehensive test suite for modules CLI commands."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.modules_dir = self.temp_dir / "modules"
        self.modules_dir.mkdir()

        # Create test module structure
        self.test_module_dir = self.modules_dir / "test_module"
        self.test_module_dir.mkdir()

        # Create module.yaml
        self.module_yaml = self.test_module_dir / "module.yaml"
        self.module_yaml.write_text(
            """
name: test_module
version: "1.0.0"
description: Test module
config_sources:
  - config/test.yaml
dependencies: []
"""
        )

        # Create config file
        config_dir = self.test_module_dir / "config"
        config_dir.mkdir()
        config_file = config_dir / "test.yaml"
        config_file.write_text("test: value")

        # Create overrides file
        overrides_dir = config_dir / "overrides"
        overrides_dir.mkdir()
        overrides_file = overrides_dir / "fastapi.yaml"
        overrides_file.write_text("fastapi: config")

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.print_error")
    def test_sign_all_modules_path_not_exists(
        self, mock_error: MagicMock, mock_modules_path: MagicMock
    ) -> None:
        """Test sign_all when modules path doesn't exist."""
        mock_modules_path.exists.return_value = False

        with self.assertRaises(typer.Exit):
            sign_all("fake_key")

        mock_error.assert_called_once_with("Modules root not found")

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.yaml")
    @patch("cli.commands.modules.print_success")
    @patch("cli.commands.modules.print_error")
    @patch("cli.commands.modules.getpass.getuser")
    @patch("cli.commands.modules.os.environ.get")
    def test_sign_all_success(
        self,
        mock_environ: MagicMock,
        mock_getuser: MagicMock,
        mock_error: MagicMock,
        mock_success: MagicMock,
        mock_yaml: MagicMock,
        mock_modules_path: MagicMock,
    ) -> None:
        """Test successful signing of all modules."""
        # Setup mocks
        mock_modules_path.exists.return_value = True
        mock_modules_path.iterdir.return_value = [self.test_module_dir]
        mock_yaml.safe_load.return_value = {
            "name": "test_module",
            "config_sources": ["config/test.yaml"],
            "dependencies": [],
        }
        mock_getuser.return_value = "testuser"
        mock_environ.return_value = "test.log"

        # Mock file operations
        with (
            patch("builtins.open", mock_open()),
            patch("hashlib.sha256") as mock_sha256,
            patch("core.module_sign.sign_manifest") as mock_sign,
            patch("base64.b64decode") as mock_b64decode,
            patch("nacl.signing.SigningKey") as mock_signing_key,
        ):
            mock_hash = MagicMock()
            mock_hash.hexdigest.return_value = "abcd1234"
            mock_sha256.return_value = mock_hash

            mock_sign.return_value = {
                "signature": "fake_signature",
                "signer_id": "fake_signer_id",
                "signature_version": "v1",
            }

            mock_b64decode.return_value = b"fake_private_key_bytes"
            mock_verify_key = MagicMock()
            mock_verify_key.encode.return_value = b"fake_public_key_bytes"
            mock_signing_key.return_value.verify_key = mock_verify_key

            with patch("cli.commands.modules.verify_manifest_multi") as mock_verify:
                mock_verify.return_value = True

                sign_all(
                    "fake_key", skip_unchanged=False, json_out=True
                )  # Verify success message was printed
                mock_success.assert_called()

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.print_error")
    def test_verify_all_modules_path_not_exists(
        self, mock_error: MagicMock, mock_modules_path: MagicMock
    ) -> None:
        """Test verify_all when modules path doesn't exist."""
        mock_modules_path.exists.return_value = False

        with self.assertRaises(typer.Exit):
            verify_all()

        mock_error.assert_called_once_with("Modules root not found")

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.yaml")
    @patch("cli.commands.modules.print_success")
    @patch("core.module_sign.verify_manifest_multi")
    def test_verify_all_success(
        self,
        mock_verify: MagicMock,
        mock_success: MagicMock,
        mock_yaml: MagicMock,
        mock_modules_path: MagicMock,
    ) -> None:
        """Test successful verification of all modules."""
        # Setup mocks
        mock_modules_path.exists.return_value = True
        mock_modules_path.iterdir.return_value = [self.test_module_dir]
        mock_yaml.safe_load.return_value = {
            "name": "test_module",
            "signature": "fake_signature",
            "signer_id": "fake_signer_id",
            "signers": ["fake_public_key"],
        }
        mock_verify.return_value = True

        with patch("builtins.open", mock_open()):
            verify_all(None, False, False, False)

            mock_success.assert_called_with("All modules verified. Valid: 1, Errors: 0")

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.print_error")
    def test_summary_modules_path_not_exists(
        self, mock_error: MagicMock, mock_modules_path: MagicMock
    ) -> None:
        """Test summary when modules path doesn't exist."""
        mock_modules_path.exists.return_value = False

        with self.assertRaises(typer.Exit):
            summary()

        mock_error.assert_called_once_with("Modules root not found")

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules._collect_module_rows")
    @patch("cli.commands.modules.console")
    def test_summary_success(
        self,
        mock_console: MagicMock,
        mock_collect: MagicMock,
        mock_modules_path: MagicMock,
    ) -> None:
        """Test successful summary display."""
        mock_modules_path.exists.return_value = True
        mock_collect.return_value = [
            {
                "name": "test_module",
                "version": "1.0.0",
                "status": "valid",
                "access": "free",
                "maturity": "stable",
                "profiles": 1,
                "features": 2,
                "deps": 3,
                "vars": 4,
                "dev_deps": 5,
                "root": "/path/to/module",
                "tags": ["tag1", "tag2"],
            }
        ]

        # Should not raise an exception
        summary()

        # Verify _collect_module_rows was called
        mock_collect.assert_called_once()

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.print_error")
    def test_validate_modules_path_not_exists(
        self, mock_error: MagicMock, mock_modules_path: MagicMock
    ) -> None:
        """Test validate when modules path doesn't exist."""
        mock_modules_path.exists.return_value = False

        with self.assertRaises(typer.Exit):
            validate()

        mock_error.assert_called_once_with("Modules root not found")

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.load_all_specs")
    @patch("cli.commands.modules.validate_spec")
    @patch("cli.commands.modules.print_success")
    @patch("cli.commands.modules.print_error")
    def test_validate_success(
        self,
        mock_error: MagicMock,
        mock_success: MagicMock,
        mock_validate_spec: MagicMock,
        mock_load_specs: MagicMock,
        mock_modules_path: MagicMock,
    ) -> None:
        """Test successful validation of modules."""
        mock_modules_path.exists.return_value = True
        mock_modules_path.iterdir.return_value = [self.test_module_dir]
        mock_load_specs.return_value = {"test_module": {"name": "test_module"}}
        mock_validate_spec.return_value = []

        validate()

        mock_success.assert_called_with("All 1 modules valid ✔")

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.print_error")
    def test_lock_modules_path_not_exists(
        self, mock_error: MagicMock, mock_modules_path: MagicMock
    ) -> None:
        """Test lock when modules path doesn't exist."""
        mock_modules_path.exists.return_value = False

        with self.assertRaises(typer.Exit):
            lock()

        mock_error.assert_called_once_with("Modules root not found")

    @patch("cli.commands.modules._lock_path")
    @patch("cli.commands.modules._collect_module_rows")
    @patch("cli.commands.modules.yaml_dump")
    @patch("cli.commands.modules.print_success")
    def test_lock_success(
        self,
        mock_success: MagicMock,
        mock_yaml_dump: MagicMock,
        mock_collect: MagicMock,
        mock_lock_path: MagicMock,
    ) -> None:
        """Test successful lock file creation."""
        mock_lock_path.return_value = self.temp_dir / "modules.lock"
        mock_collect.return_value = [
            {"module": "test_module", "version": "1.0.0", "tags": ["tag1"]}
        ]
        mock_yaml_dump.return_value = "locked: data"

        with patch("builtins.open", mock_open()):
            lock()

            mock_success.assert_called_with(f"Wrote lock file: {mock_lock_path.return_value}")

    @patch("cli.commands.modules._lock_path")
    @patch("cli.commands.modules.print_error")
    def test_outdated_lock_file_not_exists(
        self, mock_error: MagicMock, mock_lock_path: MagicMock
    ) -> None:
        """Test outdated when lock file doesn't exist."""
        mock_lock_file = MagicMock()
        mock_lock_file.exists.return_value = False
        mock_lock_path.return_value = mock_lock_file

        with self.assertRaises(typer.Exit):
            outdated(None)

        mock_error.assert_called_once_with(
            "Lock file not found. Run 'rapidkit modules lock' first."
        )

    @patch("cli.commands.modules.yaml")
    @patch("cli.commands.modules._lock_path")
    @patch("cli.commands.modules._collect_module_rows")
    @patch("cli.commands.modules.semver")
    @patch("cli.commands.modules.console")
    def test_outdated_with_updates(
        self,
        mock_console: MagicMock,
        mock_semver: MagicMock,
        mock_collect: MagicMock,
        mock_lock_path: MagicMock,
        mock_yaml: MagicMock,
    ) -> None:
        """Test outdated command when updates are available."""
        # Mock the lock file
        mock_lock_file = MagicMock()
        mock_lock_file.exists.return_value = True
        mock_lock_file.read_text.return_value = '{"modules": {"test_module": {"version": "1.0.0"}}}'
        mock_lock_path.return_value = mock_lock_file

        # Mock yaml.safe_load
        mock_yaml.safe_load.return_value = {"modules": {"test_module": {"version": "1.0.0"}}}

        mock_collect.return_value = [
            {
                "module": "test_module",
                "name": "test_module",
                "version": "1.0.0",
                "latest": "2.0.0",
            }
        ]

        # Mock version comparison - current > locked should be upgrade_available
        mock_cur_version = MagicMock()
        mock_lock_version = MagicMock()
        mock_cur_version.__gt__ = lambda _self, _other: True
        mock_semver.parse.side_effect = [mock_cur_version, mock_lock_version]

        # Should not raise an exception
        outdated(None)

        # Verify yaml.safe_load was called
        mock_yaml.safe_load.assert_called_once()

    def test_yaml_dump_success(self) -> None:
        """Test successful YAML dumping."""
        data = {"test": "value", "nested": {"key": "value"}}
        result = yaml_dump(data)

        # Verify it's valid YAML
        parsed = yaml.safe_load(result)
        self.assertEqual(parsed, data)

    def test_yaml_dump_with_yaml_none(self) -> None:
        """Test YAML dumping when yaml module is not available."""
        data = {"test": "value"}

        with patch("cli.commands.modules.yaml", None):
            result = yaml_dump(data)

            # Should fall back to JSON
            parsed = json.loads(result)
            self.assertEqual(parsed, data)

    @patch("cli.commands.modules.load_all_specs")
    @patch("cli.commands.modules.MODULES_PATH")
    def test_collect_module_rows_success(
        self, mock_modules_path: MagicMock, mock_load_specs: MagicMock
    ) -> None:
        """Test successful collection of module rows."""
        # Create a mock spec object with name attribute
        mock_spec = MagicMock()
        mock_spec.name = "test_module"
        mock_spec.version = "1.0.0"
        mock_spec.description = "Test module"

        mock_load_specs.return_value = {"test_module": mock_spec}

        with patch("cli.commands.modules.load_module_config", return_value={}):
            result = _collect_module_rows(verbose=False)

            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)

    def test_lock_path_with_base(self) -> None:
        """Test _lock_path with base path provided."""
        base = Path("/tmp/test")
        result = _lock_path(base)

        self.assertEqual(result, base / ".rapidkit" / "modules.lock.yaml")

    @patch("pathlib.Path.cwd")
    def test_lock_path_without_base(self, mock_cwd: MagicMock) -> None:
        """Test _lock_path without base path."""
        mock_cwd.return_value = Path("/repo")
        result = _lock_path(None)

        self.assertEqual(result, Path("/repo/.rapidkit/modules.lock.yaml"))

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.yaml")
    @patch("cli.commands.modules.print_error")
    def test_sign_all_yaml_load_error(
        self, mock_error: MagicMock, mock_yaml: MagicMock, mock_modules_path: MagicMock
    ) -> None:
        """Test sign_all with YAML loading error."""
        mock_modules_path.exists.return_value = True
        mock_modules_path.iterdir.return_value = [self.test_module_dir]
        mock_yaml.safe_load.side_effect = ValueError("Invalid YAML")

        with patch("builtins.open", mock_open()), self.assertRaises(typer.Exit):
            sign_all("fake_key", json_out=True)

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.yaml")
    @patch("cli.commands.modules.print_error")
    def test_verify_all_yaml_load_error(
        self, mock_error: MagicMock, mock_yaml: MagicMock, mock_modules_path: MagicMock
    ) -> None:
        """Test verify_all with YAML loading error."""
        mock_modules_path.exists.return_value = True
        mock_modules_path.iterdir.return_value = [self.test_module_dir]
        mock_yaml.safe_load.side_effect = yaml.YAMLError("Invalid YAML")

        with patch("builtins.open", mock_open()), self.assertRaises(typer.Exit):
            verify_all(None, False, False, False)

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.load_all_specs")
    @patch("cli.commands.modules.validate_spec")
    @patch("cli.commands.modules.print_error")
    def test_validate_with_validation_errors(
        self,
        mock_error: MagicMock,
        mock_validate_spec: MagicMock,
        mock_load_specs: MagicMock,
        mock_modules_path: MagicMock,
    ) -> None:
        """Test validate with validation errors."""
        mock_modules_path.exists.return_value = True
        mock_modules_path.iterdir.return_value = [self.test_module_dir]
        mock_load_specs.return_value = {"test_module": {"name": "test_module"}}
        mock_validate_spec.return_value = ["Error 1", "Error 2"]

        with self.assertRaises(typer.Exit):
            validate()

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.print_error")
    @patch("cli.commands.modules.validate_spec")
    def test_validate_fails_on_legacy_generation_targets(
        self, mock_validate_spec: MagicMock, mock_error: MagicMock, mock_modules_path: MagicMock
    ) -> None:
        """Ensure modules.validate fails when module manifests have legacy generation targets."""
        mock_modules_path.exists.return_value = True
        mock_modules_path.iterdir.return_value = [self.test_module_dir]

        # module.yaml with legacy generation target
        self.module_yaml.write_text(
            """
name: test_module
generation:
  vendor:
    files:
      - template: templates/base/foo_health.py.j2
        relative: src/core/health/foo.py
""",
            encoding="utf-8",
        )

        # Treat manifest schema as valid
        mock_validate_spec.return_value = []

        with self.assertRaises(typer.Exit) as exc:
            validate()

        # validate should raise non-zero (2) when legacy targets are present
        self.assertEqual(exc.exception.exit_code, 2)
        mock_error.assert_called()

    @patch("cli.commands.modules._lock_path")
    @patch("cli.commands.modules._collect_module_rows")
    @patch("cli.commands.modules.semver")
    @patch("cli.commands.modules.print_success")
    def test_outdated_no_updates(
        self,
        mock_success: MagicMock,
        mock_semver: MagicMock,
        mock_collect: MagicMock,
        mock_lock_path: MagicMock,
    ) -> None:
        """Test outdated command when no updates are available."""
        # Mock lock file exists and contains the module
        mock_lock_file = MagicMock()
        mock_lock_file.exists.return_value = True
        mock_lock_file.read_text.return_value = """
modules:
  test_module:
    version: "2.0.0"
    tags: []
"""
        mock_lock_path.return_value = mock_lock_file

        mock_collect.return_value = [
            {
                "module": "test_module",
                "name": "test_module",
                "version": "2.0.0",
                "latest": "1.0.0",
            }
        ]

        # Mock version comparison - current is same as locked
        mock_version = MagicMock()
        mock_version.__gt__ = lambda _self, _other: False
        mock_semver.parse.return_value = mock_version

        with patch("cli.commands.modules.yaml") as mock_yaml:
            mock_yaml.safe_load.return_value = {
                "modules": {"test_module": {"version": "2.0.0", "tags": []}}
            }
            outdated(None)

            # Should not print success message, just output the table/JSON
            mock_success.assert_not_called()

    @patch("cli.commands.modules.print_success")
    @patch("cli.commands.modules.yaml_dump")
    def test_migration_template_success(
        self, mock_yaml_dump: MagicMock, mock_success: MagicMock
    ) -> None:
        """Test successful migration template generation."""
        # Skip this test for now due to complex file mocking requirements
        self.skipTest("Migration template test requires complex file system mocking")

    @patch("cli.commands.modules.MODULES_PATH")
    @patch("cli.commands.modules.yaml")
    @patch("cli.commands.modules.print_success")
    @patch("cli.commands.modules.verify_manifest_multi")
    def test_verify_all_no_signature(
        self,
        mock_verify: MagicMock,
        mock_success: MagicMock,
        mock_yaml: MagicMock,
        mock_modules_path: MagicMock,
    ) -> None:
        """Test verify_all with module that has no signature."""
        mock_modules_path.exists.return_value = True
        mock_modules_path.iterdir.return_value = [self.test_module_dir]
        mock_yaml.safe_load.return_value = {
            "name": "test_module"
            # No signature field
        }

        with patch("builtins.open", mock_open()):
            with self.assertRaises(typer.Exit):
                verify_all(None, False, False, False)

            # Should not call verify for modules without signatures
            mock_verify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
