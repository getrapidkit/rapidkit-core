from types import SimpleNamespace

from core.config.kit_config import Variable, VariableType
from core.services.project_creator import ProjectCreatorService


def test_apply_kit_defaults_injects_missing_defaults() -> None:
    service = ProjectCreatorService()
    kit_config = SimpleNamespace(
        variables=[
            Variable(name="package_manager", type=VariableType.CHOICE, default="npm"),
            Variable(name="docker_support", type=VariableType.BOOLEAN, default=True),
        ]
    )

    merged = service._apply_kit_defaults(kit_config, {})  # noqa: SLF001

    assert merged["package_manager"] == "npm"
    assert merged["docker_support"] is True


def test_apply_kit_defaults_preserves_explicit_values() -> None:
    service = ProjectCreatorService()
    kit_config = SimpleNamespace(
        variables=[
            Variable(name="package_manager", type=VariableType.CHOICE, default="npm"),
            Variable(name="include_docs", type=VariableType.BOOLEAN, default=True),
        ]
    )

    merged = service._apply_kit_defaults(  # noqa: SLF001
        kit_config,
        {"package_manager": "yarn", "include_docs": False},
    )

    assert merged["package_manager"] == "yarn"
    assert merged["include_docs"] is False


def test_apply_kit_defaults_skips_none_defaults() -> None:
    service = ProjectCreatorService()
    kit_config = SimpleNamespace(
        variables=[
            Variable(name="custom_var", type=VariableType.STRING, default=None),
        ]
    )

    merged = service._apply_kit_defaults(kit_config, {})  # noqa: SLF001

    assert "custom_var" not in merged
