# pyright: reportMissingImports=false
"""NestJS framework plugin for the DatabasePostgres module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS wrappers around PostgreSQL database runtime."""

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
            "service": "templates/variants/nestjs/postgres.service.ts.j2",
            "module": "templates/variants/nestjs/postgres.module.ts.j2",
            "pg_types": "templates/variants/nestjs/pg.d.ts.j2",
            "health_controller": "templates/variants/nestjs/postgres-health.controller.ts.j2",
            "health_module": "templates/variants/nestjs/postgres-health.module.ts.j2",
            "config": "templates/vendor/nestjs/configuration.js.j2",
            "integration_tests": "templates/tests/integration/postgres.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/database/db_postgres/postgres.service.ts",
            "module": "src/modules/free/database/db_postgres/postgres.module.ts",
            "pg_types": "src/modules/free/database/db_postgres/pg.d.ts",
            "health_controller": "src/health/postgres-health.controller.ts",
            "health_module": "src/health/postgres-health.module.ts",
            "config": "nestjs/configuration.js",
            "integration_tests": "tests/modules/integration/database/postgres.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "module_class_name": "DatabasePostgres",
            "module_kebab": "database-postgres",
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative",
            ),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "database" / "db_postgres"
        module_root.mkdir(parents=True, exist_ok=True)
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "nestjs").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "database").mkdir(
            parents=True, exist_ok=True
        )

    def post_generation_hook(self, output_dir: Path) -> None:
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://nestjs.com/",
            "typeorm_docs": "https://typeorm.io/",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "database_url": "postgresql://user:password@localhost:5432/dbname",
        }

    def get_dependencies(self) -> List[str]:
        return [
            "@nestjs/common",
            "@nestjs/config",
            "@nestjs/typeorm",
            "typeorm",
            "pg",
            "@types/pg",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "@types/node",
            "@types/pg",
        ]
