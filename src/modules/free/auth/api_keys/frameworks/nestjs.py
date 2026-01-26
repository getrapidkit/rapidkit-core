"""NestJS framework plugin for the Api Keys module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)


class NestJSPlugin(FrameworkPlugin):
    """Plugin providing NestJS-specific code generation for Api Keys."""

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
            "service": "templates/variants/nestjs/api_keys.service.ts.j2",
            "controller": "templates/variants/nestjs/api_keys.controller.ts.j2",
            "module": "templates/variants/nestjs/api_keys.module.ts.j2",
            "health": "templates/variants/nestjs/api_keys.health.ts.j2",
            "configuration": "templates/variants/nestjs/api_keys.configuration.ts.j2",
            "tests": "templates/variants/nestjs/api_keys.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/auth/api_keys/api-keys.service.ts",
            "controller": "src/modules/free/auth/api_keys/api-keys.controller.ts",
            "module": "src/modules/free/auth/api_keys/api-keys.module.ts",
            "health": "src/modules/free/auth/api_keys/api-keys.health.ts",
            "configuration": "src/modules/free/auth/api_keys/api-keys.configuration.ts",
            "tests": "test/api-keys/api-keys.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_runtime_relative"),
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_nest_module_relative"
            ),
        }

    def pre_generation_hook(self, output_dir: Path) -> None:
        (output_dir / "src" / "modules" / "free" / "auth" / "api_keys" / "api-keys").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "test" / "api-keys").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def validate_requirements(self) -> List[str]:
        # NestJS dependencies are surfaced in generated package.json templates.
        return []

    def get_dependencies(self) -> List[str]:
        return [
            "@nestjs/common>=10.0.0",
            "uuid>=9.0.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "@nestjs/testing>=10.0.0",
            "ts-jest>=29.1.0",
        ]

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://docs.nestjs.com/",
            "security": "https://docs.nestjs.com/security/authentication",
        }


__all__ = ["NestJSPlugin"]
