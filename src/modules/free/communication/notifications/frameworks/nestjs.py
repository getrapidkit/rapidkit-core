# pyright: reportMissingImports=false
"""NestJS framework plugin for the Notifications module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)

VENDOR_CONFIG_TEMPLATE = "templates/vendor/nestjs/configuration.js.j2"
VENDOR_CONFIG_OUTPUT = "nestjs/notifications.config.js"


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS notifications integrations."""

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
            "config": VENDOR_CONFIG_TEMPLATE,
            "service": "templates/variants/nestjs/notifications.service.ts.j2",
            "controller": "templates/variants/nestjs/notifications.controller.ts.j2",
            "module": "templates/variants/nestjs/notifications.module.ts.j2",
            "configuration": "templates/variants/nestjs/notifications.configuration.ts.j2",
            "health": "templates/variants/nestjs/notifications.health.ts.j2",
            "integration_test": "templates/tests/integration/notifications.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "config": VENDOR_CONFIG_OUTPUT,
            "service": "src/modules/free/communication/notifications/notifications.service.ts",
            "controller": "src/modules/free/communication/notifications/notifications.controller.ts",
            "module": "src/modules/free/communication/notifications/notifications.module.ts",
            "configuration": "src/modules/free/communication/notifications/notifications.configuration.ts",
            "health": "src/health/notifications.health.ts",
            "integration_test": "tests/modules/integration/communication/notifications.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "module_class_name": "Notifications",
            "module_kebab": "notifications",
            "notification_types": ["email", "push", "sms"],
            "template_support": True,
            "delivery_providers": ["smtp", "sendgrid", "ses"],
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        (output_dir / "src" / "modules" / "free" / "communication" / "notifications").mkdir(
            parents=True,
            exist_ok=True,
        )
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "communication").mkdir(
            parents=True,
            exist_ok=True,
        )
        (output_dir / "nestjs").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://nestjs.com/",
            "notifications_docs": "https://docs.nestjs.com/techniques/events",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {}

    def get_dependencies(self) -> List[str]:
        return [
            "@nestjs/common",
            "@nestjs/core",
            "@nestjs/config",
            "nodemailer",
            "handlebars",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "@types/node",
            "@types/nodemailer",
            "@types/handlebars",
        ]
