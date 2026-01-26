"""
Test script for the new flat module system
"""

import importlib
import sys
from pathlib import Path

# Ensure the repository root is on sys.path for absolute imports
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

get_registry = importlib.import_module("modules.free").get_registry


def test_module_registry() -> None:
    """Test the module registry functionality."""
    print("Testing Free Modules Registry...")

    registry = get_registry()

    # Test loading registry
    print("✓ Loading registry...")
    registry.load_registry()
    print(f"  Found {len(registry.modules)} modules")
    print(f"  Found {len(registry.categories)} categories")
    print(f"  Found {len(registry.priorities)} priorities")

    # Test getting modules by priority
    print("\n✓ Testing essential modules...")
    essential = registry.get_essential_modules()
    print(f"  Essential modules: {[m['name'] for m in essential]}")

    # Test getting modules by category
    print("\n✓ Testing modules by category...")
    core_modules = registry.get_modules_by_category("core")
    print(f"  Core modules: {[m['name'] for m in core_modules]}")

    # Test dependency validation
    print("\n✓ Testing dependency validation...")
    test_modules = ["users", "settings"]
    missing = registry.validate_module_dependencies(test_modules)
    if missing:
        print(f"  Missing dependencies: {missing}")
    else:
        print("  All dependencies satisfied")

    # Test install order
    print("\n✓ Testing install order...")
    order = registry.get_install_order(["users", "auth", "settings"])
    print(f"  Install order: {order}")

    # Test template path resolution
    print("\n✓ Testing template path resolution...")
    template_path = registry.get_template_path(
        "settings", "overrides/fastapi/enterprise/core/settings.py.j2"
    )
    if template_path:
        print(f"  Template path: {template_path}")
        if template_path.exists():
            print("  Settings template found")
        else:
            print("  Settings template not found")
    else:
        print("  Template path is None")

    print("\n🎉 All tests passed!")


if __name__ == "__main__":
    test_module_registry()
