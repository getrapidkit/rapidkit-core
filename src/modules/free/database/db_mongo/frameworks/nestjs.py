"""NestJS framework plugin for the Db Mongo module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Plugin exposing NestJS-specific integrations for Db Mongo."""

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
            "service": "templates/variants/nestjs/db_mongo.service.ts.j2",
            "controller": "templates/variants/nestjs/db_mongo.controller.ts.j2",
            "module": "templates/variants/nestjs/db_mongo.module.ts.j2",
            "configuration": "templates/variants/nestjs/db_mongo.configuration.ts.j2",
            "health_controller": "templates/variants/nestjs/db_mongo.health.controller.ts.j2",
            "health_module": "templates/variants/nestjs/db_mongo.health.module.ts.j2",
            "integration_tests": "templates/tests/integration/db_mongo.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/database/db_mongo/db-mongo.service.ts",
            "controller": "src/modules/free/database/db_mongo/db-mongo.controller.ts",
            "module": "src/modules/free/database/db_mongo/db-mongo.module.ts",
            "configuration": "src/modules/free/database/db_mongo/db-mongo.configuration.ts",
            "health_controller": "src/health/db-mongo-health.controller.ts",
            "health_module": "src/health/db-mongo-health.module.ts",
            "integration_tests": "tests/modules/integration/database/db_mongo.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "module_kebab": base_context.get("module_kebab"),
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "configuration_output_relative": base_context.get("nest_configuration_relative"),
            "health_controller_relative": base_context.get("nest_health_controller_relative"),
            "health_module_relative": base_context.get("nest_health_module_relative"),
            "integration_test_relative": base_context.get("nest_test_relative"),
        }

    def validate_requirements(self) -> list[str]:  # noqa: D401
        """NestJS templates do not impose runtime requirements for generation."""

        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "database" / "db_mongo"
        module_root.mkdir(parents=True, exist_ok=True)
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "nestjs").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "database").mkdir(
            parents=True, exist_ok=True
        )

    def get_dependencies(self) -> list[str]:
        return ["@nestjs/common", "@nestjs/config", "mongodb"]

    def get_dev_dependencies(self) -> list[str]:
        return ["@types/node", "@types/mongodb"]


__all__ = ["NestJSPlugin"]
