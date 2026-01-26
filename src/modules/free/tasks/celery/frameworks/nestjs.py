# pyright: reportMissingImports=false
"""NestJS framework plugin for the Celery module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS wrappers around the Celery runtime."""

    @property
    def name(self) -> str:
        return "nestjs"

    @property
    def language(self) -> str:
        return "typescript"

    @property
    def display_name(self) -> str:
        return "NestJS"

    def get_template_mappings(self) -> Dict[str, str]:
        return {
            "service": "templates/variants/nestjs/celery.service.ts.j2",
            "controller": "templates/variants/nestjs/celery.controller.ts.j2",
            "module": "templates/variants/nestjs/celery.module.ts.j2",
            "configuration": "templates/variants/nestjs/celery.configuration.ts.j2",
            "health_controller": "templates/variants/nestjs/celery.health.controller.ts.j2",
            "health_module": "templates/variants/nestjs/celery.health.module.ts.j2",
            "integration_test": "templates/tests/integration/celery.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/tasks/celery/celery.service.ts",
            "controller": "src/modules/free/tasks/celery/celery.controller.ts",
            "module": "src/modules/free/tasks/celery/celery.module.ts",
            "configuration": "src/modules/free/tasks/celery/celery.configuration.ts",
            "health_controller": "src/health/celery-health.controller.ts",
            "health_module": "src/health/celery-health.module.ts",
            "integration_test": "tests/modules/integration/tasks/celery.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "module_kebab": "celery",
            "rapidkit_vendor_module": base_context.get("rapidkit_vendor_module"),
            "rapidkit_vendor_version": base_context.get("rapidkit_vendor_version"),
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "module_class_name": "Celery",
            "configuration_relative": base_context.get("nest_configuration_relative"),
            "health_controller_relative": base_context.get("nest_health_controller_relative"),
            "health_module_relative": base_context.get("nest_health_module_relative"),
            "integration_test_relative": base_context.get("nest_test_relative"),
        }

    def validate_requirements(self) -> list[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        celery_root = output_dir / "src" / "modules" / "free" / "tasks" / "celery"
        health_root = output_dir / "src" / "health"
        tests_root = output_dir / "tests" / "modules" / "integration" / "tasks"

        for path in (celery_root, health_root, tests_root):
            path.mkdir(parents=True, exist_ok=True)
