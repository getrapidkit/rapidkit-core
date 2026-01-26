#!/usr/bin/env python3
"""Unified module generator for the CORS module."""

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
from .overrides import CorsOverrides

JinjaEnvironment = _JinjaEnvironment
FileSystemLoader = _FileSystemLoader
StrictUndefined = _StrictUndefined
select_autoescape = _select_autoescape


class TemplateRenderer(_BaseTemplateRenderer):
    """Adapter around the shared renderer with module-scoped defaults."""

    def __init__(self, template_root: Path | None = None) -> None:
        if JinjaEnvironment is not None and select_autoescape is None:
            raise GeneratorError(
                "The CORS module requires jinja2 with select_autoescape support. Install or upgrade via 'pip install --upgrade jinja2'."
            )
        super().__init__((template_root or MODULE_ROOT))
        # Expose the Jinja environment under the historic attribute accessed by tests.
        self._env = self.jinja_env

    def render(self, template_path: Path, context: Mapping[str, Any]) -> str:
        if self._env is None:
            raise GeneratorError(
                "The CORS module requires jinja2 for template rendering. Install it via 'pip install jinja2'."
            )
        return super().render(template_path, context)


MODULE_ROOT = Path(__file__).parent


# Intentionally rely on the shared TemplateRenderer implementation provided by the
# module generator utilities to keep rendering behaviour consistent across modules.
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "cors"
MODULE_CLASS = "Cors"
MODULE_TITLE = "CORS"
MODULE_TIER = "free"
MODULE_SLUG = "free/security/cors"

PYTHON_RUNTIME_REL = "src/modules/free/security/cors/cors.py"
PYTHON_HEALTH_REL = "src/health/cors.py"
PYTHON_ROUTES_REL = "src/modules/free/security/cors/routers/cors.py"
PYTHON_CONFIG_REL = "config/security/cors.yaml"
FASTAPI_TEST_REL = "tests/modules/integration/security/test_cors_integration.py"

NEST_SERVICE_REL = "src/modules/free/security/cors/cors.service.ts"
NEST_CONTROLLER_REL = "src/modules/free/security/cors/cors.controller.ts"
NEST_MODULE_REL = "src/modules/free/security/cors/cors.module.ts"
NEST_HEALTH_REL = "src/modules/free/security/cors/cors.health.ts"
NEST_ROUTES_REL = "src/modules/free/security/cors/cors.routes.ts"
NEST_CONFIGURATION_REL = "src/modules/free/security/cors/cors.configuration.ts"
NEST_VENDOR_CONFIGURATION_RELATIVE = "nestjs/configuration.js"

DEFAULTS_KEY = "cors_defaults"

FALLBACK_DEFAULTS: Dict[str, Any] = {
    "enabled": True,
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": [],
    "max_age": 600,
    "log_level": "INFO",
    "metadata": {},
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
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, Mapping):
        return {}
    return dict(data)


def _load_defaults_bundle() -> Dict[str, Any]:
    bundle = _load_yaml(MODULE_ROOT / "config" / "base.yaml")
    defaults = bundle.get("defaults") if isinstance(bundle, Mapping) else {}
    if isinstance(defaults, Mapping):
        return dict(defaults)
    return {}


def _format_missing_dependencies(details: Mapping[str, str]) -> str:
    return format_missing_dependencies(details)


def infer_vendor_settings_path(config: Mapping[str, Any]) -> str:
    vendor_cfg = config.get("generation", {}).get("vendor", {})
    for entry in vendor_cfg.get("files", []):
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if isinstance(relative, str) and template_name.endswith(f"{MODULE_NAME}.py.j2"):
            return relative
    return PYTHON_RUNTIME_REL


class CorsModuleGenerator(BaseModuleGenerator):
    """Module generator orchestrating vendor runtime and framework variants for CORS."""

    def __init__(self, overrides: CorsOverrides | None = None) -> None:
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
            self._overrides = CorsOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> CorsOverrides:
        if self._overrides is None:
            raise RuntimeError("Cors overrides not initialised")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        version = config.get("version", "0.0.0")

        defaults = dict(FALLBACK_DEFAULTS)
        defaults.update(_load_defaults_bundle())

        return {
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_slug": MODULE_SLUG,
            "module_tier": MODULE_TIER,
            "module_kebab": module_name.replace("_", "-"),
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": version,
            "rapidkit_vendor_relative_path": infer_vendor_settings_path(config),
            "rapidkit_vendor_configuration_relative": NEST_VENDOR_CONFIGURATION_RELATIVE,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_routes_relative": PYTHON_ROUTES_REL,
            "python_config_relative": PYTHON_CONFIG_REL,
            "fastapi_test_relative": FASTAPI_TEST_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_health_relative": NEST_HEALTH_REL,
            "nest_routes_relative": NEST_ROUTES_REL,
            "nest_configuration_relative": NEST_CONFIGURATION_REL,
            DEFAULTS_KEY: defaults,
        }

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


def _create_generator(overrides: CorsOverrides | None = None) -> CorsModuleGenerator:
    return CorsModuleGenerator(overrides=overrides)


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
    overrides: CorsOverrides | None = None,
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
        variant_name, target_dir, renderer, context
    )


def main() -> None:
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = ", ".join(sorted(available_plugins.keys())) or "<none>"
        guidance = (
            "Usage: python -m modules.free.security.cors.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.security.cors.generate fastapi ../../examples/cors\n"
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
            print(f"Auto bumped cors module version to {config['version']}")
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
        print("💡 If this persists, run 'rapidkit modules doctor cors' or reinstall dependencies.")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
