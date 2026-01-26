# src / core / services / translation_utils.py
import shutil
import subprocess  # nosec
from pathlib import Path
from typing import Any, Dict

from cli.ui.printer import print_error, print_info, print_success, print_warning


def _msgfmt_bin() -> str:
    """Return absolute path to msgfmt or raise RuntimeError."""
    bin_path = shutil.which("msgfmt")
    if not bin_path:
        raise RuntimeError("msgfmt not found in PATH; please install gettext utilities")
    return bin_path


def compile_po_to_mo(po_path: Path, mo_path: Path) -> bool:
    """
    Compile a .po file to .mo using msgfmt.
    Returns True if compilation succeeded, False otherwise.
    If msgfmt is not available, skip with a warning.
    """
    if not po_path.exists():
        print_warning(f"⚠️ .po file not found: {po_path}")
        return False

    try:
        msgfmt = _msgfmt_bin()
    except RuntimeError as e:
        print_warning(str(e))
        return False

    try:
        subprocess.run(
            [msgfmt, str(po_path), "-o", str(mo_path)],
            check=True,
            capture_output=True,
        )  # nosec
        print_success(f"✅ Compiled {po_path.name} → {mo_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        stderr = ""
        try:
            stderr = e.stderr.decode().strip() if e.stderr else ""
        except UnicodeDecodeError:
            stderr = str(e)
        print_error(f"msgfmt failed for {po_path}: {stderr}")
        return False
    except (OSError, FileNotFoundError) as e:
        print_warning(f"⚠️ Failed to run msgfmt for {po_path}: {e}")
        return False


def ensure_mo_exists(mo_path: Path) -> None:
    """
    Create an empty .mo file if it does not exist.
    """
    if not mo_path.exists():
        mo_path.parent.mkdir(parents=True, exist_ok=True)
        mo_path.write_bytes(b"")
        print_warning(f"⚠️ Created empty .mo file: {mo_path}")


def process_translations(locale_dir: Path, final: bool, config: Dict[str, Any]) -> None:
    """Process translation files in the locale directory if i18n is enabled."""
    if "i18n" not in config.get("features", {}):
        print_info("⏭ i18n is disabled for this module, skipping translation processing")
        return

    if not locale_dir.exists():
        if not final:
            print_warning(f"⚠️ Locale directory not found: {locale_dir}")
        locale_dir.mkdir(parents=True, exist_ok=True)
        print_info(f"📁 Created locale directory: {locale_dir}")

    langs = [d.name for d in locale_dir.iterdir() if d.is_dir()]
    for lang in langs:
        po_path = locale_dir / lang / "LC_MESSAGES" / f"{config['name']}.po"
        mo_path = locale_dir / lang / "LC_MESSAGES" / f"{config['name']}.mo"
        if po_path.exists():
            compiled_ok = compile_po_to_mo(po_path, mo_path)
            if not compiled_ok:
                print_warning(f"⚠️ Compilation skipped/failed for {po_path}")

        if final:
            if po_path.exists():
                try:
                    po_path.unlink()
                    print_info(f"🧹 Removed {po_path.name} for production")
                except (OSError, PermissionError) as e:
                    print_warning(f"⚠️ Could not remove {po_path}: {e}")
            if not mo_path.exists():
                ensure_mo_exists(mo_path)
        elif not mo_path.exists():
            ensure_mo_exists(mo_path)


# def process_translations(locale_dir: Path, final: bool):
#     """
#     For each locale, ensure .mo is generated from .po if possible.
#     If --final: only .mo remains (even if .po is empty or missing, .mo will exist and be empty).
#     If not --final: keep both .po and .mo.
#     """
#     if not locale_dir.exists():
#         print_warning(f"⚠️ Locale directory not found: {locale_dir}")
#         return

#     # Dynamically detect all language folders
#     langs = [d.name for d in locale_dir.iterdir() if d.is_dir()]
#     for lang in langs:
#         po_path = locale_dir / lang / "LC_MESSAGES" / "auth.po"
#         mo_path = locale_dir / lang / "LC_MESSAGES" / "auth.mo"
#         # Try to compile .po to .mo if .po exists (even if empty)
#         compiled = False
#         if po_path.exists():
#             compiled = compile_po_to_mo(po_path, mo_path)
#         # If --final, remove .po and ensure .mo exists (even if empty)
#         if final:
#             if po_path.exists():
#                 try:
#                     po_path.unlink()
#                     print_info(f"🧹 Removed {po_path.name} for production")
#                 except Exception as e:
#                     print_warning(f"⚠️ Could not remove {po_path}: {e}")
#             # If .mo was not created (because .po was missing or empty), create an empty .mo
#             if not mo_path.exists():
#                 ensure_mo_exists(mo_path)
#         # If not --final and .mo does not exist (e.g. .po was missing), create empty .mo
#         elif not mo_path.exists():
#             ensure_mo_exists(mo_path)


# def process_translations(locale_dir: Path, final: bool):
#     """
#     Process translation files in the locale directory if i18n is enabled.
#     If locale directory doesn't exist, skip silently or warn in non-final mode.
#     """
#     # Check if i18n is enabled in config (assuming config is passed or globally available)
#     i18n_enabled = True  # Replace with actual config check, e.g., config.get("i18n_enabled", False)

#     if not i18n_enabled:
#         print_info("⏭ i18n is disabled, skipping translation processing")
#         return

#     if not locale_dir.exists():
#         if not final:
#             print_warning(f"⚠️ Locale directory not found: {locale_dir}")
#         return

#     # Dynamically detect all language folders
#     langs = [d.name for d in locale_dir.iterdir() if d.is_dir()]
#     for lang in langs:
#         po_path = locale_dir / lang / "LC_MESSAGES" / "auth.po"
#         mo_path = locale_dir / lang / "LC_MESSAGES" / "auth.mo"
#         # Try to compile .po to .mo if .po exists (even if empty)
#         compiled = False
#         if po_path.exists():
#             compiled = compile_po_to_mo(po_path, mo_path)
#         # If --final, remove .po and ensure .mo exists (even if empty)
#         if final:
#             if po_path.exists():
#                 try:
#                     po_path.unlink()
#                     print_info(f"🧹 Removed {po_path.name} for production")
#                 except Exception as e:
#                     print_warning(f"⚠️ Could not remove {po_path}: {e}")
#             # If .mo was not created (because .po was missing or empty), create an empty .mo
#             if not mo_path.exists():
#                 ensure_mo_exists(mo_path)
#         # If not --final and .mo does not exist (e.g. .po was missing), create empty .mo
#         elif not mo_path.exists():
#             ensure_mo_exists(mo_path)
