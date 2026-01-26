"""NestJS deployment plugin generating shared deployment assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS-oriented deployment tooling."""

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
            "makefile": "templates/variants/nestjs/Makefile.j2",
            "dockerfile": "templates/variants/nestjs/Dockerfile.j2",
            "dockerignore": "templates/variants/nestjs/.dockerignore.j2",
            "docker_compose": "templates/variants/nestjs/docker-compose.yml.j2",
            "service": "templates/variants/nestjs/deployment.service.ts.j2",
            "controller": "templates/variants/nestjs/deployment.controller.ts.j2",
            "module": "templates/variants/nestjs/deployment.module.ts.j2",
            "configuration": "templates/variants/nestjs/deployment.configuration.ts.j2",
            "compose_base": "templates/base/docker-compose.base.yml.j2",
            "compose_local": "templates/variants/nestjs/docker-compose.local.yml.j2",
            "compose_production": "templates/variants/nestjs/docker-compose.production.yml.j2",
            "ci": "templates/variants/nestjs/ci.yml.j2",
            # Health adapter templates moved to vendor payload; final project health
            # artefacts will be copied from .rapidkit/vendor if available.
            "integration_tests": "templates/tests/integration/deployment.integration.spec.ts.j2",
            "e2e_tests": "templates/variants/nestjs/tests/deployment.e2e-spec.ts",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "makefile": "Makefile",
            "dockerfile": "Dockerfile",
            "dockerignore": ".dockerignore",
            "docker_compose": "docker-compose.yml",
            "service": "src/modules/free/essentials/deployment/deployment.service.ts",
            "controller": "src/modules/free/essentials/deployment/deployment.controller.ts",
            "module": "src/modules/free/essentials/deployment/deployment.module.ts",
            "configuration": "src/modules/free/essentials/deployment/deployment.configuration.ts",
            "compose_base": "deploy/compose/base.yml",
            "compose_local": "deploy/compose/local.yml",
            "compose_production": "deploy/compose/production.yml",
            "ci": ".github/workflows/ci.yml",
            "health_controller": "src/health/deployment-health.controller.ts",
            "health_module": "src/health/deployment-health.module.ts",
            "integration_tests": "tests/modules/integration/essentials/deployment/deployment.integration.spec.ts",
            "e2e_tests": "tests/modules/e2e/free/essentials/deployment/deployment.e2e-spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        context = dict(base_context)
        context.update(
            framework="nestjs",
            framework_display_name="NestJS",
            language="typescript",
            runtime="node",
        )
        context.setdefault("node_version", "20.19.6")
        context.setdefault("include_postgres", True)
        context.setdefault("include_ci", True)
        context.setdefault("package_manager", "npm")
        context.setdefault("package_manager_command", context.get("package_manager", "npm"))
        slug_value = str(context.get("module_slug") or context.get("module_name") or "deployment")
        module_segment = slug_value.split("/")[-1]
        context.setdefault("module_kebab", module_segment.replace("_", "-"))

        return context

    def validate_requirements(self) -> List[str]:
        # For code generation, we don't require external tools to be installed
        # The generated code will require Node.js/npm when used
        # But generation itself only needs the templates to be available
        errors: List[str] = []
        return errors

    def pre_generation_hook(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
        (output_dir / "deploy" / "compose").mkdir(parents=True, exist_ok=True)
        (output_dir / "src/modules/free/essentials/deployment").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests/modules/integration/essentials/deployment").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "tests/modules/e2e/free/essentials/deployment").mkdir(
            parents=True, exist_ok=True
        )

        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:
        _ = output_dir

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://docs.nestjs.com/",
            "overview": "https://docs.nestjs.com/first-steps",
            "deployment": "https://docs.nestjs.com/recipes/deployment",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "service": {
                "import_path": "src/app.module",
                "cli": "nest",
            }
        }


class NestJSStandardPlugin(NestJSPlugin):
    """Alias plugin so nestjs.standard reuses the canonical NestJS implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias maps to canonical NestJS plugin
        return "nestjs.standard"

    @property
    def display_name(self) -> str:
        return "NestJS (standard kit)"
