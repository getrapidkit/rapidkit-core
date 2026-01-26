# pyright: reportMissingImports=false
"""NestJS framework plugin for the Middleware module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS middleware integrations."""

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
            "service": "templates/variants/nestjs/middleware.service.ts.j2",
            "controller": "templates/variants/nestjs/middleware.controller.ts.j2",
            "module": "templates/variants/nestjs/middleware.module.ts.j2",
            "config": "templates/variants/nestjs/middleware.configuration.ts.j2",
            "health": "templates/vendor/nestjs/middleware.health.ts.j2",
            "integration_tests": "templates/tests/integration/middleware.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/essentials/middleware/service.ts",
            "controller": "src/modules/free/essentials/middleware/controller.ts",
            "module": "src/modules/free/essentials/middleware/module.ts",
            "config": "src/modules/free/essentials/middleware/configuration.ts",
            "health": "src/health/middleware.health.ts",
            "integration_tests": "tests/modules/integration/essentials/middleware/middleware.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        context = dict(base_context)
        context.update(
            framework="nestjs",
            framework_display_name="NestJS",
            language="typescript",
            runtime="node",
            module_class_name="Middleware",
        )
        slug_value = str(context.get("module_slug") or context.get("module_name") or "middleware")
        module_segment = slug_value.split("/")[-1]
        context.setdefault("module_kebab", module_segment.replace("_", "-"))
        return context

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "essentials" / "middleware"
        base.mkdir(parents=True, exist_ok=True)
        (output_dir / "nestjs").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "essentials" / "middleware").mkdir(
            parents=True, exist_ok=True
        )

        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, _output_dir: Path) -> None:
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://nestjs.com/",
            "middleware_docs": "https://docs.nestjs.com/middleware",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {}

    def get_dependencies(self) -> List[str]:
        return [
            "@nestjs/common",
            "@nestjs/core",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "@types/node",
        ]


class NestJSStandardPlugin(NestJSPlugin):
    """Alias plugin so nestjs.standard reuses the canonical NestJS implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias reroutes to NestJS plugin
        return "nestjs.standard"

    @property
    def display_name(self) -> str:
        return "NestJS (standard kit)"
