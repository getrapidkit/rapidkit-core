#!/usr/bin/env python3
"""Deployment toolkit generator delivering Docker, Makefile, and CI assets."""

from __future__ import annotations

import sys
from pathlib import Path
from shutil import copy2
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional

import yaml

from modules.free.essentials.deployment.frameworks import get_plugin, list_available_plugins
from modules.free.essentials.deployment.overrides import DeploymentOverrides
from modules.shared.exceptions import ModuleGeneratorError, SettingsGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies, write_file
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

MODULE_ROOT = Path(__file__).parent
TEMPLATES_ROOT = MODULE_ROOT / "templates"
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "deployment"
MODULE_CLASS = "Deployment"
MODULE_TITLE = "Deployment Toolkit"
MODULE_TIER = "free"
MODULE_SLUG = "free/essentials/deployment"
MODULE_BASE = Path("src/modules/free/essentials/deployment")
VENDOR_RUNTIME_REL = str(MODULE_BASE / "deployment.py")
VENDOR_TYPES_REL = str(MODULE_BASE / "deployment_types.py")
VENDOR_CONFIG_REL = "deployment/fastapi/docker-compose.yml"

PYTHON_RUNTIME_REL = str(MODULE_BASE / "deployment.py")
PYTHON_ROUTES_REL = str(MODULE_BASE / "routers" / "deployment.py")
PYTHON_HEALTH_REL = str(MODULE_BASE / "health" / "deployment.py")
PYTHON_CONFIG_REL = "src/modules/free/essentials/deployment/config/deployment.yaml"
PYTHON_TEST_REL = "tests/modules/free/essentials/deployment/test_deployment_integration.py"

NEST_SERVICE_REL = str(MODULE_BASE / "deployment.service.ts")
NEST_CONTROLLER_REL = str(MODULE_BASE / "deployment.controller.ts")
NEST_MODULE_REL = str(MODULE_BASE / "deployment.module.ts")
NEST_CONFIG_REL = str(MODULE_BASE / "deployment.configuration.ts")
NEST_HEALTH_REL = str(MODULE_BASE / "health" / "deployment-health.controller.ts")
NEST_TEST_REL = "tests/modules/integration/essentials/deployment/deployment.integration.spec.ts"


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


def _infer_vendor_relative(config: Mapping[str, Any], suffix: str) -> str:
    vendor_cfg = config.get("generation", {}).get("vendor", {})
    files_cfg = vendor_cfg.get("files", [])
    for entry in files_cfg:
        template_name = entry.get("template") if isinstance(entry, Mapping) else None
        relative = entry.get("relative") if isinstance(entry, Mapping) else None
        if not isinstance(template_name, str) or not isinstance(relative, str):
            continue
        suffix_name = Path(suffix).name
        if Path(relative).name == suffix_name:
            return relative
        template_basename = Path(template_name).name
        if template_basename.endswith(f"{suffix_name}.j2") or template_basename == suffix_name:
            return relative
    return suffix


class DeploymentModuleGenerator(BaseModuleGenerator):
    def __init__(self, overrides: DeploymentOverrides | None = None) -> None:
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
            self._overrides = DeploymentOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> DeploymentOverrides:
        if self._overrides is None:
            raise RuntimeError("Deployment overrides not initialized")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        options = config.get("options", {}) if isinstance(config, Mapping) else {}

        module_name = str(config.get("name", MODULE_NAME))
        module_version = str(config.get("version", "0.0.0"))

        include_ci = bool(options.get("include_ci", True))
        include_postgres = bool(options.get("include_postgres", True))
        python_version = str(options.get("python_version", "3.10.14"))
        node_version = str(options.get("node_version", "20.19.6"))

        package_manager = str(options.get("package_manager", "npm"))
        package_manager_command = "pnpm" if package_manager == "pnpm" else package_manager

        deployment_defaults = {
            "include_ci": include_ci,
            "include_postgres": include_postgres,
            "python_version": python_version,
            "node_version": node_version,
            "package_manager": package_manager,
            "package_manager_command": package_manager_command,
        }

        runtime_relative = _infer_vendor_relative(config, VENDOR_RUNTIME_REL)
        types_relative = _infer_vendor_relative(config, VENDOR_TYPES_REL)
        vendor_config_relative = _infer_vendor_relative(config, VENDOR_CONFIG_REL)

        return {
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": module_version,
            "rapidkit_vendor_runtime_relative": runtime_relative,
            "rapidkit_vendor_types_relative": types_relative,
            "rapidkit_vendor_configuration_relative": vendor_config_relative,
            "rapidkit_vendor_relative_path": runtime_relative,
            "vendor_runtime_relative": runtime_relative,
            "vendor_types_relative": types_relative,
            "vendor_configuration_relative": vendor_config_relative,
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "include_ci": include_ci,
            "include_postgres": include_postgres,
            "python_version": python_version,
            "node_version": node_version,
            "package_manager": package_manager,
            "package_manager_command": package_manager_command,
            "deployment_defaults": deployment_defaults,
            "python_output_relative": PYTHON_RUNTIME_REL,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_routes_relative": PYTHON_ROUTES_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_config_relative": PYTHON_CONFIG_REL,
            "python_test_relative": PYTHON_TEST_REL,
            "nest_output_relative": NEST_SERVICE_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_config_relative": NEST_CONFIG_REL,
            "nest_health_relative": NEST_HEALTH_REL,
            "nest_test_relative": NEST_TEST_REL,
            "enabled_features": options.get("enabled_features"),
        }

    def apply_base_context_overrides(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return self.overrides.apply_base_context(context)

    def apply_variant_context_pre(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context(context)

    def apply_variant_context_post(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context(context)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:
        if variant_name.startswith("nestjs"):
            vendor_root = (
                target_dir
                / ".rapidkit"
                / "vendor"
                / str(enriched_context.get("rapidkit_vendor_module") or MODULE_NAME)
                / str(enriched_context.get("rapidkit_vendor_version") or "0.0.0")
            )
            controller_src = (
                vendor_root / "deployment" / "nestjs" / "deployment-health.controller.ts"
            )
            module_src = vendor_root / "deployment" / "nestjs" / "deployment-health.module.ts"

            health_dir = target_dir / "src" / "health"
            health_dir.mkdir(parents=True, exist_ok=True)

            if controller_src.exists():
                copy2(controller_src, health_dir / "deployment-health.controller.ts")
            if module_src.exists():
                copy2(module_src, health_dir / "deployment-health.module.ts")

        extra_template = self.overrides.extra_workflow_template()
        if not extra_template:
            return

        if not extra_template.exists():
            self.raise_error(
                f"Extra workflow template '{extra_template}' not found.",
                context={"framework": variant_name, "template_path": str(extra_template)},
            )

        extra_root = self.overrides.extra_workflow_root() or extra_template.parent
        extra_renderer = TemplateRenderer(extra_root)

        extra_context = dict(enriched_context)
        extra_context.setdefault("variant", variant_name)
        extra_context.setdefault("framework", variant_name)

        try:
            rendered_extra = extra_renderer.render(extra_template, extra_context)
        except (RuntimeError, OSError, ValueError, TypeError, ModuleGeneratorError) as exc:
            self.raise_error(
                f"Failed to render extra workflow template '{extra_template}'.",
                context={"framework": variant_name, "error": str(exc)},
            )

        output_dir = target_dir / ".github" / "workflows"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_name = (
            extra_template.name[:-3] if extra_template.name.endswith(".j2") else extra_template.name
        )
        output_path = output_dir / output_name
        write_file(output_path, rendered_extra)


def _create_generator(overrides: DeploymentOverrides | None = None) -> DeploymentModuleGenerator:
    return DeploymentModuleGenerator(overrides=overrides)


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
    overrides: DeploymentOverrides | None = None,
) -> None:
    _create_generator(overrides=overrides).generate_variant_files(
        variant_name, target_dir, renderer, context
    )


def main() -> None:
    EXPECTED_ARG_COUNT = 3
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        available_plugins = list_available_plugins()
        available_names = list(available_plugins.keys())
        guidance = (
            "Usage: python -m modules.free.essentials.deployment.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.essentials.deployment.generate fastapi ../../examples/deployment\n"
            f"Available frameworks: {', '.join(available_names)}"
        )
        raise GeneratorError(
            guidance,
            exit_code=2,
            context={"provided_args": sys.argv[1:], "expected_arg_count": EXPECTED_ARG_COUNT - 1},
        )

    variant_name = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve()

    missing_optional_dependencies: Dict[str, str] = {}
    generator = DeploymentModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped deployment module version to {config['version']}")
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
            "💡 If this persists, run 'rapidkit modules doctor deployment' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
