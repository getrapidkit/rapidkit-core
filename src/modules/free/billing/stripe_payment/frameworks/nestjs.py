"""NestJS framework plugin for the Stripe Payment module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin

MODULE_BASE = "src/modules/free/billing/stripe_payment"


class NestJSPlugin(FrameworkPlugin):
    """Generate NestJS bindings for the Stripe Payment runtime."""

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
            "service": "templates/variants/nestjs/stripe_payment.service.ts.j2",
            "controller": "templates/variants/nestjs/stripe_payment.controller.ts.j2",
            "module": "templates/variants/nestjs/stripe_payment.module.ts.j2",
            "health": "templates/variants/nestjs/stripe_payment.health.ts.j2",
            "routes": "templates/variants/nestjs/stripe_payment.routes.ts.j2",
            "configuration_ts": "templates/variants/nestjs/stripe_payment.configuration.ts.j2",
            "configuration": "templates/vendor/nestjs/configuration.js.j2",
            "integration_test": "templates/variants/nestjs/__tests__/stripe_payment.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": f"{MODULE_BASE}/stripe-payment.service.ts",
            "controller": f"{MODULE_BASE}/stripe-payment.controller.ts",
            "module": f"{MODULE_BASE}/stripe-payment.module.ts",
            "health": f"{MODULE_BASE}/stripe-payment.health.ts",
            "routes": f"{MODULE_BASE}/stripe-payment.routes.ts",
            "configuration_ts": f"{MODULE_BASE}/stripe-payment.configuration.ts",
            "configuration": "nestjs/configuration.js",
            "integration_test": "tests/modules/integration/billing/stripe-payment.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        stripe_dir = output_dir / "src" / "modules" / "free" / "billing" / "stripe_payment"
        stripe_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "billing").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "nestjs").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "nestjs": "https://docs.nestjs.com/",
            "stripe": "https://stripe.com/docs/payments",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "stripe_payment": {
                "providers": ["StripePaymentService"],
                "controllers": ["StripePaymentController"],
            }
        }

    def get_dependencies(self) -> List[str]:
        return [
            "@nestjs/common@^10.0.0",
            "@nestjs/core@^10.0.0",
            "@nestjs/config@^3.0.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "@nestjs/testing@^10.0.0",
            "@types/jest@^29.0.0",
            "@types/node@^20.0.0",
            "jest@^29.0.0",
            "ts-jest@^29.0.0",
            "typescript@^5.0.0",
        ]


__all__ = ["NestJSPlugin"]
