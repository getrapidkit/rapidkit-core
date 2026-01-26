#!/usr/bin/env python3
"""Unified module generator for Celery."""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional

import yaml

from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim
from modules.shared.utils.health_specs import build_standard_health_spec
from modules.shared.versioning import ensure_version_consistency

JinjaEnvironment: Optional[Any] = None
FileSystemLoader: Optional[Any] = None
StrictUndefined: Optional[Any] = None
select_autoescape: Optional[Any] = None

with contextlib.suppress(ImportError):  # pragma: no cover - optional dependency
    from jinja2 import (
        Environment as JinjaEnvironment,
        FileSystemLoader,
        StrictUndefined,
        select_autoescape,
    )

MODULE_ROOT = Path(__file__).parent
DEFAULT_ENCODING = "utf-8"

MODULE_NAME = "celery"
MODULE_CLASS = "Celery"
MODULE_TITLE = "Celery"
MODULE_TIER = "free"
MODULE_BASE = "src/modules/free/tasks/celery"
PYTHON_OUTPUT_REL = f"{MODULE_BASE}/celery.py"
FASTAPI_CONFIG_REL = "config/tasks/celery.yaml"
FASTAPI_TEST_REL = "tests/modules/integration/tasks/test_celery_integration.py"
NEST_SERVICE_OUTPUT_REL = f"{MODULE_BASE}/celery.service.ts"
NEST_CONFIGURATION_REL = f"{MODULE_BASE}/celery.configuration.ts"
NEST_HEALTH_CONTROLLER_REL = f"{MODULE_BASE}/health/celery-health.controller.ts"
NEST_HEALTH_MODULE_REL = f"{MODULE_BASE}/health/celery-health.module.ts"
NEST_TEST_REL = "tests/modules/integration/tasks/celery.integration.spec.ts"
NEST_VENDOR_CONFIGURATION_REL = "nestjs/configuration.js"


class GeneratorError(SystemExit):
    """Explicit generator failure with helpful messaging."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(exit_code)
        self.message = message


class TemplateRenderer:
    """Render Jinja2 templates with graceful fallback."""

    def __init__(self) -> None:
        self._env: Optional[Any] = None
        if JinjaEnvironment is None or FileSystemLoader is None or StrictUndefined is None:
            return

        if select_autoescape is None:
            raise GeneratorError(
                f"The {MODULE_TITLE} module requires jinja2 with select_autoescape support. Install or upgrade via 'pip install --upgrade jinja2'."
            )

        loader = FileSystemLoader(str(MODULE_ROOT))
        self._env = JinjaEnvironment(
            loader=loader,
            autoescape=select_autoescape(
                enabled_extensions=("html", "htm", "xml"),
                default_for_string=False,
                default=False,
            ),
            keep_trailing_newline=True,
            lstrip_blocks=False,
            trim_blocks=False,
            undefined=StrictUndefined,
        )

    def render(self, template_path: Path, context: Mapping[str, Any]) -> str:
        if self._env is None:
            raise GeneratorError(
                f"The {MODULE_TITLE} module requires jinja2 for template rendering. Install it via 'pip install jinja2'."
            )

        template = self._env.get_template(template_path.relative_to(MODULE_ROOT).as_posix())
        rendered = template.render(**context)
        if not isinstance(rendered, str):  # pragma: no cover - guard for unexpected output
            raise GeneratorError("Template rendering must produce a string output.")
        return rendered


def _format_missing_dependencies(details: Mapping[str, str]) -> str:
    if not details:
        return ""
    lines = ["Missing optional dependencies detected:"]
    for package, hint in details.items():
        lines.append(f"  - {package}: {hint}")
    return "\n".join(lines)


def load_module_config() -> Dict[str, Any]:
    config_path = MODULE_ROOT / "module.yaml"
    with config_path.open(encoding=DEFAULT_ENCODING) as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, Mapping):
        raise ValueError("module.yaml must resolve to a mapping")
    return dict(data)


def infer_vendor_runtime_path(config: Mapping[str, Any]) -> str:
    vendor_cfg = config.get("generation", {}).get("vendor", {})
    for entry in vendor_cfg.get("files", []):
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if isinstance(relative, str) and template_name.endswith(f"{MODULE_NAME}.py.j2"):
            return relative
    return f"{MODULE_BASE}/{MODULE_NAME}.py"


def infer_vendor_configuration_path(config: Mapping[str, Any]) -> str:
    vendor_cfg = config.get("generation", {}).get("vendor", {})
    for entry in vendor_cfg.get("files", []):
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if (
            isinstance(relative, str)
            and str(relative).endswith("nestjs/configuration.js")
            and template_name.endswith("configuration.js.j2")
        ):
            return relative
    return NEST_VENDOR_CONFIGURATION_REL


def _load_defaults_bundle() -> Dict[str, Any]:
    defaults_path = MODULE_ROOT / "config" / "base.yaml"
    if not defaults_path.exists():
        return {}
    with defaults_path.open(encoding=DEFAULT_ENCODING) as handle:
        try:
            data = yaml.safe_load(handle)
        except yaml.YAMLError:
            return {}
    if not isinstance(data, Mapping):
        return {}
    defaults = data.get("defaults")
    if isinstance(defaults, Mapping):
        return dict(defaults)
    return {}


def build_base_context(config: Mapping[str, Any]) -> Dict[str, Any]:
    module = str(config.get("name", MODULE_NAME))
    defaults_bundle = _load_defaults_bundle()
    config_defaults = {}
    module_defaults = config.get("defaults")
    if isinstance(module_defaults, Mapping):
        config_defaults = dict(module_defaults)

    merged_defaults = {**defaults_bundle, **config_defaults}
    settings_defaults = {}
    settings_payload = merged_defaults.get("settings")
    if isinstance(settings_payload, Mapping):
        settings_defaults = dict(settings_payload)

    autodiscover_defaults = merged_defaults.get("autodiscover")
    if isinstance(autodiscover_defaults, (list, tuple)):
        merged_defaults["autodiscover"] = [str(item) for item in autodiscover_defaults]
    else:
        merged_defaults["autodiscover"] = []

    for key in ("imports", "include"):
        value = settings_defaults.get(key)
        if isinstance(value, (list, tuple)):
            settings_defaults[key] = [str(item) for item in value]
        elif value is None:
            settings_defaults[key] = []

    context = {
        "rapidkit_vendor_module": module,
        "rapidkit_vendor_version": config.get("version", "0.0.0"),
        "rapidkit_vendor_relative_path": infer_vendor_runtime_path(config),
        "rapidkit_vendor_configuration_relative": infer_vendor_configuration_path(config),
        "module_name": module,
        "module_class_name": MODULE_CLASS,
        "module_title": MODULE_TITLE,
        "python_output_relative": PYTHON_OUTPUT_REL,
        "nest_output_relative": NEST_SERVICE_OUTPUT_REL,
        "module_tier": MODULE_TIER,
        "module_import_path": "modules.free.tasks.celery.celery",
        "fastapi_config_relative": FASTAPI_CONFIG_REL,
        "fastapi_test_relative": FASTAPI_TEST_REL,
        "nest_configuration_relative": NEST_CONFIGURATION_REL,
        "nest_health_controller_relative": NEST_HEALTH_CONTROLLER_REL,
        "nest_health_module_relative": NEST_HEALTH_MODULE_REL,
        "nest_test_relative": NEST_TEST_REL,
        "celery_defaults": merged_defaults,
        "celery_settings_defaults": settings_defaults,
    }
    return context


def write_file(destination: Path, content: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding=DEFAULT_ENCODING)
    print(f"Generated: {destination}")


def generate_vendor_files(
    config: Mapping[str, Any],
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
) -> None:
    vendor_cfg = config.get("generation", {}).get("vendor")
    if not vendor_cfg:
        return

    root = vendor_cfg.get("root", ".rapidkit/vendor")
    files = vendor_cfg.get("files", [])
    module_name = context["rapidkit_vendor_module"]
    version = context["rapidkit_vendor_version"]

    for entry in files:
        template_name = entry.get("template")
        if not isinstance(template_name, str):
            raise GeneratorError("Vendor file entry missing 'template' reference in module.yaml")

        template_path = MODULE_ROOT / template_name
        if not template_path.exists():
            raise GeneratorError(
                f"Vendor template '{template_path.relative_to(MODULE_ROOT)}' missing."
            )
        relative = entry.get("relative")
        if not isinstance(relative, str):
            raise GeneratorError("Vendor file entry missing 'relative' destination in module.yaml")

        file_context = {**context, **entry.get("context", {})}
        output = target_dir / root / module_name / version / relative
        rendered = renderer.render(template_path, file_context)
        write_file(output, rendered)


def generate_variant_files(
    config: Mapping[str, Any],
    variant_name: str,
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
) -> None:
    variants = config.get("generation", {}).get("variants", {})
    variant_cfg = variants.get(variant_name)
    if variant_cfg is None:
        available = ", ".join(sorted(variants)) or "<none>"
        raise GeneratorError(
            f"Variant '{variant_name}' not defined in module.yaml (available: {available})."
        )

    root = variant_cfg.get("root", ".")
    variant_context = variant_cfg.get("context", {})

    for entry in variant_cfg.get("files", []):
        template_name = entry.get("template")
        if not isinstance(template_name, str):
            raise GeneratorError(
                f"Variant '{variant_name}' file missing 'template' entry in module.yaml"
            )

        template_path = MODULE_ROOT / template_name
        if not template_path.exists():
            raise GeneratorError(
                f"Variant template '{template_path.relative_to(MODULE_ROOT)}' not found."
            )

        output_value = entry.get("output")
        if not isinstance(output_value, str):
            raise GeneratorError(
                f"Variant '{variant_name}' file missing 'output' destination in module.yaml"
            )

        output = Path(target_dir) / root / output_value
        file_context = {
            **context,
            **variant_context,
            **entry.get("context", {}),
        }
        rendered = renderer.render(template_path, file_context)
        write_file(output, rendered)

    # Materialise the canonical vendor-backed health shim into the generated
    # project (standard location src/health/<module>.py) and ensure the
    # shared health package is present. Best-effort; do not fail generation
    # if the vendor payload is not available.
    spec = build_standard_health_spec(MODULE_ROOT)
    with contextlib.suppress(RuntimeError, OSError):
        ensure_vendor_health_shim(target_dir, spec=spec)

    ensure_health_package(
        target_dir,
        extra_imports=[(f"src.health.{spec.module_name}", f"register_{spec.module_name}_health")],
    )


def main() -> None:
    EXPECTED_ARG_COUNT = 3
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        guidance = (
            "Usage: python -m modules.free.tasks.celery.generate <variant> <target_dir>\n"
            "Example: python -m modules.free.tasks.celery.generate fastapi ../../examples/celery\n"
            "Variants are declared in module.yaml"
        )
        raise GeneratorError(guidance, exit_code=2)

    variant_name = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve()

    missing_optional_dependencies: Dict[str, str] = {}
    if JinjaEnvironment is None:
        missing_optional_dependencies["jinja2"] = (
            "Install to unlock advanced templating (pip install jinja2)"
        )
    elif select_autoescape is None:
        missing_optional_dependencies["jinja2"] = (
            "Upgrade jinja2 to enable select_autoescape (pip install --upgrade jinja2)"
        )

    try:
        config = load_module_config()
        config, version_updated = ensure_version_consistency(
            config,
            module_root=MODULE_ROOT,
        )
        base_context = build_base_context(config)
        if version_updated:
            print(f"Auto bumped module version to {config['version']}")
        renderer = TemplateRenderer()

        generate_vendor_files(config, target_dir, renderer, base_context)
        generate_variant_files(config, variant_name, target_dir, renderer, base_context)
    except GeneratorError as exc:
        message = exc.message if isinstance(exc.message, str) else str(exc.message)
        dep_hint = _format_missing_dependencies(missing_optional_dependencies)
        if dep_hint:
            message = f"{message}\n\n{dep_hint}"
        print(message)
        sys.exit(exc.args[0] if exc.args else 1)
    except (RuntimeError, OSError, yaml.YAMLError) as exc:
        print("Generator failed with an unexpected error:")
        traceback = "\n".join(TracebackException.from_exception(exc).format())
        print(traceback)
        print("If this persists, run 'rapidkit modules doctor' or reinstall dependencies.")
        sys.exit(1)


if __name__ == "__main__":
    main()
