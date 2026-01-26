#!/usr/bin/env python3
"""Unified module generator for Ai Assistant."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional

import yaml

from modules.shared.exceptions import ModuleGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

from .frameworks import get_plugin, list_available_plugins

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "ai_assistant"
MODULE_CLASS = "AiAssistant"
MODULE_TITLE = "Ai Assistant"
MODULE_TIER = "free"
MODULE_SLUG = "free/ai/ai_assistant"
MODULE_CATEGORY = "ai"
MODULE_BASE = "src/modules/free/ai/ai_assistant"

PYTHON_OUTPUT_REL = f"{MODULE_BASE}/ai_assistant.py"
PYTHON_TYPES_REL = f"{MODULE_BASE}/ai_assistant_types.py"
PYTHON_HEALTH_REL = f"{MODULE_BASE}/health/ai_assistant.py"

NEST_OUTPUT_REL = f"{MODULE_BASE}/ai-assistant/ai_assistant.service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/ai-assistant/ai_assistant.controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/ai-assistant/ai_assistant.module.ts"
NEST_HEALTH_REL = f"{MODULE_BASE}/ai-assistant/ai_assistant.health.ts"
NEST_VALIDATION_REL = f"{MODULE_BASE}/ai-assistant/ai_assistant.validation.ts"
NEST_INDEX_REL = f"{MODULE_BASE}/ai-assistant/index.ts"
NEST_CONFIGURATION_REL = f"{MODULE_BASE}/ai-assistant/configuration.ts"

VENDOR_RELATIVE = f"{MODULE_BASE}/ai_assistant.py"
VENDOR_TYPES_RELATIVE = f"{MODULE_BASE}/ai_assistant_types.py"
VENDOR_HEALTH_RELATIVE = f"{MODULE_BASE}/health/ai_assistant.py"
MODULE_IMPORT_PATH = "modules.free.ai.ai_assistant"


class GeneratorError(ModuleGeneratorError):
    """Explicit generator failure carrying guidance for maintainers."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: int = 1,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        error_context = dict(context or {})
        error_context.setdefault("exit_code", exit_code)
        super().__init__(message, context=error_context)
        self.exit_code = exit_code


def infer_vendor_primary_path(config: Mapping[str, Any]) -> str:
    """Return the vendor relative path used as the default output."""

    vendor_cfg = config.get("generation", {}).get("vendor", {})
    for entry in vendor_cfg.get("files", []):
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if (
            isinstance(template_name, str)
            and template_name.endswith(f"{MODULE_NAME}.py.j2")
            and isinstance(relative, str)
        ):
            return relative
    return VENDOR_RELATIVE


class AiAssistantModuleGenerator(BaseModuleGenerator):
    def __init__(self) -> None:
        super().__init__(
            module_root=MODULE_ROOT,
            templates_root=MODULE_ROOT,
            project_root=PROJECT_ROOT,
            module_identifier=MODULE_NAME,
            get_plugin=get_plugin,
            list_plugins=list_available_plugins,
            error_cls=GeneratorError,
        )

    def build_base_context(self, config: Mapping[str, Any]) -> Dict[str, Any]:
        module = str(config.get("name", MODULE_NAME))
        return {
            "module_name": module,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "module_category": MODULE_CATEGORY,
            "module_kebab": "ai-assistant",
            "rapidkit_vendor_module": module,
            "rapidkit_vendor_version": config.get("version", "0.1.0"),
            "rapidkit_vendor_relative_path": infer_vendor_primary_path(config),
            "rapidkit_vendor_types_path": VENDOR_TYPES_RELATIVE,
            "rapidkit_vendor_health_path": VENDOR_HEALTH_RELATIVE,
            "python_output_relative": PYTHON_OUTPUT_REL,
            "python_types_relative": PYTHON_TYPES_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "nest_output_relative": NEST_OUTPUT_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_health_relative": NEST_HEALTH_REL,
            "nest_validation_relative": NEST_VALIDATION_REL,
            "nest_index_relative": NEST_INDEX_REL,
            "nest_configuration_relative": NEST_CONFIGURATION_REL,
            "enabled_features": [
                "runtime-facade",
                "framework-plugins",
                "module-overrides",
                "health-checks",
            ],
        }


def _create_generator() -> AiAssistantModuleGenerator:
    return AiAssistantModuleGenerator()


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
) -> None:
    _create_generator().generate_variant_files(variant_name, target_dir, renderer, context)


def main() -> None:
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = list(available_plugins.keys())
        guidance = (
            f"Usage: python -m {MODULE_IMPORT_PATH}.generate <framework> <target_dir>\n"
            f"Example: python -m {MODULE_IMPORT_PATH}.generate fastapi ./tmp/{MODULE_NAME}\n"
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

    try:
        generator = AiAssistantModuleGenerator()
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.build_base_context(config)
        if version_updated:
            print(f"Auto bumped {MODULE_NAME} module version to {config['version']}")
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
            f"💡 If this persists, run 'rapidkit modules doctor {MODULE_NAME}' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
