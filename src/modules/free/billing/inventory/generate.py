#!/usr/bin/env python3
"""Inventory module generator orchestrating vendor runtime and framework variants."""

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
from .overrides import InventoryOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "inventory"
MODULE_CLASS = "InventoryService"
MODULE_TITLE = "Inventory"
MODULE_TIER = "free"
MODULE_CATEGORY = "billing"
MODULE_SLUG = "free/billing/inventory"
MODULE_BASE = "src/modules/free/billing/inventory"
MODULE_IMPORT_BASE = MODULE_BASE.replace("/", ".")

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/inventory.py"
PYTHON_HEALTH_REL = f"{MODULE_BASE}/health/inventory.py"
PYTHON_TYPES_REL = f"{MODULE_BASE}/types/inventory.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/inventory.service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/inventory.controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/inventory.module.ts"
VENDOR_CONFIGURATION_REL = "nestjs/configuration.js"


class GeneratorError(SettingsGeneratorError):
    """Explicit generator failure propagating helpful metadata."""

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


class InventoryModuleGenerator(BaseModuleGenerator):
    """Module generator orchestrating vendor runtime and framework variants."""

    def __init__(self, overrides: InventoryOverrides | None = None) -> None:
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
            self._overrides = InventoryOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> InventoryOverrides:
        if self._overrides is None:
            raise RuntimeError("Inventory overrides not initialised")
        return self._overrides

    def _load_configuration_bundle(self) -> Dict[str, Any]:
        base_config = _load_yaml(MODULE_ROOT / "config" / "base.yaml")
        snippets_config = _load_yaml(MODULE_ROOT / "config" / "snippets.yaml")
        return {
            "defaults": _ensure_mapping(base_config.get("defaults")),
            "pricing": _ensure_mapping(base_config.get("pricing")),
            "warehouses": _ensure_mapping(base_config.get("warehouses")),
            "notifications": _ensure_mapping(base_config.get("notifications")),
            "snippet_catalog": snippets_config.get("snippets", []),
        }

    def build_base_context(self, config: Mapping[str, Any]) -> Dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        version = config.get("version", "0.0.0")
        bundle = self._load_configuration_bundle()

        defaults = {
            "enabled": True,
            "default_currency": "usd",
            "log_level": "INFO",
            "allow_backorders": False,
            "allow_negative_inventory": False,
            "low_stock_threshold": 5,
            "reservation_expiry_minutes": 30,
            "decimal_precision": 2,
            "metadata": {"module": MODULE_NAME},
        }
        defaults.update(_ensure_mapping(bundle.get("defaults")))

        # NestJS templates expect InventoryConfig camelCase keys.
        defaults_ts = {
            "enabled": defaults.get("enabled"),
            "defaultCurrency": (
                str(defaults.get("default_currency"))
                if defaults.get("default_currency") is not None
                else None
            ),
            "allowBackorders": defaults.get("allow_backorders"),
            "allowNegativeInventory": defaults.get("allow_negative_inventory"),
            "lowStockThreshold": defaults.get("low_stock_threshold"),
            "reservationExpiryMinutes": defaults.get("reservation_expiry_minutes"),
            "decimalPrecision": defaults.get("decimal_precision"),
        }

        pricing = {
            "min_price": 0.01,
            "max_price": 250000,
            "tax_inclusive": False,
            "rounding_mode": "half_up",
        }
        pricing.update(_ensure_mapping(bundle.get("pricing")))

        warehouses = {
            "primary": {
                "code": "primary",
                "name": "Primary Warehouse",
                "location": "global",
                "allow_backorders": False,
            }
        }
        if isinstance(bundle.get("warehouses"), Mapping):
            warehouses.update(_ensure_mapping(bundle.get("warehouses")))

        notifications = {
            "enabled": True,
            "channels": ["email", "webhook"],
            "low_stock": {"threshold": 3, "include_reservations": True},
        }
        notifications.update(_ensure_mapping(bundle.get("notifications")))

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
            "rapidkit_vendor_configuration_relative": VENDOR_CONFIGURATION_REL,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_types_relative": PYTHON_TYPES_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "inventory_defaults": defaults,
            "inventory_defaults_ts": defaults_ts,
            "inventory_pricing": pricing,
            "inventory_warehouses": warehouses,
            "inventory_notifications": notifications,
            "inventory_snippet_catalog": bundle.get("snippet_catalog", []),
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

    def generate_vendor_files(
        self,
        config: Mapping[str, Any],
        target_dir: Path,
        renderer: TemplateRenderer,
        context: Mapping[str, Any],
    ) -> None:
        super().generate_vendor_files(config, target_dir, renderer, context)

        vendor_cfg = config.get("generation", {}).get("vendor")
        if not vendor_cfg:
            return

        root = vendor_cfg.get("root", ".rapidkit/vendor")
        module_name = context.get("rapidkit_vendor_module", self.module_identifier)
        version = context.get("rapidkit_vendor_version", config.get("version", "0.0.0"))
        vendor_root = target_dir / root / module_name / version
        self.overrides._ensure_packages(vendor_root)


def _create_generator(overrides: InventoryOverrides | None = None) -> InventoryModuleGenerator:
    return InventoryModuleGenerator(overrides=overrides)


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
    overrides: InventoryOverrides | None = None,
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
            "Usage: python -m modules.free.billing.inventory.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.billing.inventory.generate fastapi ../../examples/inventory\n"
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
    generator = InventoryModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped inventory module version to {config['version']}")
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
            "💡 If this persists, run 'rapidkit modules doctor inventory' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
