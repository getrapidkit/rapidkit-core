#!/usr/bin/env python3
"""Cart module generator orchestrating vendor runtime and framework variants."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping

import yaml

from modules.shared.exceptions import SettingsGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

from .frameworks import get_plugin, list_available_plugins
from .overrides import CartOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "cart"
MODULE_CLASS = "CartService"
MODULE_TITLE = "Cart"
MODULE_TIER = "free"
MODULE_SLUG = "free/billing/cart"
MODULE_CATEGORY = "billing"
MODULE_BASE = "src/modules/free/billing/cart"
MODULE_IMPORT_BASE = MODULE_BASE.replace("/", ".")

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/cart.py"
PYTHON_HEALTH_REL = f"{MODULE_BASE}/health/cart.py"
PYTHON_TYPES_REL = f"{MODULE_BASE}/types/cart.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/cart.service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/cart.controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/cart.module.ts"
VENDOR_CONFIGURATION_REL = "nestjs/configuration.js"


class GeneratorError(SettingsGeneratorError):
    """Explicit generator failure carrying guidance for maintainers."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: int = 1,
        context: Dict[str, Any] | None = None,
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
    if not isinstance(data, dict):
        return {}
    return dict(data)


def _extract_defaults(config: Mapping[str, Any]) -> Dict[str, Any]:
    defaults = config.get("defaults")
    if isinstance(defaults, Mapping):
        return dict(defaults)
    return {}


def _extract_discount_rules(config: Mapping[str, Any]) -> list[Dict[str, Any]]:
    rules = config.get("discount_rules")
    if isinstance(rules, list):
        return [dict(rule) for rule in rules if isinstance(rule, Mapping)]
    return []


def _extract_health_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    health = config.get("health")
    if isinstance(health, Mapping):
        return dict(health)
    return {}


class CartModuleGenerator(BaseModuleGenerator):
    """Module generator orchestrating vendor runtime and framework variants."""

    def __init__(self, overrides: CartOverrides | None = None) -> None:
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
            self._overrides = CartOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> CartOverrides:
        if self._overrides is None:
            raise RuntimeError("Cart overrides not initialised")
        return self._overrides

    def _load_configuration_bundle(self) -> Dict[str, Any]:
        base_config = _load_yaml(MODULE_ROOT / "config" / "base.yaml")
        snippets_config = _load_yaml(MODULE_ROOT / "config" / "snippets.yaml")
        return {
            "defaults": _extract_defaults(base_config),
            "discount_rules": _extract_discount_rules(base_config),
            "health": _extract_health_config(base_config),
            "snippet_catalog": snippets_config.get("snippets", []),
        }

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        version = config.get("version", "0.0.0")
        bundle = self._load_configuration_bundle()

        defaults = {
            "currency": "USD",
            "tax_rate": "0.00",
            "apply_tax_before_discounts": False,
            "default_discount_code": None,
            "auto_apply_default_discount": False,
            "max_unique_items": 100,
            "metadata": {},
        }
        defaults.update(bundle.get("defaults", {}))

        base_context = {
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "module_kebab": module_name.replace("_", "-"),
            "module_category": MODULE_CATEGORY,
            "module_import_base": MODULE_IMPORT_BASE,
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": version,
            "rapidkit_vendor_configuration_relative": VENDOR_CONFIGURATION_REL,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_types_relative": PYTHON_TYPES_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "cart_defaults": defaults,
            "cart_discount_rules": bundle.get("discount_rules", []),
            "cart_health_config": bundle.get("health", {}),
            "cart_snippet_catalog": bundle.get("snippet_catalog", []),
        }
        return base_context

    def apply_base_context_overrides(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return self.overrides.apply_base_context(context)

    def apply_variant_context_pre(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context_pre(context, variant_name=variant_name)

    def apply_variant_context_post(
        self, context: Mapping[str, Any], *, variant_name: str
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


def _create_generator(overrides: CartOverrides | None = None) -> CartModuleGenerator:
    return CartModuleGenerator(overrides=overrides)


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
    overrides: CartOverrides | None = None,
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
            "Usage: python -m modules.free.billing.cart.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.billing.cart.generate fastapi ../../examples/cart\n"
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
    generator = CartModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped cart module version to {config['version']}")
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
        print("💡 If this persists, run 'rapidkit modules doctor cart' or reinstall dependencies.")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
