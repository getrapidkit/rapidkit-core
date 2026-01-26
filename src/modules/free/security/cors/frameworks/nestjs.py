# pyright: reportMissingImports=false
"""NestJS framework plugin for the Cors module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS wrappers around the Cors runtime."""

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
            "service": "templates/variants/nestjs/cors.service.ts.j2",
            "controller": "templates/variants/nestjs/cors.controller.ts.j2",
            "module": "templates/variants/nestjs/cors.module.ts.j2",
            "health": "templates/variants/nestjs/cors.health.ts.j2",
            "shared_types": "templates/base/cors_types.py.j2",
            "routes": "templates/variants/nestjs/cors.routes.ts.j2",
            "configuration_ts": "templates/variants/nestjs/cors.configuration.ts.j2",
            "integration_test": "templates/tests/integration/test_cors_integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/security/cors/cors.service.ts",
            "controller": "src/modules/free/security/cors/cors.controller.ts",
            "module": "src/modules/free/security/cors/cors.module.ts",
            "health": "src/modules/free/security/cors/cors.health.ts",
            "shared_types": "src/modules/free/security/cors/cors_types.py",
            "routes": "src/modules/free/security/cors/cors.routes.ts",
            "configuration_ts": "src/modules/free/security/cors/cors.configuration.ts",
            "integration_test": "tests/modules/integration/security/cors.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "module_kebab": "cors",
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "module_class_name": "Cors",
            "module_health_controller_class": "CorsHealthController",
            "module_routes_constant": "CORS_ROUTES",
            "nest_configuration_relative": base_context.get("nest_configuration_relative"),
            "nest_routes_relative": base_context.get("nest_routes_relative"),
            "nest_health_relative": base_context.get("nest_health_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        (output_dir / "src" / "modules" / "free" / "security" / "cors").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "tests" / "modules" / "integration" / "security").mkdir(
            parents=True, exist_ok=True
        )

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "nestjs": "https://docs.nestjs.com/",
            "cors": "https://docs.nestjs.com/security/cors",
        }

    def get_dependencies(self) -> List[str]:
        return [
            "@nestjs/common@^11.0.0",
            "@nestjs/core@^11.0.0",
            "@nestjs/config@^4.0.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "@nestjs/testing@^11.0.0",
            "typescript@^5.1.0",
        ]


class NestJSStandardPlugin(NestJSPlugin):
    """Alias plugin so nestjs.standard consumers reuse the NestJS implementation."""

    @property
    def name(self) -> str:  # noqa: D401
        return "nestjs.standard"

    @property
    def display_name(self) -> str:
        return "NestJS (standard kit)"
