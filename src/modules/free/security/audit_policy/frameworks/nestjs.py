"""NestJS plugin for Audit Policy module scaffolding."""

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
            "service": "templates/variants/nestjs/audit_policy.service.ts.j2",
            "controller": "templates/variants/nestjs/audit_policy.controller.ts.j2",
            "module": "templates/variants/nestjs/audit_policy.module.ts.j2",
            "health": "templates/variants/nestjs/audit_policy.health.ts.j2",
            "validation": "templates/variants/nestjs/audit_policy.validation.ts.j2",
            "index": "templates/variants/nestjs/audit_policy.index.ts.j2",
            "configuration": "templates/variants/nestjs/audit_policy.configuration.ts.j2",
            "e2e": "templates/variants/nestjs/tests/audit_policy.e2e-spec.ts",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/audit-policy/audit_policy.service.ts",
            "controller": "src/audit-policy/audit_policy.controller.ts",
            "module": "src/audit-policy/audit_policy.module.ts",
            "health": "src/audit-policy/audit_policy.health.ts",
            "validation": "src/audit-policy/audit_policy.validation.ts",
            "index": "src/audit-policy/index.ts",
            "configuration": "src/audit-policy/configuration.ts",
            "e2e": "tests/modules/e2e/security/audit_policy/audit_policy.e2e-spec.ts",
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
