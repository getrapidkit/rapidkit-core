import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import core.services.translation_utils as translation_utils_module
from core.services.translation_utils import (
    _msgfmt_bin,
    compile_po_to_mo,
    ensure_mo_exists,
    process_translations,
)


class TestMsgfmtBin(unittest.TestCase):
    """Test cases for _msgfmt_bin function"""

    @patch("shutil.which")
    def test_msgfmt_bin_found(self, mock_which) -> None:
        """Test when msgfmt is found in PATH"""
        mock_which.return_value = "/usr/bin/msgfmt"
        result = _msgfmt_bin()
        self.assertEqual(result, "/usr/bin/msgfmt")

    @patch("shutil.which")
    def test_msgfmt_bin_not_found(self, mock_which) -> None:
        """Test when msgfmt is not found in PATH"""
        mock_which.return_value = None
        with self.assertRaises(RuntimeError) as cm:
            _msgfmt_bin()
        self.assertIn("msgfmt not found in PATH", str(cm.exception))


class TestCompilePoToMo(unittest.TestCase):
    """Test cases for compile_po_to_mo function"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.po_path = self.temp_dir / "test.po"
        self.mo_path = self.temp_dir / "test.mo"

    def tearDown(self) -> None:
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_compile_po_to_mo_po_not_exists(self) -> None:
        """Test when .po file doesn't exist"""
        with patch.object(translation_utils_module, "print_warning") as mock_warning:
            result = compile_po_to_mo(self.po_path, self.mo_path)
            self.assertFalse(result)
            mock_warning.assert_called_once()

    @patch.object(translation_utils_module, "_msgfmt_bin")
    def test_compile_po_to_mo_msgfmt_not_found(self, mock_msgfmt_bin) -> None:
        """Test when msgfmt binary is not found"""
        self.po_path.write_text("# Test PO file")
        mock_msgfmt_bin.side_effect = RuntimeError("msgfmt not found")

        with patch.object(translation_utils_module, "print_warning") as mock_warning:
            result = compile_po_to_mo(self.po_path, self.mo_path)
            self.assertFalse(result)
            self.assertEqual(mock_warning.call_count, 1)

    @patch.object(translation_utils_module, "_msgfmt_bin")
    @patch("subprocess.run")
    def test_compile_po_to_mo_success(self, mock_run, mock_msgfmt_bin) -> None:
        """Test successful compilation"""
        self.po_path.write_text("# Test PO file")
        mock_msgfmt_bin.return_value = "/usr/bin/msgfmt"
        mock_run.return_value = MagicMock()

        with patch.object(translation_utils_module, "print_success") as mock_success:
            result = compile_po_to_mo(self.po_path, self.mo_path)
            self.assertTrue(result)
            mock_success.assert_called_once()
            mock_run.assert_called_once_with(
                ["/usr/bin/msgfmt", str(self.po_path), "-o", str(self.mo_path)],
                check=True,
                capture_output=True,
            )

    @patch.object(translation_utils_module, "_msgfmt_bin")
    @patch("subprocess.run")
    def test_compile_po_to_mo_compilation_failed(
        self, mock_run: MagicMock, mock_msgfmt_bin: MagicMock
    ) -> None:
        """Test when compilation fails"""
        self.po_path.write_text("# Test PO file")
        mock_msgfmt_bin.return_value = "/usr/bin/msgfmt"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "msgfmt", stderr=b"Compilation error"
        )

        with patch.object(translation_utils_module, "print_error") as mock_error:
            result = compile_po_to_mo(self.po_path, self.mo_path)
            self.assertFalse(result)
            mock_error.assert_called_once()
            # Verify the error message contains the stderr content
            call_args = mock_error.call_args[0][0]
            self.assertIn("Compilation error", call_args)

    @patch.object(translation_utils_module, "_msgfmt_bin")
    @patch("subprocess.run")
    def test_compile_po_to_mo_unicode_decode_error(
        self, mock_run: MagicMock, mock_msgfmt_bin: MagicMock
    ) -> None:
        """Test when UnicodeDecodeError occurs while decoding stderr"""
        self.po_path.write_text("# Test PO file")
        mock_msgfmt_bin.return_value = "/usr/bin/msgfmt"

        # Create a CalledProcessError with bytes that can't be decoded
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "msgfmt", stderr=b"\xff\xfe\xfd"  # Invalid UTF-8 bytes
        )

        with patch.object(translation_utils_module, "print_error") as mock_error:
            result = compile_po_to_mo(self.po_path, self.mo_path)
            self.assertFalse(result)
            mock_error.assert_called_once()
            # Verify the error message contains the CalledProcessError string representation
            call_args = mock_error.call_args[0][0]
            self.assertIn("msgfmt failed for", call_args)


class TestEnsureMoExists(unittest.TestCase):
    """Test cases for ensure_mo_exists function"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mo_path = self.temp_dir / "test.mo"

    def tearDown(self) -> None:
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_ensure_mo_exists_already_exists(self) -> None:
        """Test when .mo file already exists"""
        self.mo_path.write_bytes(b"existing content")
        with patch.object(translation_utils_module, "print_warning") as mock_warning:
            ensure_mo_exists(self.mo_path)
            mock_warning.assert_not_called()
            self.assertEqual(self.mo_path.read_bytes(), b"existing content")

    def test_ensure_mo_exists_creates_empty(self) -> None:
        """Test creating empty .mo file when it doesn't exist"""
        with patch.object(translation_utils_module, "print_warning") as mock_warning:
            ensure_mo_exists(self.mo_path)
            mock_warning.assert_called_once()
            self.assertTrue(self.mo_path.exists())
            self.assertEqual(self.mo_path.read_bytes(), b"")

    def test_ensure_mo_exists_creates_parent_dirs(self) -> None:
        """Test creating parent directories when needed"""
        nested_mo_path = self.temp_dir / "locale" / "en" / "LC_MESSAGES" / "test.mo"
        with patch.object(translation_utils_module, "print_warning") as mock_warning:
            ensure_mo_exists(nested_mo_path)
            mock_warning.assert_called_once()
            self.assertTrue(nested_mo_path.exists())
            self.assertEqual(nested_mo_path.read_bytes(), b"")


class TestProcessTranslations(unittest.TestCase):
    """Test cases for process_translations function"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.locale_dir = self.temp_dir / "locale"

    def tearDown(self) -> None:
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_process_translations_i18n_disabled(self) -> None:
        """Test when i18n is disabled"""
        config = {"features": {}, "name": "test"}
        with patch.object(translation_utils_module, "print_info") as mock_info:
            process_translations(self.locale_dir, False, config)
            mock_info.assert_called_once_with(
                "⏭ i18n is disabled for this module, skipping translation processing"
            )

    def test_process_translations_locale_dir_not_exists_non_final(self) -> None:
        """Test when locale directory doesn't exist in non-final mode"""
        config = {"features": {"i18n": True}, "name": "test"}
        with (
            patch.object(translation_utils_module, "print_warning") as mock_warning,
            patch.object(translation_utils_module, "print_info") as mock_info,
        ):
            process_translations(self.locale_dir, False, config)
            mock_warning.assert_called_once()
            mock_info.assert_called_once()
            self.assertTrue(self.locale_dir.exists())

    def test_process_translations_no_languages(self) -> None:
        """Test when locale directory exists but has no language directories"""
        self.locale_dir.mkdir()
        config = {"features": {"i18n": True}, "name": "test"}
        # Should not raise any errors
        process_translations(self.locale_dir, False, config)

    @patch.object(translation_utils_module, "compile_po_to_mo")
    @patch.object(translation_utils_module, "ensure_mo_exists")
    def test_process_translations_with_po_file(
        self, mock_ensure_mo: MagicMock, mock_compile: MagicMock
    ) -> None:
        """Test processing when .po file exists"""
        self.locale_dir.mkdir()
        lang_dir = self.locale_dir / "en" / "LC_MESSAGES"
        lang_dir.mkdir(parents=True)
        po_file = lang_dir / "test.po"
        po_file.write_text("# Test PO file")
        mo_file = lang_dir / "test.mo"

        config = {"features": {"i18n": True}, "name": "test"}

        # Simulate successful compilation
        def mock_compile_func(*_args: Any, **_kwargs: Any) -> bool:
            mo_file.write_bytes(b"compiled")
            return True

        mock_compile.side_effect = mock_compile_func

        process_translations(self.locale_dir, False, config)

        mock_compile.assert_called_once()
        mock_ensure_mo.assert_not_called()
        self.assertTrue(mo_file.exists())

    @patch.object(translation_utils_module, "compile_po_to_mo")
    @patch.object(translation_utils_module, "ensure_mo_exists")
    def test_process_translations_compilation_failed(
        self, mock_ensure_mo: MagicMock, mock_compile: MagicMock
    ) -> None:
        """Test when compilation fails"""
        self.locale_dir.mkdir()
        lang_dir = self.locale_dir / "en" / "LC_MESSAGES"
        lang_dir.mkdir(parents=True)
        po_file = lang_dir / "test.po"
        po_file.write_text("# Test PO file")

        config = {"features": {"i18n": True}, "name": "test"}
        mock_compile.return_value = False

        with patch.object(translation_utils_module, "print_warning") as mock_warning:
            process_translations(self.locale_dir, False, config)
            # Should warn about compilation failure
            self.assertTrue(mock_warning.call_count >= 1)
            # Should ensure .mo exists since compilation failed and it's not final mode
            mock_ensure_mo.assert_called_once()

    @patch.object(translation_utils_module, "compile_po_to_mo")
    @patch.object(translation_utils_module, "ensure_mo_exists")
    def test_process_translations_final_mode_with_po(
        self, mock_ensure_mo: MagicMock, mock_compile: MagicMock
    ) -> None:
        """Test final mode processing with .po file"""
        self.locale_dir.mkdir()
        lang_dir = self.locale_dir / "en" / "LC_MESSAGES"
        lang_dir.mkdir(parents=True)
        po_file = lang_dir / "test.po"
        po_file.write_text("# Test PO file")
        mo_file = lang_dir / "test.mo"
        mo_file.write_text("compiled content")

        config = {"features": {"i18n": True}, "name": "test"}
        mock_compile.return_value = True

        with patch.object(translation_utils_module, "print_info") as mock_info:
            process_translations(self.locale_dir, True, config)
            mock_compile.assert_called_once()
            mock_info.assert_called_once()  # For removing .po file
            self.assertFalse(po_file.exists())
            self.assertTrue(mo_file.exists())

    @patch.object(translation_utils_module, "compile_po_to_mo")
    @patch.object(translation_utils_module, "ensure_mo_exists")
    def test_process_translations_final_mode_no_mo(
        self, mock_ensure_mo: MagicMock, mock_compile: MagicMock
    ) -> None:
        """Test final mode when .mo doesn't exist"""
        self.locale_dir.mkdir()
        lang_dir = self.locale_dir / "en" / "LC_MESSAGES"
        lang_dir.mkdir(parents=True)
        po_file = lang_dir / "test.po"
        po_file.write_text("# Test PO file")

        config = {"features": {"i18n": True}, "name": "test"}
        mock_compile.return_value = False

        process_translations(self.locale_dir, True, config)

        mock_compile.assert_called_once()
        mock_ensure_mo.assert_called_once()

    @patch.object(translation_utils_module, "compile_po_to_mo")
    @patch.object(translation_utils_module, "ensure_mo_exists")
    def test_process_translations_non_final_no_mo(
        self, mock_ensure_mo: MagicMock, mock_compile: MagicMock
    ) -> None:
        """Test non-final mode when .mo doesn't exist"""
        self.locale_dir.mkdir()
        lang_dir = self.locale_dir / "en" / "LC_MESSAGES"
        lang_dir.mkdir(parents=True)
        po_file = lang_dir / "test.po"
        po_file.write_text("# Test PO file")
        mo_file = lang_dir / "test.mo"

        # Simulate successful compilation by creating the .mo file
        def mock_compile_func(*_args: Any, **_kwargs: Any) -> bool:
            mo_file.write_bytes(b"compiled")
            return True

        mock_compile.side_effect = mock_compile_func

        config = {"features": {"i18n": True}, "name": "test"}

        process_translations(self.locale_dir, False, config)

        mock_compile.assert_called_once()
        mock_ensure_mo.assert_not_called()
        self.assertTrue(mo_file.exists())

    @patch.object(translation_utils_module, "compile_po_to_mo")
    @patch.object(translation_utils_module, "ensure_mo_exists")
    def test_process_translations_remove_po_error(
        self, mock_ensure_mo: MagicMock, mock_compile: MagicMock
    ) -> None:
        """Test error when removing .po file in final mode"""
        self.locale_dir.mkdir()
        lang_dir = self.locale_dir / "en" / "LC_MESSAGES"
        lang_dir.mkdir(parents=True)
        po_file = lang_dir / "test.po"
        po_file.write_text("# Test PO file")

        config = {"features": {"i18n": True}, "name": "test"}
        mock_compile.return_value = True

        with (
            patch("pathlib.Path.unlink", side_effect=OSError("Permission denied")),
            patch.object(translation_utils_module, "print_warning") as mock_warning,
        ):
            process_translations(self.locale_dir, True, config)
            mock_warning.assert_called()


if __name__ == "__main__":
    unittest.main()
