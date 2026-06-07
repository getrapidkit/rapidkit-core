"""NestJS plugin for Tool Registry module scaffolding."""

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
            "service": "templates/variants/nestjs/tool_registry.service.ts.j2",
            "controller": "templates/variants/nestjs/tool_registry.controller.ts.j2",
            "module": "templates/variants/nestjs/tool_registry.module.ts.j2",
            "health": "templates/variants/nestjs/tool_registry.health.ts.j2",
            "validation": "templates/variants/nestjs/tool_registry.validation.ts.j2",
            "index": "templates/variants/nestjs/tool_registry.index.ts.j2",
            "configuration": "templates/variants/nestjs/tool_registry.configuration.ts.j2",
            "e2e": "templates/variants/nestjs/tests/tool_registry.e2e-spec.ts",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/tool-registry/tool_registry.service.ts",
            "controller": "src/tool-registry/tool_registry.controller.ts",
            "module": "src/tool-registry/tool_registry.module.ts",
            "health": "src/tool-registry/tool_registry.health.ts",
            "validation": "src/tool-registry/tool_registry.validation.ts",
            "index": "src/tool-registry/index.ts",
            "configuration": "src/tool-registry/configuration.ts",
            "e2e": "tests/modules/e2e/ai/tool_registry/tool_registry.e2e-spec.ts",
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
