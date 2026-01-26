from core.engine.registry import KitRegistry


def test_shared_variables_merge_preserves_kit_overrides() -> None:
    registry = KitRegistry()
    kit = registry.get_kit("fastapi.standard")

    project_name_var = next(v for v in kit.variables if v.name == "project_name")
    # Ensure kit-specific description overrides shared default
    assert "snake_case" in project_name_var.description

    license_var = next(v for v in kit.variables if v.name == "license")
    assert "Apache-2.0" in license_var.choices
    # FastAPI kit defaults have been aligned to MIT in kit metadata
    assert license_var.default == "MIT"


def test_merge_variables_includes_shared_defaults() -> None:
    registry = KitRegistry()
    merged = registry._merge_variables({})  # noqa: SLF001
    assert "project_name" in merged
    assert merged["project_name"]["type"] == "string"
    assert merged["include_logging"]["default"] is True
