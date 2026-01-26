"""NestJS framework plugin for Observability Core."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Plugin exposing NestJS-specific integrations for Observability Core."""

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
            "service": "templates/variants/nestjs/observability_core.service.ts.j2",
            "controller": "templates/variants/nestjs/observability_core.controller.ts.j2",
            "module": "templates/variants/nestjs/observability_core.module.ts.j2",
            "configuration": "templates/variants/nestjs/observability_core.configuration.ts.j2",
            "health_controller": "templates/variants/nestjs/observability_core.health.controller.ts.j2",
            "health_module": "templates/variants/nestjs/observability_core.health.module.ts.j2",
            "integration_tests": "templates/tests/integration/observability_core.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/observability/core/observability-core/observability-core.service.ts",
            "controller": "src/modules/free/observability/core/observability-core/observability-core.controller.ts",
            "module": "src/modules/free/observability/core/observability-core/observability-core.module.ts",
            "configuration": "src/modules/free/observability/core/observability-core/observability-core.configuration.ts",
            "health_controller": "src/health/observability-core-health.controller.ts",
            "health_module": "src/health/observability-core-health.module.ts",
            "integration_tests": "tests/modules/integration/observability/observability_core.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "metrics_endpoint": base_context.get("metrics_endpoint", "/metrics"),
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "configuration_output_relative": base_context.get("nest_configuration_relative"),
            "health_controller_relative": base_context.get("nest_health_controller_relative"),
            "health_module_relative": base_context.get("nest_health_module_relative"),
            "integration_test_relative": base_context.get("nest_test_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "observability" / "core"
        (base / "observability-core").mkdir(parents=True, exist_ok=True)
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "observability").mkdir(
            parents=True, exist_ok=True
        )

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_dependencies(self) -> List[str]:
        return [
            "@nestjs/common@^10.0.0",
            "@nestjs/core@^10.0.0",
            "rxjs@^7.8.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return []

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://docs.nestjs.com/",
            "logging": "https://docs.nestjs.com/techniques/logger",
        }


__all__ = ["NestJSPlugin"]
