# pyright: reportMissingImports=false
"""NestJS framework plugin for the Rate Limiting module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS wrappers around the rate limiter runtime."""

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
            "module": "templates/variants/nestjs/rate_limiting.module.ts.j2",
            "service": "templates/variants/nestjs/rate_limiting.service.ts.j2",
            "guard": "templates/variants/nestjs/rate_limiting.guard.ts.j2",
            "controller": "templates/variants/nestjs/rate_limiting.controller.ts.j2",
            "configuration": "templates/variants/nestjs/rate_limiting.configuration.ts.j2",
            "health_controller": "templates/variants/nestjs/rate_limiting.health.controller.ts.j2",
            "health_module": "templates/variants/nestjs/rate_limiting.health.module.ts.j2",
            "shared_types": "templates/base/rate_limiting_types.py.j2",
            "integration_test": "templates/tests/integration/rate_limiting.integration.spec.ts.j2",
            "e2e_tests": "templates/variants/nestjs/tests/rate_limiting.e2e-spec.ts",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "module": "src/modules/free/security/rate_limiting/rate-limiting.module.ts",
            "service": "src/modules/free/security/rate_limiting/rate-limiting.service.ts",
            "guard": "src/modules/free/security/rate_limiting/rate-limiting.guard.ts",
            "controller": "src/modules/free/security/rate_limiting/rate-limiting.controller.ts",
            "configuration": "src/modules/free/security/rate_limiting/rate-limiting.configuration.ts",
            "health_controller": "src/health/rate-limiting-health.controller.ts",
            "health_module": "src/health/rate-limiting-health.module.ts",
            "shared_types": "src/modules/free/security/rate_limiting/rate_limiting_types.py",
            "integration_test": "tests/modules/integration/security/rate_limiting.integration.spec.ts",
            "e2e_tests": "tests/modules/e2e/free/security/rate_limiting/rate_limiting.e2e-spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "module_kebab": "rate-limiting",
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_relative_path"),
            "configuration_relative": base_context.get("nest_configuration_relative"),
            "health_controller_relative": base_context.get("nest_health_controller_relative"),
            "health_module_relative": base_context.get("nest_health_module_relative"),
            "integration_test_relative": base_context.get("nest_test_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "security" / "rate_limiting"
        base.mkdir(parents=True, exist_ok=True)
        tests_root = output_dir / "tests" / "modules" / "integration" / "security"
        tests_root.mkdir(parents=True, exist_ok=True)

        (output_dir / "tests" / "modules" / "e2e" / "free" / "security" / "rate_limiting").mkdir(
            parents=True, exist_ok=True
        )

        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://docs.nestjs.com/",
            "rate_limiting": "https://docs.rapidkit.top/modules/rate_limiting",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "imports": ["RateLimitingModule"],
            "guards": ["RateLimitingGuard"],
        }

    def get_dependencies(self) -> List[str]:
        return [
            "@nestjs/common>=11.1.0",
            "@nestjs/core>=11.1.0",
            "@nestjs/config>=4.0.0",
            "joi>=17.0.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return []
