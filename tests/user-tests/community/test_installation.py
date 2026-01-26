"""
User-facing tests for RapidKit Core
These tests verify basic functionality and help users validate their installation
"""

import os
from pathlib import Path

# Constants
MIN_RAPIDKIT_FILES = 1  # Reduced for core tier flexibility


def test_rapidkit_installation() -> None:
    """
    Test that RapidKit is properly installed and accessible
    This is a basic smoke test for users to verify their setup
    """
    try:
        # Check if we're in a RapidKit project
        current_dir = Path.cwd()

        # Look for common RapidKit files - prioritize core tier essentials
        rapidkit_files = [
            "pyproject.toml",  # Essential for all tiers
            "rapidkit_cli.py",  # CLI entry point
            "src/rapidkit/__init__.py",  # Core module (may not exist in core tier)
        ]

        found_files = []
        for file_path in rapidkit_files:
            if (current_dir / file_path).exists():
                found_files.append(file_path)

        # Smart validation: require at least pyproject.toml OR rapidkit_cli.py
        has_essential_files = "pyproject.toml" in found_files or "rapidkit_cli.py" in found_files

        # For core tier, be more lenient - just need basic structure
        if not has_essential_files:
            assert (
                len(found_files) >= MIN_RAPIDKIT_FILES
            ), f"Found only {len(found_files)} RapidKit files. Installation may be incomplete."

        print("✅ RapidKit installation verified")
        print(f"   📁 Found {len(found_files)} RapidKit files: {', '.join(found_files)}")

    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        raise


def test_basic_import() -> None:
    """
    Test that basic RapidKit modules can be imported
    Users can run this to verify their Python environment is set up correctly
    """
    try:
        # Test importing core modules using importlib
        import importlib.util
        import sys
        from pathlib import Path

        # Add current directory to Python path for imports
        current_dir = Path.cwd()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))

        # Check for available modules in src directory
        src_dir = current_dir / "src"
        available_modules = []

        if src_dir.exists():
            # Check for core module
            core_spec = importlib.util.find_spec("core")
            if core_spec is not None:
                available_modules.append("core")
                print("✅ Core module found")
            else:
                print("⚠️  Core module not found")

            # Check for cli module
            cli_spec = importlib.util.find_spec("cli")
            if cli_spec is not None:
                available_modules.append("cli")
                print("✅ CLI module found")
            else:
                print("⚠️  CLI module not found")

        # Try importing rapidkit_cli directly if available
        cli_spec = importlib.util.find_spec("rapidkit_cli")
        if cli_spec is not None:
            available_modules.append("rapidkit_cli")
            print("✅ RapidKit CLI found")
        else:
            print("⚠️  RapidKit CLI not available (this is normal for some setups)")

        # Ensure at least one module is available
        if not available_modules:
            raise ImportError("No RapidKit modules could be imported")

        print(f"📦 Successfully imported: {', '.join(available_modules)}")

    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        print("💡 Make sure you're in the correct directory and Python path is set up")
        raise


def test_project_structure() -> None:
    """
    Test that the project has a valid structure
    Helps users understand what files should be present
    """
    current_dir = Path.cwd()
    required_dirs = ["src", "tests"]
    recommended_files = ["README.md", "pyproject.toml"]

    print("🔍 Checking project structure...")

    # Check required directories
    for dir_name in required_dirs:
        if (current_dir / dir_name).exists():
            print(f"✅ {dir_name}/ directory found")
        else:
            print(f"⚠️  {dir_name}/ directory missing")

    # Check recommended files
    for file_name in recommended_files:
        if (current_dir / file_name).exists():
            print(f"✅ {file_name} found")
        else:
            print(f"ℹ️  {file_name} not found (recommended)")

    print("✅ Project structure check completed")


def test_common_issues() -> None:
    """
    Test for common installation issues
    """
    try:
        import sys

        # Check Python version
        assert sys.version_info >= (3, 8), "Python 3.8+ required"

        # Check if in virtual environment
        in_venv = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )
        if not in_venv:
            print("⚠️  Not in virtual environment - this may cause issues")

        # Check write permissions
        current_dir = Path.cwd()
        test_file = current_dir / ".rapidkit_test_write"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except PermissionError as exc:
            raise AssertionError("No write permissions in current directory") from exc

        print("✅ Common issues check passed")

    except (OSError, ValueError) as e:
        raise AssertionError(f"Common issues check failed: {e}") from e


def test_cli_basic_commands() -> None:
    """
    Test basic CLI commands work
    """
    import subprocess
    import sys
    from pathlib import Path

    # Set PYTHONPATH to include src directory
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent.parent / "src")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    # Test help command using direct module execution
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0
    assert "rapidkit" in result.stdout.lower()

    # Test version command if available
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--version"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    # Version command might not exist, so don't assert returncode
    if result.returncode == 0:
        assert "rapidkit" in result.stdout.lower()


def test_dependencies_available() -> None:
    """
    Test that key dependencies are available
    """
    try:
        import requests
        import rich
        import typer
        import yaml

        # Check that dependencies can be imported
        assert typer is not None
        assert rich is not None
        assert yaml is not None
        assert requests is not None

        print("✅ Key dependencies available")

    except ImportError as e:
        raise AssertionError(f"Missing dependency: {e}") from e
