# pyright: reportMissingImports=false
"""NestJS framework plugin for the Session module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS session management integrations."""

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
            "configuration": "templates/variants/nestjs/configuration.ts.j2",
            "service": "templates/variants/nestjs/session.service.ts.j2",
            "module": "templates/variants/nestjs/session.module.ts.j2",
            "controller": "templates/variants/nestjs/session.controller.ts.j2",
            "index": "templates/variants/nestjs/index.ts.j2",
            "validation": "templates/variants/nestjs/validation.ts.j2",
            "health": "templates/variants/nestjs/session.health.ts.j2",
            "routes": "templates/variants/nestjs/session.routes.ts.j2",
            "tests": "templates/variants/nestjs/session.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "configuration": "src/modules/free/auth/session/configuration.ts",
            "service": "src/modules/free/auth/session/session.service.ts",
            "module": "src/modules/free/auth/session/session.module.ts",
            "controller": "src/modules/free/auth/session/session.controller.ts",
            "index": "src/modules/free/auth/session/index.ts",
            "validation": "src/modules/free/auth/session/config/session.validation.ts",
            "health": "src/health/session.health.ts",
            "routes": "src/modules/free/auth/session/session.routes.ts",
            "tests": "test/session/session.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "module_class_name": "Session",
            "module_kebab": "session",
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "session_backends": ["redis", "database", "memory"],
            "secure_cookies": True,
            "csrf_protection": True,
            "session_timeout": 3600,  # 1 hour
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "auth" / "session"
        module_root.mkdir(parents=True, exist_ok=True)
        (module_root / "config").mkdir(parents=True, exist_ok=True)
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "test" / "session").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None
