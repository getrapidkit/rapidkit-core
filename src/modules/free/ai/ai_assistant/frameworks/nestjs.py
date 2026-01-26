"""NestJS plugin for Ai Assistant module scaffolding."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin

MODULE_BASE = "src/modules/free/ai/ai_assistant"


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
            "service": "templates/variants/nestjs/ai_assistant.service.ts.j2",
            "controller": "templates/variants/nestjs/ai_assistant.controller.ts.j2",
            "module": "templates/variants/nestjs/ai_assistant.module.ts.j2",
            "health": "templates/variants/nestjs/ai_assistant.health.ts.j2",
            "validation": "templates/variants/nestjs/ai_assistant.validation.ts.j2",
            "index": "templates/variants/nestjs/ai_assistant.index.ts.j2",
            "configuration": "templates/variants/nestjs/ai_assistant.configuration.ts.j2",
            "spec": "templates/variants/nestjs/ai_assistant.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": f"{MODULE_BASE}/ai-assistant/ai_assistant.service.ts",
            "controller": f"{MODULE_BASE}/ai-assistant/ai_assistant.controller.ts",
            "module": f"{MODULE_BASE}/ai-assistant/ai_assistant.module.ts",
            "health": f"{MODULE_BASE}/ai-assistant/ai_assistant.health.ts",
            "validation": f"{MODULE_BASE}/ai-assistant/ai_assistant.validation.ts",
            "index": f"{MODULE_BASE}/ai-assistant/index.ts",
            "configuration": f"{MODULE_BASE}/ai-assistant/configuration.ts",
            "spec": "test/ai-assistant/ai_assistant.spec.ts",
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
        (output_dir / "src" / "modules" / "free" / "ai" / "ai_assistant" / "ai-assistant").mkdir(
            parents=True,
            exist_ok=True,
        )
        (output_dir / "test" / "ai-assistant").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:
        _ = output_dir


class NestJSStandardPlugin(NestJSPlugin):
    """Alias plugin to expose nestjs.standard profile."""

    @property
    def name(self) -> str:  # pragma: no cover - simple alias
        return "nestjs.standard"

    @property
    def display_name(self) -> str:  # pragma: no cover - simple alias
        return "NestJS (standard kit)"
