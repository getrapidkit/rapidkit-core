# pyright: reportMissingImports=false
"""NestJS framework plugin for the File Storage module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)


class NestJSPlugin(FrameworkPlugin):
    """Generate NestJS bindings for the storage runtime."""

    @property
    def name(self) -> str:  # noqa: D401 - short alias
        return "nestjs"

    @property
    def language(self) -> str:  # noqa: D401 - short alias
        return "typescript"

    @property
    def display_name(self) -> str:  # noqa: D401 - short alias
        return "NestJS"

    def get_template_mappings(self) -> Dict[str, str]:
        return {
            "service": "templates/variants/nestjs/storage.service.ts.j2",
            "controller": "templates/variants/nestjs/storage.controller.ts.j2",
            "module": "templates/variants/nestjs/storage.module.ts.j2",
            "health": "templates/variants/nestjs/storage.health.ts.j2",
            "routes": "templates/variants/nestjs/storage.routes.ts.j2",
            "configuration_ts": "templates/variants/nestjs/storage.configuration.ts.j2",
            "integration_test": "templates/variants/nestjs/__tests__/storage.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/business/storage/storage.service.ts",
            "controller": "src/modules/free/business/storage/storage.controller.ts",
            "module": "src/modules/free/business/storage/storage.module.ts",
            "health": "src/modules/free/business/storage/storage.health.ts",
            "routes": "src/modules/free/business/storage/storage.routes.ts",
            "configuration_ts": "src/modules/free/business/storage/storage.configuration.ts",
            "integration_test": "tests/modules/integration/business/storage/storage.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "module_kebab": "storage",
            "module_camel": "storage",
            "module_service_class": "StorageService",
            "module_controller_class": "StorageController",
            "module_module_class": "StorageModule",
            "module_health_controller_class": "StorageHealthController",
        }

    def validate_requirements(self) -> list[str]:
        return []

    def get_dependencies(self) -> list[str]:
        return [
            "@nestjs/common@^10.0.0",
            "@nestjs/core@^10.0.0",
            "@nestjs/config@^3.0.0",
            "@nestjs/platform-express@^10.0.0",
            "reflect-metadata@^0.1.13",
            "rxjs@^7.5.0",
            "sharp@^0.32.0",
            "aws-sdk@^2.1000.0",
            "@google-cloud/storage@^6.0.0",
        ]

    def get_dev_dependencies(self) -> list[str]:
        return [
            "@nestjs/testing@^10.0.0",
            "@types/jest@^29.0.0",
            "@types/supertest@^2.0.0",
            "jest@^29.0.0",
            "supertest@^6.3.0",
            "ts-jest@^29.0.0",
            "@faker-js/faker@^8.0.0",
        ]

    def pre_generation_hook(self, output_dir: Path) -> None:
        (output_dir / "src" / "modules" / "free" / "business" / "storage").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "tests" / "modules" / "integration" / "business").mkdir(
            parents=True, exist_ok=True
        )
