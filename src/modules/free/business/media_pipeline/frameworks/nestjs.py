"""NestJS plugin for Media Pipeline module scaffolding."""

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
            "service": "templates/variants/nestjs/media_pipeline.service.ts.j2",
            "controller": "templates/variants/nestjs/media_pipeline.controller.ts.j2",
            "module": "templates/variants/nestjs/media_pipeline.module.ts.j2",
            "health": "templates/variants/nestjs/media_pipeline.health.ts.j2",
            "validation": "templates/variants/nestjs/media_pipeline.validation.ts.j2",
            "index": "templates/variants/nestjs/media_pipeline.index.ts.j2",
            "configuration": "templates/variants/nestjs/media_pipeline.configuration.ts.j2",
            "e2e": "templates/variants/nestjs/tests/media_pipeline.e2e-spec.ts",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/media-pipeline/media_pipeline.service.ts",
            "controller": "src/media-pipeline/media_pipeline.controller.ts",
            "module": "src/media-pipeline/media_pipeline.module.ts",
            "health": "src/media-pipeline/media_pipeline.health.ts",
            "validation": "src/media-pipeline/media_pipeline.validation.ts",
            "index": "src/media-pipeline/index.ts",
            "configuration": "src/media-pipeline/configuration.ts",
            "e2e": "tests/modules/e2e/business/media_pipeline/media_pipeline.e2e-spec.ts",
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
