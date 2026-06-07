"""NestJS plugin for Queue Platform module scaffolding."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Provide NestJS-specific template and output mappings."""

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
            "service": "templates/variants/nestjs/queue_platform.service.ts.j2",
            "controller": "templates/variants/nestjs/queue_platform.controller.ts.j2",
            "module": "templates/variants/nestjs/queue_platform.module.ts.j2",
            "health": "templates/variants/nestjs/queue_platform.health.ts.j2",
            "validation": "templates/variants/nestjs/queue_platform.validation.ts.j2",
            "index": "templates/variants/nestjs/queue_platform.index.ts.j2",
            "configuration": "templates/variants/nestjs/queue_platform.configuration.ts.j2",
            "e2e": "templates/variants/nestjs/tests/queue_platform.e2e-spec.ts",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/queue-platform/queue_platform.service.ts",
            "controller": "src/queue-platform/queue_platform.controller.ts",
            "module": "src/queue-platform/queue_platform.module.ts",
            "health": "src/queue-platform/queue_platform.health.ts",
            "validation": "src/queue-platform/queue_platform.validation.ts",
            "index": "src/queue-platform/index.ts",
            "configuration": "src/queue-platform/configuration.ts",
            "e2e": "tests/modules/e2e/tasks/queue_platform/queue_platform.e2e-spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        enriched = dict(base_context)
        enriched.update(
            {
                "framework": "nestjs",
                "framework_display_name": "NestJS",
                "language": "typescript",
            }
        )
        return enriched

    def validate_requirements(self) -> List[str]:
        return []

    def get_dependencies(self) -> List[str]:
        return ["@nestjs/common>=10.0.0"]

    def get_dev_dependencies(self) -> List[str]:
        return ["@nestjs/testing>=10.0.0", "ts-jest>=29.0.0"]

    def pre_generation_hook(self, output_dir: Path) -> None:
        (output_dir / "src").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:
        _ = output_dir
