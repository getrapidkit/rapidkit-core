#!/usr/bin/env python3
"""Unified module generator for the Email module."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional, cast

import yaml

from modules.shared.exceptions import SettingsGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

from .frameworks import get_plugin, list_available_plugins
from .overrides import EmailOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "email"
MODULE_CLASS = "Email"
MODULE_TITLE = "Email Delivery"
MODULE_TIER = "free"
MODULE_SLUG = "free/communication/email"

VENDOR_RUNTIME_REL = "src/modules/free/communication/email/email.py"
VENDOR_HEALTH_REL = "src/health/email.py"
VENDOR_TYPES_REL = "src/modules/free/communication/email/email_types.py"

# New module layout under src/modules/<tier>/<category>/<slug>
MODULE_BASE = "src/modules/free/communication/email"

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/email.py"
PYTHON_ROUTES_REL = f"{MODULE_BASE}/routers/email.py"
PYTHON_HEALTH_REL = "src/health/email.py"
PYTHON_CONFIG_REL = "src/modules/free/communication/email/config/email.yaml"
PYTHON_TEST_REL = "tests/modules/free/communication/email/test_email_integration.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/email.service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/email.controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/email.module.ts"
NEST_CONFIG_REL = f"{MODULE_BASE}/email.configuration.ts"
NEST_HEALTH_REL = f"{MODULE_BASE}/email.health.ts"
NEST_TEST_REL = "tests/modules/integration/communication/email.integration.spec.ts"


class GeneratorError(SettingsGeneratorError):
    """Explicit generator error carrying additional context."""

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


def _infer_vendor_relative(config: Mapping[str, Any], suffix: str) -> str:
    vendor_cfg = config.get("generation", {}).get("vendor", {})
    files_cfg = vendor_cfg.get("files", [])
    for entry in files_cfg:
        if not isinstance(entry, Mapping):
            continue
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if (
            isinstance(relative, str)
            and isinstance(template_name, str)
            and template_name.endswith(suffix)
        ):
            return relative
    return suffix


def _deep_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _deep_copy(sub) for key, sub in value.items()}
    if isinstance(value, list):
        return [_deep_copy(item) for item in value]
    return value


def _load_defaults(config: Mapping[str, Any]) -> Dict[str, Any]:
    defaults = config.get("defaults")
    if isinstance(defaults, Mapping):
        return cast(Dict[str, Any], _deep_copy(defaults))
    return {}


class EmailModuleGenerator(BaseModuleGenerator):
    """Module generator that bridges vendor artefacts with framework variants."""

    def __init__(self, overrides: EmailOverrides | None = None) -> None:
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
            self._overrides = EmailOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> EmailOverrides:
        if self._overrides is None:
            raise RuntimeError("Email overrides not initialised")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        defaults = _load_defaults(config)
        runtime_relative = _infer_vendor_relative(config, VENDOR_RUNTIME_REL)
        health_relative = _infer_vendor_relative(config, VENDOR_HEALTH_REL)
        types_relative = _infer_vendor_relative(config, VENDOR_TYPES_REL)

        return {
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": config.get("version", "0.0.0"),
            "rapidkit_vendor_runtime_relative": runtime_relative,
            "rapidkit_vendor_health_relative": health_relative,
            "rapidkit_vendor_types_relative": types_relative,
            "vendor_runtime_relative": runtime_relative,
            "vendor_health_relative": health_relative,
            "vendor_types_relative": types_relative,
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_routes_relative": PYTHON_ROUTES_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_config_relative": PYTHON_CONFIG_REL,
            "python_test_relative": PYTHON_TEST_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_config_relative": NEST_CONFIG_REL,
            "nest_health_relative": NEST_HEALTH_REL,
            "nest_test_relative": NEST_TEST_REL,
            "email_defaults": defaults,
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


def _create_generator(overrides: EmailOverrides | None = None) -> EmailModuleGenerator:
    return EmailModuleGenerator(overrides=overrides)


def load_module_config() -> Dict[str, Any]:
    config_path = MODULE_ROOT / "module.yaml"
    with config_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, Mapping):
        raise GeneratorError("module.yaml must resolve to a mapping")
    return dict(data)


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
    config: Mapping[str, Any],
    variant_name: str,
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
) -> None:
    del config  # Config is provided for parity with legacy generator signatures.
    _create_generator().generate_variant_files(
        variant_name,
        target_dir,
        renderer,
        context,
    )


def create_renderer() -> TemplateRenderer:
    return _create_generator().create_renderer()


def main() -> None:
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        guidance = (
            "Usage: python -m modules.free.communication.email.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.communication.email.generate fastapi ../../examples/email\n"
            f"Available frameworks: {', '.join(available_plugins.keys())}"
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
    generator = EmailModuleGenerator()

    try:
        config = load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped email module version to {config['version']}")

        renderer = generator.create_renderer()
        if getattr(renderer, "jinja_env", None) is None:
            missing_optional_dependencies["jinja2"] = (
                "Install for advanced template rendering (pip install jinja2)"
            )

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
        print("💡 If this persists, run 'rapidkit modules doctor email' or reinstall dependencies.")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
