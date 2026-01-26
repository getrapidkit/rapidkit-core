#!/usr/bin/env python3
"""Unified module generator for Security Headers."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional

import yaml

from modules.shared.exceptions import ModuleGeneratorError
from modules.shared.generator import (
    FileSystemLoader as _FileSystemLoader,
    JinjaEnvironment as _JinjaEnvironment,
    StrictUndefined as _StrictUndefined,
    TemplateRenderer as _BaseTemplateRenderer,
    format_missing_dependencies,
    select_autoescape as _select_autoescape,
)
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

from .frameworks import get_plugin, list_available_plugins
from .overrides import SecurityHeadersOverrides

JinjaEnvironment = _JinjaEnvironment
FileSystemLoader = _FileSystemLoader
StrictUndefined = _StrictUndefined
select_autoescape = _select_autoescape


class TemplateRenderer(_BaseTemplateRenderer):
    """Adapter around the shared renderer with module-scoped defaults."""

    def __init__(self, template_root: Path | None = None) -> None:
        if JinjaEnvironment is not None and select_autoescape is None:
            raise GeneratorError(
                "The Security Headers module requires jinja2 with select_autoescape support. Install or upgrade via 'pip install --upgrade jinja2'."
            )
        super().__init__(template_root or MODULE_ROOT)
        # Preserve legacy attribute expected by tests.
        self._env = self.jinja_env

    def render(self, template_path: Path, context: Mapping[str, Any]) -> str:
        if self._env is None:
            raise GeneratorError(
                "The Security Headers module requires jinja2 for template rendering. Install it via 'pip install jinja2'."
            )
        return super().render(template_path, context)


MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "security_headers"
MODULE_CLASS = "SecurityHeaders"
MODULE_TITLE = "Security Headers"
MODULE_TIER = "free"
MODULE_CATEGORY = "security"
MODULE_CATEGORY_DISPLAY = "security"
MODULE_IMPORT_PATH = "modules.free.security.security_headers"

PYTHON_RUNTIME_REL = "src/modules/free/security/security_headers/security_headers.py"
PYTHON_HEALTH_REL = "src/health/security_headers.py"
PYTHON_ROUTES_REL = "src/modules/free/security/security_headers/routers/security_headers.py"
PYTHON_TYPES_REL = "src/modules/free/security/security_headers/types/security_headers.py"
FASTAPI_TEST_REL = "tests/modules/integration/security/test_security_headers_integration.py"
FASTAPI_CONFIG_REL = "config/security/security_headers.yaml"

NEST_SERVICE_REL = (
    "src/modules/free/security/security_headers/security-headers/security-headers.service.ts"
)
NEST_CONTROLLER_REL = (
    "src/modules/free/security/security_headers/security-headers/security-headers.controller.ts"
)
NEST_MODULE_REL = (
    "src/modules/free/security/security_headers/security-headers/security-headers.module.ts"
)
NEST_CONFIGURATION_REL = (
    "src/modules/free/security/security_headers/security-headers/security-headers.configuration.ts"
)
NEST_HEALTH_CONTROLLER_REL = "src/health/security-headers-health.controller.ts"
NEST_HEALTH_MODULE_REL = "src/health/security-headers-health.module.ts"
NEST_TEST_REL = "tests/modules/integration/security/security_headers.integration.spec.ts"
NEST_VENDOR_CONFIGURATION_RELATIVE = "nestjs/configuration.js"

DEFAULTS_KEY = "security_headers_defaults"

FALLBACK_DEFAULTS: Dict[str, Any] = {
    "enabled": True,
    "strict_transport_security": {
        "enabled": True,
        "max_age": 63_072_000,
        "include_subdomains": True,
        "preload": True,
    },
    "content_security_policy": None,
    "content_security_policy_report_only": False,
    "referrer_policy": "strict-origin-when-cross-origin",
    "x_content_type_options": "nosniff",
    "x_frame_options": "DENY",
    "x_xss_protection": False,
    "cross_origin_embedder_policy": "require-corp",
    "cross_origin_opener_policy": "same-origin",
    "cross_origin_resource_policy": "same-origin",
    "permissions_policy": {},
    "expect_ct": None,
    "x_dns_prefetch_control": "off",
    "x_download_options": "noopen",
    "additional_headers": {},
}


class GeneratorError(ModuleGeneratorError):
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
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:  # pragma: no cover - defensive logging handled upstream
        raise GeneratorError(f"Failed to parse YAML configuration at {path}") from exc
    if not isinstance(data, Mapping):
        return {}
    return dict(data)


def _load_defaults_bundle() -> Dict[str, Any]:
    bundle = _load_yaml(MODULE_ROOT / "config" / "base.yaml")
    defaults = bundle.get("defaults") if isinstance(bundle, Mapping) else {}
    if isinstance(defaults, Mapping):
        return dict(defaults)
    return {}


def _as_bool(value: Any, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return fallback


def _as_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _as_str(value: Any, fallback: str | None = None) -> str | None:
    if value is None:
        return fallback
    cleaned = str(value).strip()
    return cleaned or fallback


def _normalize_x_content_type_options(value: Any, fallback: str | bool) -> str | bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return fallback
        lowered = cleaned.lower()
        if lowered in {"0", "false", "no", "off", "disabled"}:
            return False
        if lowered in {"1", "true", "yes", "on", "enabled"}:
            return fallback if isinstance(fallback, str) else "nosniff"
        return cleaned
    return fallback


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): value[key] for key in value}
    return {}


def _merge_defaults(module_config: Mapping[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = dict(FALLBACK_DEFAULTS)
    bundle_defaults = _load_defaults_bundle()

    defaults_candidate = module_config.get("defaults")
    config_defaults: Dict[str, Any]
    if isinstance(defaults_candidate, Mapping):
        config_defaults = {str(key): defaults_candidate[key] for key in defaults_candidate}
    else:
        config_defaults = {}

    merged.update(config_defaults)
    merged.update(bundle_defaults)

    strict_defaults = dict(merged.get("strict_transport_security", {}))
    strict_bundle = _coerce_mapping(bundle_defaults.get("strict_transport_security"))
    if strict_bundle:
        strict_defaults.update(strict_bundle)
    merged["strict_transport_security"] = {
        "enabled": _as_bool(strict_defaults.get("enabled"), True),
        "max_age": _as_int(strict_defaults.get("max_age"), 63_072_000),
        "include_subdomains": _as_bool(strict_defaults.get("include_subdomains"), True),
        "preload": _as_bool(strict_defaults.get("preload"), True),
    }

    merged["content_security_policy"] = _as_str(
        bundle_defaults.get("content_security_policy"),
        merged.get("content_security_policy"),
    )
    merged["content_security_policy_report_only"] = _as_bool(
        bundle_defaults.get("content_security_policy_report_only"),
        bool(merged.get("content_security_policy_report_only", False)),
    )
    merged["referrer_policy"] = (
        _as_str(
            bundle_defaults.get("referrer_policy"),
            merged.get("referrer_policy"),
        )
        or "strict-origin-when-cross-origin"
    )
    merged["x_content_type_options"] = _normalize_x_content_type_options(
        bundle_defaults.get("x_content_type_options", merged.get("x_content_type_options")),
        merged.get("x_content_type_options", "nosniff"),
    )
    merged["x_frame_options"] = (
        _as_str(
            bundle_defaults.get("x_frame_options"),
            merged.get("x_frame_options"),
        )
        or "DENY"
    )
    merged["x_xss_protection"] = _as_bool(
        bundle_defaults.get("x_xss_protection"), bool(merged.get("x_xss_protection", False))
    )
    merged["cross_origin_embedder_policy"] = _as_str(
        bundle_defaults.get("cross_origin_embedder_policy"),
        merged.get("cross_origin_embedder_policy"),
    )
    merged["cross_origin_opener_policy"] = _as_str(
        bundle_defaults.get("cross_origin_opener_policy"),
        merged.get("cross_origin_opener_policy"),
    )
    merged["cross_origin_resource_policy"] = _as_str(
        bundle_defaults.get("cross_origin_resource_policy"),
        merged.get("cross_origin_resource_policy"),
    )
    merged["permissions_policy"] = _coerce_mapping(bundle_defaults.get("permissions_policy"))
    merged["expect_ct"] = _as_str(bundle_defaults.get("expect_ct"), merged.get("expect_ct"))
    merged["x_dns_prefetch_control"] = _as_str(
        bundle_defaults.get("x_dns_prefetch_control"),
        merged.get("x_dns_prefetch_control"),
    )
    merged["x_download_options"] = _as_str(
        bundle_defaults.get("x_download_options"),
        merged.get("x_download_options"),
    )
    merged["additional_headers"] = _coerce_mapping(bundle_defaults.get("additional_headers"))

    return merged


def infer_vendor_settings_path(config: Mapping[str, Any]) -> str:
    vendor_cfg = config.get("generation", {}).get("vendor", {})
    for entry in vendor_cfg.get("files", []):
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if isinstance(relative, str) and template_name.endswith(f"{MODULE_NAME}.py.j2"):
            return relative
    return PYTHON_RUNTIME_REL


class SecurityHeadersModuleGenerator(BaseModuleGenerator):
    """Module generator orchestrating vendor runtime and framework variants."""

    def __init__(self, overrides: SecurityHeadersOverrides | None = None) -> None:
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
            self._overrides = SecurityHeadersOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> SecurityHeadersOverrides:
        if self._overrides is None:  # pragma: no cover - defensive
            self._overrides = SecurityHeadersOverrides(MODULE_ROOT)
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        version = config.get("version", "0.0.0")
        module_kebab = module_name.replace("_", "-")

        defaults = _merge_defaults(config)
        strict_defaults = _coerce_mapping(defaults.get("strict_transport_security"))
        permissions_defaults = _coerce_mapping(defaults.get("permissions_policy"))
        additional_headers_defaults = _coerce_mapping(defaults.get("additional_headers"))

        return {
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_kebab": module_kebab,
            "module_category": MODULE_CATEGORY,
            "module_category_display": MODULE_CATEGORY_DISPLAY,
            "module_import_path": MODULE_IMPORT_PATH,
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": version,
            "rapidkit_vendor_relative_path": infer_vendor_settings_path(config),
            "rapidkit_vendor_configuration_relative": NEST_VENDOR_CONFIGURATION_RELATIVE,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_routes_relative": PYTHON_ROUTES_REL,
            "python_types_relative": PYTHON_TYPES_REL,
            "fastapi_config_relative": FASTAPI_CONFIG_REL,
            "fastapi_integration_test_relative": FASTAPI_TEST_REL,
            "fastapi_test_relative": FASTAPI_TEST_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_configuration_relative": NEST_CONFIGURATION_REL,
            "nest_health_controller_relative": NEST_HEALTH_CONTROLLER_REL,
            "nest_health_module_relative": NEST_HEALTH_MODULE_REL,
            "nest_test_relative": NEST_TEST_REL,
            DEFAULTS_KEY: defaults,
            "enabled_by_default": bool(defaults.get("enabled", True)),
            "strict_transport_security_defaults": strict_defaults,
            "permissions_policy_defaults": permissions_defaults,
            "additional_headers_defaults": additional_headers_defaults,
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
    overrides: SecurityHeadersOverrides | None = None,
) -> SecurityHeadersModuleGenerator:
    return SecurityHeadersModuleGenerator(overrides=overrides)


def load_module_config() -> Dict[str, Any]:
    return dict(_create_generator().load_module_config())


def build_base_context(config: Mapping[str, Any]) -> Dict[str, Any]:
    generator = _create_generator()
    context = generator.build_base_context(config)
    return generator.apply_base_context_overrides(context)


def generate_vendor_files(
    config: Mapping[str, Any],
    target_dir: Path,
    renderer: _BaseTemplateRenderer,
    context: Mapping[str, Any],
) -> None:
    _create_generator().generate_vendor_files(config, target_dir, renderer, context)


def generate_variant_files(
    config: Mapping[str, Any],
    variant_name: str,
    target_dir: Path,
    renderer: _BaseTemplateRenderer,
    context: Mapping[str, Any],
    overrides: SecurityHeadersOverrides | None = None,
) -> None:
    variant_cfg: Mapping[str, Any] | None = None
    if isinstance(config, Mapping):
        generation = config.get("generation", {})
        if isinstance(generation, Mapping):
            variants = generation.get("variants", {})
            if isinstance(variants, Mapping):
                candidate_cfg = variants.get(variant_name)
                if isinstance(candidate_cfg, Mapping):
                    variant_cfg = candidate_cfg

    if variant_cfg is not None:
        for entry in variant_cfg.get("files", []):
            template_ref = entry.get("template") if isinstance(entry, Mapping) else None
            if not template_ref:
                continue
            candidate = MODULE_ROOT / template_ref
            if not candidate.exists():
                raise GeneratorError(
                    f"Variant template '{template_ref}' not found for framework '{variant_name}'.",
                    context={
                        "framework": variant_name,
                        "template_path": str(candidate),
                        "logical_name": entry.get("output") if isinstance(entry, Mapping) else None,
                    },
                )

    _create_generator(overrides=overrides).generate_variant_files(
        variant_name,
        target_dir,
        renderer,
        context,
    )


def main() -> None:
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = ", ".join(sorted(available_plugins.keys())) or "<none>"
        guidance = (
            "Usage: python -m modules.free.security.security_headers.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.security.security_headers.generate fastapi ../../examples/security_headers\n"
            f"Available frameworks: {available_names}"
        )
        raise GeneratorError(
            guidance,
            exit_code=2,
            context={"provided_args": sys.argv[1:], "expected_arg_count": expected_arg_count - 1},
        )

    variant_name = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve()

    missing_optional_dependencies: Dict[str, str] = {}
    if JinjaEnvironment is None or FileSystemLoader is None or StrictUndefined is None:
        missing_optional_dependencies["jinja2"] = (
            "Install to unlock advanced templating (pip install jinja2)"
        )
    elif select_autoescape is None:
        missing_optional_dependencies["jinja2"] = (
            "Upgrade jinja2 to enable select_autoescape (pip install --upgrade jinja2)"
        )

    try:
        generator = _create_generator()
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(
            config,
            module_root=MODULE_ROOT,
        )
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped security_headers module version to {config['version']}")
        renderer = generator.create_renderer()

        generate_vendor_files(config, target_dir, renderer, base_context)
        generate_variant_files(
            config,
            variant_name,
            target_dir,
            renderer,
            base_context,
            overrides=generator.overrides,
        )
    except GeneratorError as exc:
        print(f"❌ Generator Error: {exc.message}")
        if exc.context:
            print("Context:")
            for key, value in exc.context.items():
                print(f"  {key}: {value}")
        dep_hint = format_missing_dependencies(missing_optional_dependencies)
        if dep_hint:
            print(f"\n{dep_hint}")
        sys.exit(getattr(exc, "exit_code", 1))
    except (RuntimeError, OSError, yaml.YAMLError) as exc:
        print("❌ Generator failed with an unexpected error:")
        traceback = "\n".join(TracebackException.from_exception(exc).format())
        print(traceback)
        print(
            "💡 If this persists, run 'rapidkit modules doctor security_headers' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
