#!/usr/bin/env python3
"""Unified module generator for OAuth provider scaffolding."""

from __future__ import annotations

import contextlib
import sys
from contextlib import suppress
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

MODULE_NAME = "oauth"
MODULE_CLASS = "Oauth"
MODULE_TITLE = "OAuth"
MODULE_TIER = "free"
# New module layout under src/modules/<tier>/<category>/<slug>
MODULE_SLUG = "free/auth/oauth"
MODULE_BASE = "src/modules/free/auth/oauth"
PYTHON_OUTPUT_REL = f"{MODULE_BASE}/oauth.py"
NEST_OUTPUT_REL = f"{MODULE_BASE}/oauth.service.ts"
DEFAULTS_KEY = "oauth_defaults"


class TemplateRenderer:
    """Render Jinja2 templates with graceful fallback."""

    def __init__(self) -> None:
        self._env: Optional[Any] = None
        if JinjaEnvironment is None or FileSystemLoader is None or StrictUndefined is None:
            return

        loader = FileSystemLoader(str(MODULE_ROOT))
        if select_autoescape is None:
            raise GeneratorError(
                f"The {MODULE_TITLE} module requires jinja2 with select_autoescape support. Install or upgrade via 'pip install --upgrade jinja2'."
            )

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
                "The OAuth module requires jinja2 for template rendering. Install it via 'pip install jinja2'."
            )

        normalized_path = template_path
        if not normalized_path.is_absolute():
            normalized_path = (MODULE_ROOT / normalized_path).resolve()
        else:
            normalized_path = normalized_path.resolve()

        try:
            template_name = normalized_path.relative_to(MODULE_ROOT).as_posix()
        except ValueError:
            from os import path as osp

            template_name = osp.relpath(str(normalized_path), str(MODULE_ROOT))
            template_name = template_name.replace("\\", "/")

        template = self._env.get_template(template_name)
        rendered = template.render(**context)
        if not isinstance(rendered, str):  # pragma: no cover
            raise GeneratorError("Template rendering must produce a string output.")
        return rendered


class GeneratorError(SystemExit):
    """Explicit generator failure with helpful messaging."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(exit_code)
        self.message = message


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


def infer_vendor_settings_path(config: Mapping[str, Any]) -> str:
    vendor_cfg = config.get("generation", {}).get("vendor", {})
    for entry in vendor_cfg.get("files", []):
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if isinstance(relative, str) and template_name.endswith(f"{MODULE_NAME}.py.j2"):
            return relative
    return PYTHON_OUTPUT_REL


def _load_defaults(config: Mapping[str, Any]) -> Dict[str, Any]:
    defaults: Any = config.get("defaults")
    if isinstance(defaults, Mapping):
        return dict(defaults)

    defaults_path = MODULE_ROOT / "config" / "base.yaml"
    if defaults_path.exists():
        with defaults_path.open(encoding=DEFAULT_ENCODING) as fh:
            base_config = yaml.safe_load(fh)
        if isinstance(base_config, Mapping):
            defaults = base_config.get("defaults")
            if isinstance(defaults, Mapping):
                return dict(defaults)
    return {}


def build_base_context(config: Mapping[str, Any]) -> Dict[str, Any]:
    module = str(config.get("name", MODULE_NAME))
    defaults = _load_defaults(config)
    context = {
        "rapidkit_vendor_module": module,
        "rapidkit_vendor_version": config.get("version", "0.0.0"),
        "rapidkit_vendor_relative_path": infer_vendor_settings_path(config),
        "module_name": module,
        "module_class_name": MODULE_CLASS,
        "module_title": MODULE_TITLE,
        "python_output_relative": PYTHON_OUTPUT_REL,
        "nest_output_relative": NEST_OUTPUT_REL,
        "module_tier": MODULE_TIER,
        "module_defaults": defaults,
        DEFAULTS_KEY: defaults,
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

    # Materialise vendor-backed canonical health shim and alias into the
    # generated project so tests and consumers can find the shared runtime.
    spec = build_standard_health_spec(MODULE_ROOT)
    with suppress(RuntimeError, OSError):
        ensure_vendor_health_shim(target_dir, spec=spec)
        # If the vendor payload was generated in this run, prefer the vendor
        # runtime implementation for the shared alias so tests that expect
        # the concrete runtime functions (not just the compatibility shim)
        # will find the real content.
        # vendor payload (if present) is stored under .rapidkit/vendor/<module>/<version>
        # Under canonical-only policy we do not create legacy alias files.
        # If vendor runtime exists, ensure_vendor_health_shim already created the canonical
        # target at spec.target_relative_path and tests/consumers will use that.
        # Under canonical-only policy we do not create legacy alias files.
        # ensure_vendor_health_shim already created the canonical target at spec.target_relative_path
        # if a vendor runtime was available in the .rapidkit/vendor layout.
    # suppressed: allow generation to continue when vendor payload missing

    ensure_health_package(
        target_dir,
        extra_imports=[(f"src.health.{spec.module_name}", f"register_{spec.module_name}_health")],
    )


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


def main() -> None:
    EXPECTED_ARG_COUNT = 3
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        guidance = (
            "Usage: python -m modules.free.auth.oauth.generate <variant> <target_dir>\n"
            "Example: python -m modules.free.auth.oauth.generate fastapi ../../examples/oauth\n"
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
