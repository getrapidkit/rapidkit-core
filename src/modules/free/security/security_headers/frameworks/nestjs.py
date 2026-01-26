"""NestJS framework plugin for the Security Headers module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Plugin describing NestJS-specific generation outputs."""

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
            "service": "templates/variants/nestjs/security_headers.service.ts.j2",
            "controller": "templates/variants/nestjs/security_headers.controller.ts.j2",
            "module": "templates/variants/nestjs/security_headers.module.ts.j2",
            "configuration": "templates/variants/nestjs/security_headers.configuration.ts.j2",
            "health_controller": "templates/variants/nestjs/security_headers.health.controller.ts.j2",
            "health_module": "templates/variants/nestjs/security_headers.health.module.ts.j2",
            "integration_test": "templates/tests/integration/security_headers.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/security/security_headers/security-headers/security-headers.service.ts",
            "controller": "src/modules/free/security/security_headers/security-headers/security-headers.controller.ts",
            "module": "src/modules/free/security/security_headers/security-headers/security-headers.module.ts",
            "configuration": "src/modules/free/security/security_headers/security-headers/security-headers.configuration.ts",
            "health_controller": "src/health/security-headers-health.controller.ts",
            "health_module": "src/health/security-headers-health.module.ts",
            "integration_test": "tests/modules/integration/security/security_headers.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "module_class_name": "SecurityHeaders",
            "module_kebab": "security-headers",
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_relative_path"),
            "configuration_relative": base_context.get("nest_configuration_relative"),
            "health_controller_relative": base_context.get("nest_health_controller_relative"),
            "health_module_relative": base_context.get("nest_health_module_relative"),
            "integration_test_relative": base_context.get("nest_test_relative"),
        }

    def validate_requirements(self) -> list[str]:  # noqa: D401
        """NestJS generation requires @nestjs/common to be available in the target project."""

        return []

    def get_dependencies(self) -> list[str]:
        return ["@nestjs/common", "express"]

    def pre_generation_hook(self, output_dir: Path) -> None:
        base_root = output_dir / "src" / "modules" / "free" / "security" / "security_headers"
        security_root = base_root / "security-headers"
        tests_root = output_dir / "tests" / "modules" / "integration" / "security"

        for path in (security_root, tests_root):
            path.mkdir(parents=True, exist_ok=True)

        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)


__all__ = ["NestJSPlugin"]
