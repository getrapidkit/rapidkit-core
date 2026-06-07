"""NestJS plugin for Vector Store module scaffolding."""

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
            "service": "templates/variants/nestjs/vector_store.service.ts.j2",
            "controller": "templates/variants/nestjs/vector_store.controller.ts.j2",
            "module": "templates/variants/nestjs/vector_store.module.ts.j2",
            "health": "templates/variants/nestjs/vector_store.health.ts.j2",
            "validation": "templates/variants/nestjs/vector_store.validation.ts.j2",
            "index": "templates/variants/nestjs/vector_store.index.ts.j2",
            "configuration": "templates/variants/nestjs/vector_store.configuration.ts.j2",
            "e2e": "templates/variants/nestjs/tests/vector_store.e2e-spec.ts",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/vector-store/vector_store.service.ts",
            "controller": "src/vector-store/vector_store.controller.ts",
            "module": "src/vector-store/vector_store.module.ts",
            "health": "src/vector-store/vector_store.health.ts",
            "validation": "src/vector-store/vector_store.validation.ts",
            "index": "src/vector-store/index.ts",
            "configuration": "src/vector-store/configuration.ts",
            "e2e": "tests/modules/e2e/ai/vector_store/vector_store.e2e-spec.ts",
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
