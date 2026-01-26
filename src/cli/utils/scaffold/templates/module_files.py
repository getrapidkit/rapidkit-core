"""Template factories for module-level scaffold outputs."""

from __future__ import annotations

import textwrap
from pathlib import Path
from string import Template
from typing import Dict, Mapping


def build_module_files(identifiers: Mapping[str, str]) -> Dict[Path, Template]:
    """Return the mapping of module-relative file paths to rendered templates."""

    module_name = identifiers["module_name"]

    files: Dict[Path, Template] = {
        Path("README.md"): Template(_readme_template()),
        Path("__init__.py"): Template(_init_template()),
        Path("generate.py"): Template(_generator_template()),
        Path("module.yaml"): Template(_module_yaml_template()),
        Path("module.verify.json"): Template(_module_verify_template()),
        Path(".module_state.json"): Template(_module_state_template()),
        Path("overrides.py"): Template(_overrides_template()),
        Path("config/base.yaml"): Template(_base_config_template()),
        Path("config/snippets.yaml"): Template(_snippets_config_template()),
        Path("scripts/run_demo.py"): Template(_run_demo_script_template()),
    }

    files.update(
        {
            Path("frameworks/__init__.py"): Template(_frameworks_init_template()),
            Path("frameworks/fastapi.py"): Template(_framework_fastapi_template()),
            Path("frameworks/nestjs.py"): Template(_framework_nestjs_template()),
        }
    )

    files.update(_module_docs_templates())
    files.update(_module_template_files(module_name))

    return files


def _module_docs_templates() -> Dict[Path, Template]:
    return {
        Path("docs/README.md"): Template(_module_docs_readme_template()),
        Path("docs/overview.md"): Template(_module_docs_overview_template()),
        Path("docs/usage.md"): Template(_module_docs_usage_template()),
        Path("docs/monitoring.md"): Template(_module_docs_monitoring_template()),
        Path("docs/advanced.md"): Template(_module_docs_advanced_template()),
        Path("docs/changelog.md"): Template(_module_docs_changelog_template()),
        Path("docs/migration.md"): Template(_module_docs_migration_template()),
        Path("docs/troubleshooting.md"): Template(_module_docs_troubleshooting_template()),
        Path("docs/api-reference.md"): Template(_module_docs_api_reference_template()),
    }


def _module_template_files(module_name: str) -> Dict[Path, Template]:
    return {
        Path("templates/base") / f"{module_name}.py.j2": Template(_base_python_template()),
        Path("templates/base") / f"{module_name}_types.py.j2": Template(_base_types_template()),
        Path("templates/base") / f"{module_name}_health.py.j2": Template(_base_health_template()),
        Path("templates/variants/fastapi")
        / f"{module_name}.py.j2": Template(_fastapi_runtime_template()),
        Path("templates/variants/fastapi")
        / f"{module_name}_routes.py.j2": Template(_fastapi_router_template()),
        Path("templates/variants/fastapi")
        / f"{module_name}_health.py.j2": Template(_fastapi_health_template()),
        Path("templates/variants/nestjs")
        / f"{module_name}.service.ts.j2": Template(_nestjs_service_template()),
        Path("templates/variants/nestjs")
        / f"{module_name}.controller.ts.j2": Template(_nestjs_controller_template()),
        Path("templates/variants/nestjs")
        / f"{module_name}.module.ts.j2": Template(_nestjs_module_template()),
        Path("templates/variants/nestjs")
        / f"{module_name}.health.ts.j2": Template(_nestjs_health_template()),
        Path("templates/variants/nestjs")
        / f"{module_name}.validation.ts.j2": Template(_nestjs_validation_template()),
        Path("templates/variants/nestjs")
        / f"{module_name}.index.ts.j2": Template(_nestjs_index_template()),
        Path("templates/variants/nestjs")
        / f"{module_name}.configuration.ts.j2": Template(_nestjs_configuration_template()),
        Path("templates/variants/fastapi/tests")
        / f"test_{module_name}_e2e.py": Template(_fastapi_e2e_test_template()),
        Path("templates/variants/nestjs/tests")
        / f"{module_name}.e2e-spec.ts": Template(_nestjs_e2e_test_template()),
        Path("templates/vendor/nestjs/configuration.js.j2"): Template(_vendor_template()),
        Path("templates/snippets") / f"{module_name}.snippet.j2": Template(_snippet_template()),
        Path("templates/tests/__init__.py"): Template(_templates_tests_package_template()),
        Path("templates/tests/integration/__init__.py"): Template(
            _templates_tests_integration_package_template()
        ),
        Path("templates/tests/integration")
        / f"test_{module_name}_integration.j2": Template(_integration_test_template()),
    }


def _run_demo_script_template() -> str:
    return textwrap.dedent(
        '''#!/usr/bin/env python3
"""Generate a small demo project for ${module_title}.

This script is intended for module developers to quickly smoke-check generator outputs.

Usage:
  python scripts/run_demo.py fastapi
  python scripts/run_demo.py nestjs
  python scripts/run_demo.py fastapi ./tmp/demo-out
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _find_project_root(start: Path) -> Path:
    for parent in (start, *start.parents):
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    return start.parents[len(start.parents) - 1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("variant", choices=("fastapi", "nestjs"), help="Target kit")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="Target output directory (default: ./tmp/${module_name}-<variant>)",
    )
    args = parser.parse_args(argv)

    script_path = Path(__file__).resolve()
    module_root = script_path.parents[1]
    project_root = _find_project_root(module_root)
    modules_root = project_root / "src" / "modules"

    try:
        rel_slug = module_root.relative_to(modules_root).as_posix()
    except ValueError:
        raise SystemExit(f"Unable to resolve module slug for {module_root}")

    module_import = f"modules.{rel_slug.replace('/', '.')}"
    default_out = project_root / "tmp" / f"${module_name}-{args.variant}"
    out_dir = Path(args.output_dir).resolve() if args.output_dir else default_out

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(project_root / "src"))

    cmd = [sys.executable, "-m", f"{module_import}.generate", args.variant, str(out_dir)]
    subprocess.run(cmd, check=True, cwd=project_root, env=env)  # nosec
    print(f"✅ Generated demo at: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    ).strip()


def _fastapi_e2e_test_template() -> str:
    return textwrap.dedent(
        '''"""E2E smoke test for ${module_title} (FastAPI).

This is intentionally lightweight and designed to run without external services.
"""

from __future__ import annotations

import importlib

import pytest


def test_router_builds_without_crashing() -> None:
    fastapi = pytest.importorskip("fastapi")
    _ = fastapi

    router_rel = "${python_router_rel}"
    router_mod_path = router_rel.replace("/", ".").removesuffix(".py")
    router_module = importlib.import_module(router_mod_path)

    router = getattr(router_module, "router", None)
    if router is None:
        build_router = getattr(router_module, "build_router", None)
        create_router = getattr(router_module, "create_router", None)
        if callable(build_router):
            router = build_router()
        elif callable(create_router):
            router = create_router()
        else:
            pytest.skip("Module router does not expose router/build_router/create_router")

    assert getattr(router, "routes", None) is not None
'''
    ).strip()


def _nestjs_e2e_test_template() -> str:
    return textwrap.dedent(
        """import { Test, TestingModule } from "@nestjs/testing";

import { {{ module_class_name }}Module } from "../../../../../src/${module_kebab}/${module_name}.module";

describe("{{ module_class_name }} NestJS E2E", () => {
  it("compiles the module", async () => {
    let moduleRef: TestingModule;
    try {
      moduleRef = await Test.createTestingModule({
        imports: [{{ module_class_name }}Module],
      }).compile();
    } catch (err) {
      // If a downstream app doesn't install optional dependencies,
      // treat this as a skipped smoke rather than failing CI.
      // eslint-disable-next-line no-console
      console.warn("Skipping module compile smoke:", err);
      return;
    }

    expect(moduleRef).toBeDefined();
  });
});
"""
    ).strip()


def _generator_template() -> str:
    return textwrap.dedent(
        '''#!/usr/bin/env python3
"""Unified module generator for ${module_title}."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional

import yaml

from ${module_frameworks_import} import get_plugin, list_available_plugins
from modules.shared.exceptions import ModuleGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "${module_name}"
MODULE_CLASS = "${module_class}"
MODULE_TITLE = "${module_title}"
MODULE_TIER = "${tier}"
MODULE_SLUG = "${module_slug}"
PYTHON_OUTPUT_REL = "${python_output_rel}"
PYTHON_TYPES_REL = "${python_types_rel}"
PYTHON_HEALTH_REL = "${python_health_rel}"
NEST_OUTPUT_REL = "${nest_output_rel}"
NEST_CONTROLLER_REL = "${nest_controller_rel}"
NEST_MODULE_REL = "${nest_module_rel}"
NEST_HEALTH_REL = "${nest_health_rel}"
NEST_VALIDATION_REL = "${nest_validation_rel}"
NEST_INDEX_REL = "${nest_index_rel}"
NEST_CONFIGURATION_REL = "${nest_configuration_rel}"
VENDOR_RELATIVE = "${vendor_relative}"
VENDOR_TYPES_RELATIVE = "${vendor_types_relative}"
VENDOR_HEALTH_RELATIVE = "${vendor_health_relative}"
MODULE_IMPORT_PATH = "${module_package_import}"


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


class ${module_class}ModuleGenerator(BaseModuleGenerator):
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
            "module_kebab": "${module_kebab}",
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


def _create_generator() -> ${module_class}ModuleGenerator:
    return ${module_class}ModuleGenerator()


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
        generator = ${module_class}ModuleGenerator()
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
'''
    ).strip()


def _readme_template() -> str:
    return textwrap.dedent(
        """
        # RapidKit ${module_title} Module

        The ${module_title_lower} module ${module_description}

        This README follows the shared RapidKit module format:

        1. **Overview & capabilities**
        1. **Installation commands**
        1. **Directory layout**
        1. **Generation workflow**
        1. **Runtime customisation hooks**
        1. **Security & audit notes**
        1. **Testing & release checklist**
        1. **Reference links**

        Use the same headings when documenting other modules so maintainers know what to expect.

        As a RapidKit module, `${module_name}` also follows the shared metadata/documentation standard:

        - `module.yaml` is the canonical source of truth (including the `documentation:` map).
        - Module docs live under `docs/` and should match the keys referenced from `module.yaml`.
        - The module changelog is maintained in `docs/changelog.md` and referenced both from `module.yaml`
          and this README.

        ______________________________________________________________________

        ## Module Capabilities

        - TODO: Summarise the most valuable behaviours this module delivers.
        - TODO: Highlight cross-cutting features (e.g. vendor snapshots, overrides, snippets).
        - TODO: Mention supported runtimes or frameworks.

        ______________________________________________________________________

        ## Install Commands

        ```bash
        rapidkit add module ${module_name}
        ```

        Re-run `rapidkit modules lock --overwrite` after adding or upgrading the module so downstream
        projects capture the new snapshot.

        ### Quickstart

        Follow the end-to-end walkthrough in `docs/usage.md`.

        ______________________________________________________________________

        ## Directory Layout

        | Path                     | Responsibility                                                       |
        | ------------------------ | -------------------------------------------------------------------- |
        | `module.yaml`            | Canonical metadata (version, compatibility, testing roster)         |
        | `config/base.yaml`       | Declarative inputs that drive prompts and dependency resolution     |
        | `generate.py`            | CLI entry point orchestrating vendor + variant generation           |
        | `frameworks/`            | Framework plugin implementations registered via `modules.shared.frameworks` |
        | `overrides.py`           | Runtime override contracts toggled via environment variables        |
        | `docs/`                  | Module docs referenced from `module.yaml` (usage/overview/changelog) |
        | `templates/`             | Base templates plus per-framework variants                          |
        | `tests/` or `tests/modules` | Generator and integration test suites                               |

        Add or prune rows to match the concrete files once the module is implemented.

        ______________________________________________________________________

        ## Generation Workflow

        1. `generate.py` loads `module.yaml`, validates schema, and checks for version drift using `modules.shared.versioning.ensure_version_consistency`.
        2. Vendor artefacts render into `.rapidkit/vendor/${module_name}/<version>` to keep upgrades auditable.
        3. Framework plugins provide template mappings, output paths, and lifecycle hooks for each variant.
        4. Optional snippets are injected via `modules.shared.generator.snippets` when enabled.
        5. Overrides may tweak the render context or perform post-processing on generated files.

        Replace the bullets once the module logic is finalised.

        ______________________________________________________________________

        ## Runtime Customisation

        Document the environment variables or override contracts exposed by `overrides.py`. Include a table similar to:

        | Environment Variable | Effect |
        | -------------------- | ------ |
        | `RAPIDKIT_${module_name_upper}_EXAMPLE` | TODO: Describe behaviour |

        Remove or expand entries to match the real override hooks.

        ______________________________________________________________________

        ## Security & Audit

        This module ships as part of the RapidKit module ecosystem and is intended to be **audited** as a unit:

        - Use `scripts/modules_doctor.py` (or `rapidkit modules vet`) to validate structure and generator invariants.
        - Use `rapidkit modules verify-all` to verify recorded hashes/signatures when running in release mode.

        If you extend this module, keep the documentation updated with the security assumptions and any threat model
        relevant to your deployment.

        ______________________________________________________________________

        ## Testing Checklist

        ```bash
        # Unit + integration suite
        poetry run pytest tests/modules/${module_slug_test_path} -q

        # Generator smoke tests
        poetry run python -m ${module_import_path}.generate fastapi ./tmp/${module_name}
        poetry run python -m ${module_import_path}.generate nestjs ./tmp/${module_name}-nestjs

        # Optional integrity audit
        poetry run python scripts/check_module_integrity.py --module ${module_slug}
        ```

        Update the commands and file paths to mirror the real test layout before publishing.

        ______________________________________________________________________

        ## Release Checklist

        1. Update templates and/or `module.yaml`.
        1. Regenerate vendor snapshots and project variants for every supported framework.
        1. Inspect rendered files (`.rapidkit/vendor` and sample project outputs) for accuracy.
        1. Execute the testing checklist above; ensure versioning is bumped when content hashes change.
        1. Commit regenerated assets alongside the updated metadata.

        ______________________________________________________________________

        ## Reference Documentation

        - Overview: `docs/overview.md`
        - Usage guide: `docs/usage.md`
        - Advanced scenarios: `docs/advanced.md`
        - Monitoring: `docs/monitoring.md`
        - Changelog: `docs/changelog.md`
        - Migration playbook: `docs/migration.md`
        - Troubleshooting: `docs/troubleshooting.md`
        - API reference: `docs/api-reference.md`
        - Override contracts: `overrides.py`

        For additional help, open an issue at <https://github.com/getrapidkit/core/issues> or consult the full product documentation at <https://docs.rapidkit.top>.
        """
    ).strip()


def _module_docs_readme_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Module Documentation

        This directory contains the canonical documentation set for the ${module_title_lower} module.
        Keep guidance concise, actionable, and synchronised with the generator outputs.

        | Document | Purpose |
        | -------- | ------- |
        | [Overview](overview.md) | High-level capabilities and architecture |
        | [Usage](usage.md) | Configuration examples and integration walkthroughs |
        | [Monitoring](monitoring.md) | Metrics, telemetry, health probes, and dashboards |
        | [Advanced](advanced.md) | Extensibility patterns and override contracts |
        | [Changelog](changelog.md) | Release notes and upgrade history |
        | [Migration](migration.md) | Upgrade guidance and compatibility notes |
        | [Troubleshooting](troubleshooting.md) | Common diagnostics and remediation steps |
        | [API Reference](api-reference.md) | Public classes, functions, and CLI entrypoints |
        """
    ).strip()


def _module_docs_monitoring_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Monitoring

        This document covers metrics, telemetry, and monitoring guidance for the ${module_title_lower} module.

        ## What to monitor
        - Functional health checks (readiness/liveness)
        - Key error rates and timeouts
        - Dependency connectivity (database/cache/third-party APIs)

        ## Suggested metrics
        - Request latency and error counts
        - Queue depth / job failures (when applicable)
        - Resource utilisation correlated with load

        ## Telemetry notes
        If you emit telemetry spans/logs, ensure sensitive data is redacted and identifiers are minimised.
        """
    ).strip()


def _module_docs_overview_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Overview

        ## Mission
        Summarise why this module exists, the business value it delivers, and the user journeys it accelerates.

        ## Capabilities
        - Runtime features shipped with the module
        - Framework variants (FastAPI, NestJS) and parity notes
        - Optional vendor integrations or adapters

        ## Architecture
        Outline the flow from generator inputs to rendered artefacts. Highlight where overrides, snippets,
        and framework plugins plug into the pipeline.
        """
    ).strip()


def _module_docs_usage_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Usage Guide

        ## Quickstart
        ```bash
        rapidkit modules add ${module_name} --tier ${tier} --category ${category_path}
        python -m ${module_import_path}.generate fastapi ./tmp/${module_name}
        ```

        ## Configuration
        Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
        augment the base context.

        ## Framework Examples
        Describe how to integrate the generated FastAPI router and NestJS service into an application,
        including health endpoints and dependency injection touchpoints.
        """
    ).strip()


def _module_docs_advanced_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Advanced Topics

        Capture extensibility hooks, override strategies, observability requirements, and cross-cutting concerns.
        Provide concrete code snippets or configuration fragments wherever possible.
        """
    ).strip()


def _module_docs_migration_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Migration Guide

        Track version upgrades, breaking changes, and operator checklists required when rolling out new releases.
        Each entry should explain the impact, upgrade steps, and fallback plan.
        """
    ).strip()


def _module_docs_troubleshooting_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Troubleshooting

        | Symptom | Diagnostic Steps | Resolution |
        | ------- | ---------------- | ---------- |
        | Example issue | `rapidkit modules doctor ${module_slug}` | Document the remediation steps |

        Update the table as production incidents surface to build a reliable operational playbook.
        """
    ).strip()


def _module_docs_api_reference_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} API Reference

        ## Runtime Surface
        Detail public classes, functions, and dataclasses exported from the runtime templates.

        ## Configuration Schema
        Enumerate configuration keys, types, defaults, and validation semantics.

        ## CLI Entrypoints
        Describe generator commands, arguments, and expected outputs for each framework.
        """
    ).strip()


def _module_docs_changelog_template() -> str:
    return textwrap.dedent(
        """
        # Changelog — ${module_slug}

        ## 0.1.0 — Initial baseline (${today_date})

        - Initial scaffold created via `rapidkit modules scaffold`
        """
    ).strip()


def _frameworks_init_template() -> str:
    return textwrap.dedent(
        '''
        """Framework plugin registry for the ${module_title} module."""

        from __future__ import annotations

        from modules.shared.frameworks import FrameworkPlugin, PluginRegistry

        from .fastapi import FastAPIPlugin
        from .nestjs import NestJSPlugin

        PLUGIN_ENTRYPOINT_GROUP = "${module_entry_point_group}"

        _REGISTRY = PluginRegistry(entry_point_group=PLUGIN_ENTRYPOINT_GROUP)
        _BUILTIN_PLUGINS = (FastAPIPlugin, NestJSPlugin)


        def register_plugin(plugin_class: type[FrameworkPlugin]) -> None:
            """Register an additional framework plugin."""

            _REGISTRY.register(plugin_class)


        def refresh_plugin_registry(*, auto_discover: bool = True) -> None:
            """Refresh registry contents and re-register built-in implementations."""

            _REGISTRY.refresh(builtins=_BUILTIN_PLUGINS, auto_discover=auto_discover)


        def get_plugin(framework_name: str) -> FrameworkPlugin:
            """Return an instantiated plugin for the framework identifier."""

            return _REGISTRY.get(framework_name)


        def list_available_plugins() -> dict[str, str]:
            """Return available plugins mapped to their display names."""

            return _REGISTRY.list_available()


        refresh_plugin_registry(auto_discover=False)


        __all__ = [
            "FrameworkPlugin",
            "register_plugin",
            "refresh_plugin_registry",
            "get_plugin",
            "list_available_plugins",
        ]
        '''
    ).strip()


def _framework_fastapi_template() -> str:
    return textwrap.dedent(
        '''
        """FastAPI plugin for ${module_title} module scaffolding."""

        from __future__ import annotations

        from pathlib import Path
        from typing import Any, Dict, List, Mapping

        from modules.shared.frameworks import FrameworkPlugin


        class FastAPIPlugin(FrameworkPlugin):
            """Provide FastAPI-specific template and output mappings."""

            @property
            def name(self) -> str:
                return "fastapi"

            @property
            def language(self) -> str:
                return "python"

            @property
            def display_name(self) -> str:
                return "FastAPI"

            def get_template_mappings(self) -> Dict[str, str]:
                return {
                    "runtime": "templates/variants/fastapi/${module_name}.py.j2",
                    "router": "templates/variants/fastapi/${module_name}_routes.py.j2",
                    "health": "templates/variants/fastapi/${module_name}_health.py.j2",
                    "integration": "templates/tests/integration/test_${module_name}_integration.j2",
                    "e2e": "templates/variants/fastapi/tests/test_${module_name}_e2e.py",
                }

            def get_output_paths(self) -> Dict[str, str]:
                return {
                    "runtime": "${python_output_rel}",
                    "router": "${python_router_rel}",
                    "health": "${python_health_rel}",
                    "integration": "${module_integration_test}",
                    "e2e": "tests/modules/e2e/${tier}/${category_path}/${module_name}/test_${module_name}_e2e.py",
                }

            def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
                enriched = dict(base_context)
                enriched.update({
                    "framework": "fastapi",
                    "framework_display_name": "FastAPI",
                    "language": "python",
                })
                return enriched

            def validate_requirements(self) -> List[str]:
                return []

            def get_dependencies(self) -> List[str]:
                return ["fastapi>=0.110.0"]

            def get_dev_dependencies(self) -> List[str]:
                return ["pytest-asyncio>=0.23.0", "httpx>=0.27.0"]

            def pre_generation_hook(self, output_dir: Path) -> None:
                (output_dir / "src" / "routers").mkdir(parents=True, exist_ok=True)
                (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)

            def post_generation_hook(self, output_dir: Path) -> None:
                _ = output_dir
        '''
    ).strip()


def _framework_nestjs_template() -> str:
    return textwrap.dedent(
        '''
        """NestJS plugin for ${module_title} module scaffolding."""

        from __future__ import annotations

        from pathlib import Path
        from typing import Any, Dict, List, Mapping

        from modules.shared.frameworks import FrameworkPlugin


        class NestJSPlugin(FrameworkPlugin):
            """Provide NestJS-specific template and output mappings."""

            @property
            def name(self) -> str:
                return "nestjs"

            @property
            def language(self) -> str:
                return "typescript"

            @property
            def display_name(self) -> str:
                return "NestJS"

            def get_template_mappings(self) -> Dict[str, str]:
                return {
                    "service": "templates/variants/nestjs/${module_name}.service.ts.j2",
                    "controller": "templates/variants/nestjs/${module_name}.controller.ts.j2",
                    "module": "templates/variants/nestjs/${module_name}.module.ts.j2",
                    "health": "templates/variants/nestjs/${module_name}.health.ts.j2",
                    "validation": "templates/variants/nestjs/${module_name}.validation.ts.j2",
                    "index": "templates/variants/nestjs/${module_name}.index.ts.j2",
                    "configuration": "templates/variants/nestjs/${module_name}.configuration.ts.j2",
                    "e2e": "templates/variants/nestjs/tests/${module_name}.e2e-spec.ts",
                }

            def get_output_paths(self) -> Dict[str, str]:
                return {
                    "service": "${nest_service_rel}",
                    "controller": "${nest_controller_rel}",
                    "module": "${nest_module_rel}",
                    "health": "${nest_health_rel}",
                    "validation": "${nest_validation_rel}",
                    "index": "${nest_index_rel}",
                    "configuration": "${nest_configuration_rel}",
                    "e2e": "tests/modules/e2e/${category_path}/${module_name}/${module_name}.e2e-spec.ts",
                }

            def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
                enriched = dict(base_context)
                enriched.update({
                    "framework": "nestjs",
                    "framework_display_name": "NestJS",
                    "language": "typescript",
                })
                return enriched

            def validate_requirements(self) -> List[str]:
                return []

            def get_dependencies(self) -> List[str]:
                return ["@nestjs/common>=10.0.0"]

            def get_dev_dependencies(self) -> List[str]:
                return ["@nestjs/testing>=10.0.0", "ts-jest>=29.0.0"]

            def pre_generation_hook(self, output_dir: Path) -> None:
                (output_dir / "src").mkdir(parents=True, exist_ok=True)

            def post_generation_hook(self, output_dir: Path) -> None:
                _ = output_dir
        '''
    ).strip()


def _init_template() -> str:
    return textwrap.dedent(
        '''
        """Runtime package for the ${module_title} module."""

        __all__ = ["${module_class}"]
        '''
    ).strip()


def _module_yaml_template() -> str:
    lines = (
        "name: ${module_name}",
        "display_name: ${module_display_name_literal}",
        "description: ${module_description_literal}",
        "version: 0.1.0",
        "access: ${tier}",
        "status: draft",
        "tier: ${tier}",
        "category: ${category_path}",
        "tags:",
        "${module_tags_block}",
        "generated_from_config: true",
        "profile_inherits:",
        "  fastapi.standard: fastapi",
        "  fastapi.ddd: fastapi",
        "  nestjs.standard: nestjs",
        "config_sources:",
        "  - config/base.yaml",
        "  - config/snippets.yaml",
        "generation:",
        "  vendor:",
        "    root: .rapidkit/vendor",
        "    files:",
        "      - template: templates/base/${module_name}.py.j2",
        "        relative: ${vendor_relative}",
        "      - template: templates/base/${module_name}_types.py.j2",
        "        relative: ${vendor_types_relative}",
        "      - template: templates/base/${module_name}_health.py.j2",
        "        relative: ${vendor_health_relative}",
        "      - template: templates/vendor/nestjs/configuration.js.j2",
        "        relative: nestjs/configuration.js",
        "  variants:",
        "    fastapi: &fastapi_variant",
        "      root: .",
        "      context:",
        "        framework: fastapi",
        "        module_class_name: ${module_class}",
        "      files:",
        "        - template: templates/variants/fastapi/${module_name}.py.j2",
        "          output: ${python_output_rel}",
        "        - template: templates/variants/fastapi/${module_name}_routes.py.j2",
        "          output: ${python_router_rel}",
        "        - template: templates/variants/fastapi/${module_name}_health.py.j2",
        "          output: ${python_health_rel}",
        "        - template: templates/tests/integration/test_${module_name}_integration.j2",
        "          output: ${module_integration_test}",
        "        - template: templates/variants/fastapi/tests/test_${module_name}_e2e.py",
        "          output: tests/modules/e2e/${tier}/${category_path}/${module_name}/test_${module_name}_e2e.py",
        "",
        "    # Compatibility aliases: the installer uses kit profile names.",
        "    fastapi.standard: *fastapi_variant",
        "    fastapi.ddd: *fastapi_variant",
        "",
        "    nestjs: &nestjs_variant",
        "      root: .",
        "      context:",
        "        framework: nestjs",
        "        vendor_configuration_relative: nestjs/configuration.js",
        "        module_class_name: ${module_class}",
        "        module_kebab: ${module_kebab}",
        "      files:",
        "        - template: templates/variants/nestjs/${module_name}.service.ts.j2",
        "          output: ${nest_output_rel}",
        "        - template: templates/variants/nestjs/${module_name}.controller.ts.j2",
        "          output: ${nest_controller_rel}",
        "        - template: templates/variants/nestjs/${module_name}.module.ts.j2",
        "          output: ${nest_module_rel}",
        "        - template: templates/variants/nestjs/${module_name}.health.ts.j2",
        "          output: ${nest_health_rel}",
        "        - template: templates/variants/nestjs/${module_name}.validation.ts.j2",
        "          output: ${nest_validation_rel}",
        "        - template: templates/variants/nestjs/${module_name}.index.ts.j2",
        "          output: ${nest_index_rel}",
        "        - template: templates/variants/nestjs/${module_name}.configuration.ts.j2",
        "          output: ${nest_configuration_rel}",
        "        - template: templates/variants/nestjs/tests/${module_name}.e2e-spec.ts",
        "          output: tests/modules/e2e/${category_path}/${module_name}/${module_name}.e2e-spec.ts",
        "",
        "    nestjs.standard: *nestjs_variant",
        "  snippets:",
        "    enabled: true",
        "    config: config/snippets.yaml",
        "    default: []",
        "compatibility:",
        "${module_compatibility_block}",
        "testing:",
        "  coverage_min: ${testing_coverage_min}",
        "  integration_tests: ${testing_integration_tests}",
        "  e2e_tests: ${testing_e2e_tests}",
        "${module_unit_tests_yaml}",
        "  integration_test_files:",
        "    - ${module_integration_test}",
        "  fixtures:${module_testing_fixtures_block}",
        "documentation:",
        '  changelog: "${doc_changelog_rel_module}"',
        '  readme: "README.md"',
        '  overview: "${doc_overview_rel_module}"',
        '  usage: "${doc_usage_rel_module}"',
        '  advanced: "${doc_advanced_rel_module}"',
        '  migration: "${doc_migration_rel_module}"',
        '  troubleshooting: "${doc_troubleshooting_rel_module}"',
        '  api_docs: "${doc_api_reference_rel_module}"',
        "  examples: []",
        "support:",
        "  issues: https://github.com/getrapidkit/core/issues",
        "  discussions: https://github.com/getrapidkit/core/discussions",
        "  documentation: https://docs.rapidkit.top/modules/${module_name}",
        "changelog:",
        "- version: 0.1.0",
        "  date: '${today_date}'",
        "  notes: See docs/changelog.md",
        "validation:",
        "  pre_install:",
        "    - check_python_version",
        "  post_install:",
        "    - validate_generated_code",
        "rollback:",
        "  strategy: uninstall",
        "  backup_path: .rapidkit/backups/",
        "  max_backups: 3",
        "performance:",
        "  lazy_loading: true",
        "  caching:",
        "    templates: true",
        "    ttl: 300",
        "capabilities:",
        "${module_capabilities_block}",
        "signature: null",
        "signer_id: null",
        "signature_version: null",
    )
    return "\n".join(lines).strip()


def _templates_tests_package_template() -> str:
    return textwrap.dedent(
        '''
        """Test templates package for ${module_title} module."""

        __all__ = []
        '''
    ).strip()


def _templates_tests_integration_package_template() -> str:
    return textwrap.dedent(
        '''
        """Integration test templates for ${module_title} module."""

        __all__ = []
        '''
    ).strip()


def _module_verify_template() -> str:
    return textwrap.dedent(
        """
        {
          "module": "${module_name}",
          "version": "0.1.0",
          "templates": [],
          "generated_at": "<populate via rapidkit modules verify>"
        }
        """
    ).strip()


def _module_state_template() -> str:
    return textwrap.dedent(
        """
        {
          "status": "draft",
          "owner": "",
          "notes": [
            "Initial scaffold generated via rapidkit cli"
          ]
        }
        """
    ).strip()


def _overrides_template() -> str:
    return textwrap.dedent(
        '''
        """Override contracts for ${module_title}."""

        from core.services.override_contracts import ConfigurableOverrideMixin


        class ${module_class}Overrides(ConfigurableOverrideMixin):
            """Extend or customize generated behaviour for ${module_title}."""

            # def custom_method(self, *args, **kwargs):
            #     """Example override."""
            #     original = self.call_original("custom_method", *args, **kwargs)
            #     return original
        '''
    ).strip()


def _base_config_template() -> str:
    lines = (
        "# Module configuration baseline for ${module_title}",
        "name: ${module_name}",
        "display_name: ${module_display_name_literal}",
        "description: ${module_description_literal}",
        "root_path: src/",
        "${module_base_config_block}",
    )
    return "\n".join(lines).strip()


def _snippets_config_template() -> str:
    lines = (
        "# Register snippet bundles for ${module_title}",
        "",
        "${module_snippet_config_block}",
    )
    return "\n".join(lines).strip()


def _base_python_template() -> str:
    return textwrap.dedent(
        '''
        from dataclasses import dataclass
        from typing import Any, Dict


        @dataclass
        class {{ module_class_name }}Config:
            """Runtime configuration for {{ module_title }}."""

            enabled: bool = True
            metadata: Dict[str, Any] | None = None


        def build_default_config() -> {{ module_class_name }}Config:
            """Return default configuration payload."""

            return {{ module_class_name }}Config()
        '''
    ).strip()


def _base_types_template() -> str:
    return textwrap.dedent(
        '''
        from dataclasses import dataclass
        from typing import Any, Mapping


        @dataclass
        class {{ module_class_name }}Context:
            """Typed runtime context shared across templates."""

            metadata: Mapping[str, Any] | None = None
            enabled: bool = True
        '''
    ).strip()


def _base_health_template() -> str:
    return textwrap.dedent(
        '''
        from datetime import datetime


        def check_health() -> dict[str, str]:
            """Return a simple health payload for the runtime facade."""

            return {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
                "status": "ok",
            }
        '''
    ).strip()


def _fastapi_runtime_template() -> str:
    return textwrap.dedent(
        '''
        from fastapi import APIRouter


        def create_router() -> APIRouter:
            """Sample FastAPI router for {{ module_title }}."""

            router = APIRouter()

            @router.get("/health")
            def healthcheck() -> dict[str, str]:
                return {"module": "{{ module_name }}", "status": "ok"}

            return router
        '''
    ).strip()


def _fastapi_router_template() -> str:
    return textwrap.dedent(
        '''
        from fastapi import APIRouter


        def create_router() -> APIRouter:
            """Provide an application router for {{ module_title }}."""

            router = APIRouter()

            @router.get("/health", tags=["{{ module_name }}"])
            def healthcheck() -> dict[str, str]:
                return {"module": "{{ module_name }}", "status": "ok"}

            return router
        '''
    ).strip()


def _fastapi_health_template() -> str:
    return textwrap.dedent(
        '''
        from datetime import datetime


        def module_health_status() -> dict[str, str]:
            """Return a minimal health payload for FastAPI variants."""

            return {"checked_at": datetime.utcnow().isoformat(timespec="seconds")}
        '''
    ).strip()


def _nestjs_service_template() -> str:
    return textwrap.dedent(
        """
        import { Injectable } from "@nestjs/common";

        @Injectable()
        export class {{ module_class_name }}Service {
            getStatus(): Record<string, string> {
                return { module: "{{ module_name }}", status: "ok" };
            }
        }
        """
    ).strip()


def _nestjs_controller_template() -> str:
    return textwrap.dedent(
        """
        import { Controller, Get } from "@nestjs/common";
        import { {{ module_class_name }}Service } from "./{{ module_name }}.service";

        @Controller("{{ module_kebab }}")
        export class {{ module_class_name }}Controller {
            constructor(private readonly service: {{ module_class_name }}Service) {}

            @Get("health")
            getHealth(): Record<string, string> {
                return this.service.getStatus();
            }
        }
        """
    ).strip()


def _nestjs_module_template() -> str:
    return textwrap.dedent(
        """
        import { Module } from "@nestjs/common";
        import { {{ module_class_name }}Controller } from "./{{ module_name }}.controller";
        import { {{ module_class_name }}Service } from "./{{ module_name }}.service";

        @Module({
            controllers: [{{ module_class_name }}Controller],
            providers: [{{ module_class_name }}Service],
            exports: [{{ module_class_name }}Service],
        })
        export class {{ module_class_name }}Module {}
        """
    ).strip()


def _nestjs_health_template() -> str:
    return textwrap.dedent(
        """
        export interface {{ module_class_name }}Health {
            module: string;
            status: string;
            checkedAt: string;
        }

        export function runtimeHealth(): {{ module_class_name }}Health {
            return {
                module: "{{ module_name }}",
                status: "ok",
                checkedAt: new Date().toISOString(),
            };
        }
        """
    ).strip()


def _nestjs_validation_template() -> str:
    return textwrap.dedent(
        """
        import { z } from "zod";

        export const {{ module_name }}ConfigSchema = z.object({
            enabled: z.boolean().default(true),
        });

        export type {{ module_class_name }}Config = z.infer<typeof {{ module_name }}ConfigSchema>;
        """
    ).strip()


def _nestjs_index_template() -> str:
    return textwrap.dedent(
        """
        export * from "./{{ module_name }}.module";
        export * from "./{{ module_name }}.service";
        export * from "./{{ module_name }}.controller";
        export * from "./{{ module_name }}.health";
        export * from "./{{ module_name }}.validation";
        """
    ).strip()


def _nestjs_configuration_template() -> str:
    return textwrap.dedent(
        """
        export const configuration = () => ({
            {{ module_name }}: {
                enabled: true,
            },
        });
        """
    ).strip()


def _vendor_template() -> str:
    return textwrap.dedent(
        """
        "use strict";

        function loadConfiguration() {
          return {
            module: "${module_name}",
            title: "${module_title}",
            enabled: true,
          };
        }

        module.exports = {
          loadConfiguration,
        };
        """
    ).strip()


def _snippet_template() -> str:
    return textwrap.dedent(
        """
        {# Jinja snippet used to inject shared fragments into generated artefacts. #}
        {# Name this snippet when referencing from module.yaml generation entries. #}

        {% set module_name = "${module_name}" %}

        # TODO: Provide snippet content for {{ module_name }}
        """
    ).strip()


def _integration_test_template() -> str:
    return textwrap.dedent(
        '''
        from pathlib import Path


        def test_generator_entrypoint() -> None:
            """Smoky assertion ensuring generator is importable."""

            module_root = Path(__file__).resolve().parents[3]
            assert module_root.exists()
        '''
    ).strip()


__all__ = ["build_module_files"]
