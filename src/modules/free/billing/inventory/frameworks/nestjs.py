"""NestJS framework plugin for the Inventory module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin

MODULE_BASE = "src/modules/free/billing/inventory"


class NestJSPlugin(FrameworkPlugin):
    """Generate NestJS bindings for the Inventory runtime."""

    @property
    def name(self) -> str:  # noqa: D401 - short alias
        return "nestjs"

    @property
    def language(self) -> str:  # noqa: D401 - short alias
        return "typescript"

    @property
    def display_name(self) -> str:  # noqa: D401 - short alias
        return "NestJS"

    def get_template_mappings(self) -> Dict[str, str]:
        return {
            "service": "templates/variants/nestjs/inventory.service.ts.j2",
            "controller": "templates/variants/nestjs/inventory.controller.ts.j2",
            "module": "templates/variants/nestjs/inventory.module.ts.j2",
            "configuration": "templates/variants/nestjs/inventory.configuration.ts.j2",
            "health": "templates/variants/nestjs/inventory.health.ts.j2",
            "routes": "templates/variants/nestjs/inventory.routes.ts.j2",
            "tests": "templates/variants/nestjs/inventory.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": f"{MODULE_BASE}/inventory.service.ts",
            "controller": f"{MODULE_BASE}/inventory.controller.ts",
            "module": f"{MODULE_BASE}/inventory.module.ts",
            "configuration": f"{MODULE_BASE}/inventory.configuration.ts",
            "health": f"{MODULE_BASE}/inventory.health.ts",
            "routes": f"{MODULE_BASE}/inventory.routes.ts",
            "tests": "test/inventory/inventory.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        (output_dir / "src" / "modules" / "free" / "billing" / "inventory").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "nestjs").mkdir(parents=True, exist_ok=True)
        (output_dir / "test" / "inventory").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "nestjs": "https://docs.nestjs.com/",
            "rapidkit": "https://docs.rapidkit.top/modules/billing/inventory",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {"inventory": {"warehouses": {"primary": {"code": "primary", "name": "Primary"}}}}

    def get_dependencies(self) -> List[str]:
        return ["@nestjs/common>=10.0.0"]

    def get_dev_dependencies(self) -> List[str]:
        return ["jest>=29.0.0"]


__all__ = ["NestJSPlugin"]
