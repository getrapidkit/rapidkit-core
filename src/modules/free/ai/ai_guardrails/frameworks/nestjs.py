"""NestJS plugin for Ai Guardrails module scaffolding."""

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
            "service": "templates/variants/nestjs/ai_guardrails.service.ts.j2",
            "controller": "templates/variants/nestjs/ai_guardrails.controller.ts.j2",
            "module": "templates/variants/nestjs/ai_guardrails.module.ts.j2",
            "health": "templates/variants/nestjs/ai_guardrails.health.ts.j2",
            "validation": "templates/variants/nestjs/ai_guardrails.validation.ts.j2",
            "index": "templates/variants/nestjs/ai_guardrails.index.ts.j2",
            "configuration": "templates/variants/nestjs/ai_guardrails.configuration.ts.j2",
            "e2e": "templates/variants/nestjs/tests/ai_guardrails.e2e-spec.ts",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/ai-guardrails/ai_guardrails.service.ts",
            "controller": "src/ai-guardrails/ai_guardrails.controller.ts",
            "module": "src/ai-guardrails/ai_guardrails.module.ts",
            "health": "src/ai-guardrails/ai_guardrails.health.ts",
            "validation": "src/ai-guardrails/ai_guardrails.validation.ts",
            "index": "src/ai-guardrails/index.ts",
            "configuration": "src/ai-guardrails/configuration.ts",
            "e2e": "tests/modules/e2e/ai/ai_guardrails/ai_guardrails.e2e-spec.ts",
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
