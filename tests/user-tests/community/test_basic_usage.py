"""
Basic usage tests for RapidKit Core
These tests demonstrate common usage patterns for core users
"""

from pathlib import Path


def test_basic_project_creation() -> None:
    """
    Test basic project creation workflow
    Shows users how to create a simple RapidKit project
    """
    print("🔧 Testing basic project creation workflow...")

    # This would be a real test that:
    # 1. Creates a temporary directory
    # 2. Initializes a basic RapidKit project
    # 3. Verifies the structure is correct
    # 4. Cleans up

    # For now, just demonstrate the concept
    current_dir = Path.cwd()

    # Check if we have the necessary files for project creation
    required_files = ["pyproject.toml", "src/rapidkit/__init__.py"]

    missing_files = []
    for file_path in required_files:
        if not (current_dir / file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"⚠️  Missing files for project creation: {missing_files}")
        print("💡 Make sure you're in a complete RapidKit project directory")
    else:
        print("✅ Project structure looks good for creation")

    print("✅ Basic project creation test completed")


def test_configuration_access() -> None:
    """
    Test accessing and using RapidKit configuration
    Shows users how to work with configuration files
    """
    print("⚙️  Testing configuration access...")

    current_dir = Path.cwd()

    # Look for configuration files
    config_files = ["pyproject.toml", "poetry.lock", "requirements.txt"]

    found_configs = []
    for config_file in config_files:
        if (current_dir / config_file).exists():
            found_configs.append(config_file)

    if found_configs:
        print(f"✅ Found configuration files: {found_configs}")
        print("💡 You can use these files to configure your RapidKit project")
    else:
        print("⚠️  No configuration files found")
        print("💡 Consider creating a pyproject.toml for your project")

    print("✅ Configuration access test completed")


def test_module_discovery() -> None:
    """
    Test discovering available modules
    Helps users understand what modules are available in their tier
    """
    print("🔍 Testing module discovery...")

    current_dir = Path.cwd()
    modules_dir = current_dir / "src" / "modules"

    if modules_dir.exists():
        # List available modules
        modules = []
        for item in modules_dir.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                modules.append(item.name)

        if modules:
            print(f"✅ Found {len(modules)} modules: {modules}")
            print("💡 These modules are available in your current tier")
        else:
            print("⚠️  No modules found in src/modules/")
            print("💡 This might be normal if you're in a minimal setup")
    else:
        print("⚠️  Modules directory not found")
        print("💡 Make sure you're in the correct RapidKit directory")

    print("✅ Module discovery test completed")
