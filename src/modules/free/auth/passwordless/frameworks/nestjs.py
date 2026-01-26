# pyright: reportMissingImports=false
"""NestJS framework plugin for the Passwordless module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS passwordless authentication integrations."""

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
            "configuration": "templates/variants/nestjs/configuration.ts.j2",
            "service": "templates/variants/nestjs/passwordless.service.ts.j2",
            "module": "templates/variants/nestjs/passwordless.module.ts.j2",
            "controller": "templates/variants/nestjs/passwordless.controller.ts.j2",
            "index": "templates/variants/nestjs/index.ts.j2",
            "validation": "templates/variants/nestjs/validation.ts.j2",
            "health": "templates/variants/nestjs/passwordless.health.ts.j2",
            "routes": "templates/variants/nestjs/passwordless.routes.ts.j2",
            "tests": "templates/variants/nestjs/passwordless.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "configuration": "src/modules/free/auth/passwordless/configuration.ts",
            "service": "src/modules/free/auth/passwordless/passwordless.service.ts",
            "module": "src/modules/free/auth/passwordless/passwordless.module.ts",
            "controller": "src/modules/free/auth/passwordless/passwordless.controller.ts",
            "index": "src/modules/free/auth/passwordless/index.ts",
            "validation": "src/modules/free/auth/passwordless/config/passwordless.validation.ts",
            "health": "src/health/passwordless.health.ts",
            "routes": "src/modules/free/auth/passwordless/passwordless.routes.ts",
            "tests": "test/passwordless/passwordless.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "module_class_name": "Passwordless",
            "module_kebab": "passwordless",
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "auth_methods": ["email", "sms", "magic_link"],
            "token_expiry": 900,  # 15 minutes
            "rate_limiting": True,
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        (output_dir / "src" / "modules" / "free" / "auth" / "passwordless").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "test" / "passwordless").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None
