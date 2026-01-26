#!/usr/bin/env python3
"""Stripe Payment module generator orchestrating vendor runtime and framework variants."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional

import yaml

from modules.shared.exceptions import SettingsGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

from .frameworks import get_plugin, list_available_plugins
from .overrides import StripePaymentOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "stripe_payment"
MODULE_CLASS = "StripePayment"
MODULE_TITLE = "Stripe Payment"
MODULE_TIER = "free"
MODULE_CATEGORY = "billing"
MODULE_SLUG = "free/billing/stripe_payment"
MODULE_BASE = "src/modules/free/billing/stripe_payment"
MODULE_IMPORT_BASE = MODULE_BASE.replace("/", ".")

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/stripe_payment.py"
PYTHON_HEALTH_REL = f"{MODULE_BASE}/health/stripe_payment.py"
PYTHON_TYPES_REL = f"{MODULE_BASE}/types/stripe_payment.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/stripe-payment.service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/stripe-payment.controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/stripe-payment.module.ts"


class GeneratorError(SettingsGeneratorError):
    """Explicit generator failure carrying guidance for maintainers."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: int = 1,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        error_context = context or {}
        error_context["exit_code"] = exit_code
        super().__init__(message, context=error_context)
        self.exit_code = exit_code


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, Mapping):
        return {}
    return dict(data)


def _ensure_mapping(payload: Mapping[str, Any] | None) -> Dict[str, Any]:
    if isinstance(payload, Mapping):
        return dict(payload)
    return {}


class StripePaymentModuleGenerator(BaseModuleGenerator):
    """Module generator orchestrating vendor runtime and framework variants."""

    def __init__(self, overrides: StripePaymentOverrides | None = None) -> None:
        self._overrides = overrides
        super().__init__(
            module_root=MODULE_ROOT,
            templates_root=MODULE_ROOT,
            project_root=PROJECT_ROOT,
            module_identifier=MODULE_NAME,
            get_plugin=get_plugin,
            list_plugins=list_available_plugins,
            error_cls=GeneratorError,
        )
        if self._overrides is None:
            self._overrides = StripePaymentOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> StripePaymentOverrides:
        if self._overrides is None:
            raise RuntimeError("StripePayment overrides not initialised")
        return self._overrides

    def _load_configuration_bundle(self) -> Dict[str, Any]:
        base_config = _load_yaml(MODULE_ROOT / "config" / "base.yaml")
        snippets_config = _load_yaml(MODULE_ROOT / "config" / "snippets.yaml")
        return {
            "defaults": _ensure_mapping(base_config.get("defaults")),
            "retry_policy": _ensure_mapping(base_config.get("retry_policy")),
            "webhook": _ensure_mapping(base_config.get("webhook")),
            "features": _ensure_mapping(base_config.get("features")),
            "billing": _ensure_mapping(base_config.get("billing")),
            "network": _ensure_mapping(base_config.get("network")),
            "metadata_keys": _ensure_mapping(base_config.get("metadata_keys")),
            "snippet_catalog": snippets_config.get("snippets", []),
        }

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        version = config.get("version", "0.0.0")
        bundle = self._load_configuration_bundle()

        defaults = {
            "enabled": True,
            "mode": "test",
            "default_currency": "usd",
            "capture_method": "automatic",
            "statement_descriptor": "RapidKit",
            "description_prefix": "RapidKit",
            "automatic_payment_methods": True,
            "metadata": {},
        }
        defaults.update(_ensure_mapping(bundle.get("defaults")))

        retry_policy = {
            "max_attempts": 3,
            "base_delay_seconds": 2.0,
            "max_delay_seconds": 30.0,
        }
        retry_policy.update(_ensure_mapping(bundle.get("retry_policy")))

        webhook = {
            "enabled": True,
            "endpoint_secret_env": "RAPIDKIT_STRIPE_WEBHOOK_SECRET",
            "tolerance_seconds": 300,
            "events": [
                "payment_intent.succeeded",
                "payment_intent.payment_failed",
            ],
        }
        webhook_defaults = _ensure_mapping(bundle.get("webhook"))
        webhook.update({k: v for k, v in webhook_defaults.items() if v is not None})

        features = {
            "allow_manual_capture": True,
            "enable_idempotency_keys": True,
            "verify_webhooks": True,
            "emit_metrics": True,
        }
        features.update(_ensure_mapping(bundle.get("features")))

        billing = {
            "minimum_amount": 50,
            "maximum_amount": 5_000_000,
            "allowed_currencies": ["usd", "eur", "gbp"],
            "default_payment_method_types": ["card"],
        }
        billing_bundle = _ensure_mapping(bundle.get("billing"))
        billing.update({k: v for k, v in billing_bundle.items() if v is not None})

        network = {
            "timeout_seconds": 10.0,
            "max_connections": 4,
        }
        network.update(_ensure_mapping(bundle.get("network")))

        metadata_keys = {
            "customer_id": "customer_id",
            "tenant_id": "tenant_id",
            "order_id": "order_id",
        }
        metadata_keys.update(_ensure_mapping(bundle.get("metadata_keys")))

        return {
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "module_category": MODULE_CATEGORY,
            "module_import_base": MODULE_IMPORT_BASE,
            "module_kebab": module_name.replace("_", "-"),
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": version,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_types_relative": PYTHON_TYPES_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "stripe_defaults": defaults,
            "stripe_retry_policy": retry_policy,
            "stripe_webhook": webhook,
            "stripe_features": features,
            "stripe_billing": billing,
            "stripe_network": network,
            "stripe_metadata_keys": metadata_keys,
            "stripe_snippet_catalog": bundle.get("snippet_catalog", []),
            "stripe_env_overrides": {"api_key": None, "webhook_secret": None},
        }

    def apply_base_context_overrides(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return self.overrides.apply_base_context(context)

    def apply_variant_context_pre(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context_pre(context, variant_name=variant_name)

    def apply_variant_context_post(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context_post(context, variant_name=variant_name)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:
        self.overrides.post_variant_generation(
            variant_name=variant_name,
            target_dir=target_dir,
            enriched_context=enriched_context,
        )


def _create_generator(
    overrides: StripePaymentOverrides | None = None,
) -> StripePaymentModuleGenerator:
    return StripePaymentModuleGenerator(overrides=overrides)


def load_module_config() -> Dict[str, Any]:
    return dict(_create_generator().load_module_config())


def build_base_context(config: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(_create_generator().build_base_context(config))


def generate_vendor_files(
    config: Mapping[str, Any],
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
) -> None:
    _create_generator().generate_vendor_files(config, target_dir, renderer, context)


def generate_variant_files(
    variant_name: str,
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
    overrides: StripePaymentOverrides | None = None,
) -> None:
    _create_generator(overrides=overrides).generate_variant_files(
        variant_name, target_dir, renderer, context
    )


def main() -> None:
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = list(available_plugins.keys())
        guidance = (
            "Usage: python -m modules.free.billing.stripe_payment.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.billing.stripe_payment.generate fastapi ../../examples/stripe-payment\n"
            f"Available frameworks: {', '.join(available_names)}"
        )
        raise GeneratorError(
            guidance,
            exit_code=2,
            context={
                "provided_args": sys.argv[1:],
                "expected_arg_count": expected_arg_count - 1,
            },
        )

    variant_name = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve()

    missing_optional_dependencies: Dict[str, str] = {}
    generator = StripePaymentModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped stripe payment module version to {config['version']}")
        renderer = generator.create_renderer()

        generator.generate_vendor_files(config, target_dir, renderer, base_context)
        generator.generate_variant_files(variant_name, target_dir, renderer, base_context)
    except GeneratorError as exc:
        print(f"❌ Generator Error: {exc.message}")
        if exc.context:
            print("Context:")
            for key, value in exc.context.items():
                print(f"  {key}: {value}")
        dep_hint = format_missing_dependencies(missing_optional_dependencies)
        if dep_hint:
            print(f"\n{dep_hint}")
        sys.exit(exc.exit_code)
    except (RuntimeError, OSError, yaml.YAMLError) as exc:
        print("❌ Generator failed with an unexpected error:")
        traceback = "\n".join(TracebackException.from_exception(exc).format())
        print(traceback)
        print(
            "💡 If this persists, run 'rapidkit modules doctor stripe-payment' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
