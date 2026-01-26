import textwrap
from pathlib import Path

import pytest

from modules.free import FreeModulesRegistry, get_registry, list_available_modules


def test_kit_support_lookup_returns_status_strings() -> None:
    registry = get_registry()

    support = registry.get_kit_support("settings")
    assert "fastapi.standard" in support
    assert support["fastapi.standard"] == "supported"
    assert support["fastapi.ddd"] == "supported"

    fastapi_status = registry.get_kit_status("settings", "fastapi/standard")
    nest_status = registry.get_kit_status("settings", "nestjs.standard")

    assert fastapi_status == "supported"
    assert nest_status == "experimental"


def test_kit_support_missing_profile_warns() -> None:
    registry = get_registry()

    assert registry.get_kit_status("db_postgres", "nestjs/standard") == "unsupported"
    assert registry.get_kit_status("db_postgres", "unknown/profile") is None


def test_module_queries_cover_basic_metadata() -> None:
    registry = get_registry()

    essentials = registry.get_modules_by_category("essentials")
    assert any(mod["name"] == "settings" for mod in essentials)

    essential_modules = registry.get_modules_by_priority("essential")
    module_names = {mod["name"] for mod in essential_modules}
    assert "settings" in module_names

    available = list_available_modules()
    assert "settings" in available


def test_template_resolution_existing_and_missing() -> None:
    registry = get_registry()

    existing = registry.get_template_path("settings", "base/settings.py.j2")
    assert existing is not None and existing.exists()

    missing = registry.get_template_path("settings", "missing-template.j2")
    assert missing is None


def test_dependency_validation_and_install_order() -> None:
    registry = get_registry()

    missing = registry.validate_module_dependencies(["db_postgres"])
    assert any("requires 'free/essentials/settings'" in msg for msg in missing)

    satisfied = registry.validate_module_dependencies(["db_postgres", "settings"])
    assert satisfied == []

    order = registry.get_install_order(["db_postgres", "settings"])
    assert order.index("free/essentials/settings") < order.index("free/database/db_postgres")


def test_custom_registry_normalizes_entries(tmp_path: Path) -> None:
    yaml_body = textwrap.dedent(
        """
                                modules:
                                        alpha:
                                                name: alpha
                                                category: demo
                                                priority: optional
                                                dependencies: []
                                categories:
                                        demo: {}
                                priorities:
                                        optional: {}
                                kit_support:
                                        alpha:
                                                123: 456
                                        beta: invalid
                                """
    )

    modules_yaml = tmp_path / "modules.yaml"
    modules_yaml.write_text(yaml_body, encoding="utf-8")

    registry = FreeModulesRegistry(str(modules_yaml))
    data = registry.load_registry()

    assert data["modules"]["alpha"]["name"] == "alpha"
    assert registry.modules["alpha"]["category"] == "demo"
    assert registry.categories == {"demo": {}}
    assert registry.priorities == {"optional": {}}

    kit_support = registry.get_kit_support("alpha")
    assert kit_support == {"123": "456"}

    # Invalid kit support entries are ignored
    assert registry.get_kit_support("beta") == {}


@pytest.mark.parametrize(
    "profile,expected",
    [
        ("fastapi.standard", "supported"),
        ("fastapi/standard", "supported"),
        ("fastapi.ddd", "supported"),
        ("fastapi/ddd", "supported"),
        ("nestjs.standard", "experimental"),
    ],
)
def test_profile_normalization_variants(profile: str, expected: str) -> None:
    registry = get_registry()
    assert registry.get_kit_status("settings", profile) == expected
