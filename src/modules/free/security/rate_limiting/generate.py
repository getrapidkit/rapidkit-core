#!/usr/bin/env python3
"""Unified module generator for Rate Limiting."""

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
from .overrides import RateLimitingOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "rate_limiting"
MODULE_TITLE = "Rate Limiting"
MODULE_TIER = "free"
MODULE_SLUG = "free/security/rate_limiting"
MODULE_CLASS = "RateLimiting"

VENDOR_RUNTIME_RELATIVE = "src/modules/free/security/rate_limiting/rate_limiting.py"
NEST_VENDOR_CONFIGURATION_RELATIVE = "nestjs/configuration.js"
FASTAPI_RUNTIME_RELATIVE = "src/modules/free/security/rate_limiting/rate_limiting/__init__.py"
FASTAPI_DEPENDENCIES_RELATIVE = (
    "src/modules/free/security/rate_limiting/rate_limiting/dependencies.py"
)
FASTAPI_ROUTER_RELATIVE = "src/modules/free/security/rate_limiting/rate_limiting/router.py"
FASTAPI_METADATA_RELATIVE = "src/modules/free/security/rate_limiting/rate_limiting/routes.py"
FASTAPI_RUNTIME_RELATIVE = "src/modules/free/security/rate_limiting/__init__.py"
FASTAPI_DEPENDENCIES_RELATIVE = "src/modules/free/security/rate_limiting/dependencies.py"
FASTAPI_ROUTER_RELATIVE = "src/modules/free/security/rate_limiting/router.py"
FASTAPI_METADATA_RELATIVE = "src/modules/free/security/rate_limiting/routes.py"
FASTAPI_HEALTH_RELATIVE = "src/health/rate_limiting.py"
FASTAPI_CONFIG_RELATIVE = "config/security/rate_limiting.yaml"
FASTAPI_TEST_RELATIVE = "tests/modules/integration/security/test_rate_limiting_integration.py"

NEST_MODULE_RELATIVE = "src/modules/free/security/rate_limiting/rate-limiting.module.ts"
NEST_SERVICE_RELATIVE = "src/modules/free/security/rate_limiting/rate-limiting.service.ts"
NEST_GUARD_RELATIVE = "src/modules/free/security/rate_limiting/rate-limiting.guard.ts"
NEST_CONTROLLER_RELATIVE = "src/modules/free/security/rate_limiting/rate-limiting.controller.ts"
NEST_CONFIGURATION_RELATIVE = (
    "src/modules/free/security/rate_limiting/rate-limiting.configuration.ts"
)
NEST_HEALTH_CONTROLLER_RELATIVE = "src/health/rate-limiting-health.controller.ts"
NEST_HEALTH_MODULE_RELATIVE = "src/health/rate-limiting-health.module.ts"
NEST_TEST_RELATIVE = "tests/modules/integration/security/rate_limiting.integration.spec.ts"

FALLBACK_DEFAULTS: Dict[str, Any] = {
    "enabled": True,
    "backend": "memory",
    "redis_url": "",
    "redis_prefix": "rate-limit",
    "trust_forwarded_for": False,
    "forwarded_for_header": "X-Forwarded-For",
    "identity_header": "X-RateLimit-Identity",
    "default_scope": "identity",
    "default_rule_name": "default",
    "default_limit": 120,
    "default_window": 60,
    "default_priority": 100,
    "default_block_seconds": None,
    "headers": {
        "limit": "X-RateLimit-Limit",
        "remaining": "X-RateLimit-Remaining",
        "reset": "X-RateLimit-Reset",
        "retry_after": "Retry-After",
        "rule": "X-RateLimit-Rule",
    },
    "rules": [],
    "metadata": {},
}


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


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _merge_defaults(config: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(FALLBACK_DEFAULTS)
    config_defaults = _coerce_mapping(config.get("defaults"))
    headers = _coerce_mapping(merged["headers"]) | _coerce_mapping(config_defaults.get("headers"))
    rules = config_defaults.get("rules")
    if isinstance(rules, list):
        merged_rules = []
        for rule in rules:
            if isinstance(rule, Mapping):
                merged_rules.append(dict(rule))
        config_defaults = dict(config_defaults)
        config_defaults["rules"] = merged_rules
    merged.update(config_defaults)
    merged["headers"] = headers
    merged.setdefault("rules", [])
    merged.setdefault("metadata", {})
    return merged


class RateLimitingModuleGenerator(BaseModuleGenerator):
    """Module generator bridging vendor artefacts and framework variants."""

    def __init__(self, overrides: RateLimitingOverrides | None = None) -> None:
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
            self._overrides = RateLimitingOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> RateLimitingOverrides:
        if self._overrides is None:  # pragma: no cover - defensive
            raise RuntimeError("Rate limiting overrides not initialised")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        defaults = _merge_defaults(config)
        return {
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": config.get("version", "0.0.0"),
            "rapidkit_vendor_relative_path": VENDOR_RUNTIME_RELATIVE,
            "rapidkit_vendor_configuration_relative": NEST_VENDOR_CONFIGURATION_RELATIVE,
            "python_runtime_relative": FASTAPI_RUNTIME_RELATIVE,
            "python_dependencies_relative": FASTAPI_DEPENDENCIES_RELATIVE,
            "python_router_relative": FASTAPI_ROUTER_RELATIVE,
            "python_metadata_relative": FASTAPI_METADATA_RELATIVE,
            "python_health_relative": FASTAPI_HEALTH_RELATIVE,
            "fastapi_config_relative": FASTAPI_CONFIG_RELATIVE,
            "fastapi_test_relative": FASTAPI_TEST_RELATIVE,
            "nest_module_relative": NEST_MODULE_RELATIVE,
            "nest_service_relative": NEST_SERVICE_RELATIVE,
            "nest_guard_relative": NEST_GUARD_RELATIVE,
            "nest_controller_relative": NEST_CONTROLLER_RELATIVE,
            "nest_configuration_relative": NEST_CONFIGURATION_RELATIVE,
            "nest_health_controller_relative": NEST_HEALTH_CONTROLLER_RELATIVE,
            "nest_health_module_relative": NEST_HEALTH_MODULE_RELATIVE,
            "nest_test_relative": NEST_TEST_RELATIVE,
            "module_name": module_name,
            "module_title": MODULE_TITLE,
            "module_class_name": MODULE_CLASS,
            "module_slug": MODULE_SLUG,
            "module_tier": MODULE_TIER,
            "module_identifier": MODULE_NAME,
            "rate_limiting_defaults": defaults,
            "headers_defaults": defaults.get("headers", {}),
            "default_rules": defaults.get("rules", []),
            "metadata_defaults": defaults.get("metadata", {}),
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
    overrides: RateLimitingOverrides | None = None,
) -> RateLimitingModuleGenerator:
    return RateLimitingModuleGenerator(overrides=overrides)


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
    overrides: RateLimitingOverrides | None = None,
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
            "Usage: python -m modules.free.security.rate_limiting.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.security.rate_limiting.generate fastapi ../../examples/rate_limiting\n"
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

    missing_optional_dependencies: Dict[str, str] = {
        "redis": "Install redis>=5.0.0 to enable Redis-backed rate limiting",
    }

    generator = RateLimitingModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped rate_limiting module version to {config['version']}")
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
            "💡 If this persists, run 'rapidkit modules doctor rate_limiting' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
