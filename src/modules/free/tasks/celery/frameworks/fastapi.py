# pyright: reportMissingImports=false
"""FastAPI framework plugin for the Celery module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-oriented Celery integrations."""

    @property
    def name(self) -> str:
        return "fastapi"

    @property
    def language(self) -> str:
        return "python"

    @property
    def display_name(self) -> str:
        return "FastAPI"

    def get_template_mappings(self) -> Dict[str, str]:
        return {
            "runtime_wrapper": "templates/variants/fastapi/celery.py.j2",
            "metadata_routes": "templates/variants/fastapi/celery_routes.py.j2",
            "config_yaml": "templates/variants/fastapi/celery_config.yaml.j2",
            "integration_test": "templates/tests/integration/test_celery_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime_wrapper": "src/modules/free/tasks/celery/celery.py",
            "metadata_routes": "src/modules/free/tasks/celery/celery_routes.py",
            "config_yaml": "config/tasks/celery.yaml",
            "integration_test": "tests/modules/integration/tasks/test_celery_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_relative_path"),
            "rapidkit_vendor_module": base_context.get("rapidkit_vendor_module"),
            "rapidkit_vendor_version": base_context.get("rapidkit_vendor_version"),
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "module_class_name": "Celery",
            "module_kebab": "celery",
            "config_relative": base_context.get("fastapi_config_relative"),
            "integration_test_relative": base_context.get("fastapi_test_relative"),
        }

    def validate_requirements(self) -> list[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "tasks" / "celery"
        config_root = output_dir / "config" / "tasks"
        tests_root = output_dir / "tests" / "modules" / "integration" / "tasks"

        for path in (module_root, config_root, tests_root):
            path.mkdir(parents=True, exist_ok=True)

        # Materialise vendor-backed health shim and ensure health package
        # Best-effort: don't fail generation if vendor content cannot be materialised
        with suppress(RuntimeError, OSError):
            ensure_vendor_health_shim(output_dir, spec=HEALTH_SHIM_SPEC)

        ensure_health_package(
            output_dir,
            extra_imports=[
                (
                    f"src.health.{HEALTH_SHIM_SPEC.module_name}",
                    f"register_{HEALTH_SHIM_SPEC.module_name}_health",
                )
            ],
        )
