"""FastAPI deployment plugin generating shared deployment assets."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import importlib.util
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping, cast

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import (
    ensure_health_package,
    ensure_vendor_health_shim,
    synchronize_health_package,
)
from modules.shared.utils.health_specs import build_standard_health_spec

_VERSION_COMPONENTS = 3


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-oriented deployment tooling."""

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
            "makefile": "templates/variants/fastapi/Makefile.j2",
            "dockerfile": "templates/variants/fastapi/Dockerfile.j2",
            "dockerignore": "templates/variants/fastapi/.dockerignore.j2",
            "docker_compose": "templates/variants/fastapi/docker-compose.yml.j2",
            "runtime": "templates/variants/fastapi/deployment.py.j2",
            "routes": "templates/variants/fastapi/deployment_routes.py.j2",
            "health_router": "templates/base/deployment_health.py.j2",
            "compose_base": "templates/base/docker-compose.base.yml.j2",
            "compose_local": "templates/variants/fastapi/docker-compose.local.yml.j2",
            "compose_production": "templates/variants/fastapi/docker-compose.production.yml.j2",
            "ci": "templates/variants/fastapi/ci.yml.j2",
            "integration_tests": "templates/tests/integration/test_deployment_integration.j2",
            "e2e_tests": "templates/variants/fastapi/tests/test_deployment_e2e.py",
            "config": "templates/variants/fastapi/deployment_config.yaml.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "makefile": "Makefile",
            "dockerfile": "Dockerfile",
            "dockerignore": ".dockerignore",
            "docker_compose": "docker-compose.yml",
            "runtime": "src/modules/free/essentials/deployment/deployment.py",
            "routes": "src/modules/free/essentials/deployment/routers/deployment.py",
            "compose_base": "deploy/compose/base.yml",
            "compose_local": "deploy/compose/local.yml",
            "compose_production": "deploy/compose/production.yml",
            "ci": ".github/workflows/ci.yml",
            # FastAPI projects use the shared vendor-backed shim under src/health/<module>.py.
            "health_router": "src/health/deployment.py",
            "integration_tests": "tests/modules/free/essentials/deployment/test_deployment_integration.py",
            "e2e_tests": "tests/modules/e2e/free/essentials/deployment/test_deployment_e2e.py",
            "config": "src/modules/free/essentials/deployment/config/deployment.yaml",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        context = dict(base_context)
        context.update(
            framework="fastapi",
            framework_display_name="FastAPI",
            language="python",
            runtime="python",
        )
        context.setdefault("include_ci", True)
        context.setdefault("include_postgres", True)
        context.setdefault("python_version", "3.10")
        slug_value = str(context.get("module_slug") or context.get("module_name") or "deployment")
        module_segment = slug_value.split("/")[-1]
        context.setdefault("module_kebab", module_segment.replace("_", "-"))

        return context

    def validate_requirements(self) -> List[str]:
        errors: List[str] = []
        min_python = (3, 10)
        min_fastapi_version = (0, 119, 0)

        if sys.version_info < min_python:
            errors.append("FastAPI plugins require Python 3.10 or newer.")

        version_str: str | None = None
        fastapi_available = False

        if "fastapi" in sys.modules:
            fastapi_available = True
            version_str = getattr(sys.modules["fastapi"], "__version__", None)
        else:
            try:
                spec = importlib.util.find_spec("fastapi")
            except ValueError:
                spec = None
            if spec is not None:
                fastapi_available = True

        if fastapi_available and version_str is None:
            try:
                version_str = importlib_metadata.version("fastapi")
            except importlib_metadata.PackageNotFoundError:
                version_str = None

        if not fastapi_available:
            return errors

        if version_str:
            version_tuple = self._normalise_version(version_str)
            if version_tuple < min_fastapi_version:
                errors.append(
                    "FastAPI version {found} is too old. Upgrade with: pip install 'fastapi>=0.119.0'".format(
                        found=version_str
                    )
                )

        return errors

    @staticmethod
    def _normalise_version(version: str) -> tuple[int, int, int]:
        parts: List[int] = []
        for raw_part in version.split("."):
            digits = "".join(ch for ch in raw_part if ch.isdigit())
            if not digits:
                break
            parts.append(int(digits))

        while len(parts) < _VERSION_COMPONENTS:
            parts.append(0)

        return cast(tuple[int, int, int], tuple(parts[:_VERSION_COMPONENTS]))

    def get_dependencies(self) -> List[str]:
        return [
            "fastapi>=0.119.0",
            "uvicorn[standard]>=0.37.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest-asyncio>=0.23.0",
            "httpx>=0.28.0",
            "fastapi[all]>=0.119.0",
        ]

    def pre_generation_hook(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
        (output_dir / "deploy" / "compose").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests/modules/free/essentials/deployment").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests/modules/e2e/free/essentials/deployment").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "src/modules/free/essentials/deployment").mkdir(parents=True, exist_ok=True)
        (output_dir / "src/modules/free/essentials/deployment/routers").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "src/modules/free/essentials/deployment/config").mkdir(
            parents=True, exist_ok=True
        )
        # Try to generate a vendor-backed shim for the module's health (uniform shim
        # used across all modules), then ensure the aggregator health package is present.
        # Best-effort: don't fail generation if vendor content can't be materialised.
        module_root = Path(__file__).resolve().parents[1]
        spec = build_standard_health_spec(module_root)
        with suppress(RuntimeError, OSError):
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[
                (
                    f"src.health.{spec.module_name}",
                    f"register_{spec.module_name}_health",
                )
            ],
        )
        synchronize_health_package(output_dir)

    def post_generation_hook(self, output_dir: Path) -> None:
        _ = output_dir

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://fastapi.tiangolo.com/",
            "tutorial": "https://fastapi.tiangolo.com/tutorial/",
            "deployment": "https://fastapi.tiangolo.com/deployment/",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "app": {
                "title": "RapidKit FastAPI Service",
                "version": "0.1.0",
                "description": "Sample FastAPI application generated by RapidKit",
            }
        }


class FastAPIStandardPlugin(FastAPIPlugin):
    """Alias plugin for fastapi.standard kit consumers."""

    @property
    def name(self) -> str:  # noqa: D401 - alias maps to canonical FastAPI plugin
        return "fastapi.standard"

    @property
    def display_name(self) -> str:
        return "FastAPI (standard kit)"


class FastAPIDDDPlugin(FastAPIPlugin):
    """Alias plugin mapping fastapi.ddd to the base FastAPI implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias maps to canonical FastAPI plugin
        return "fastapi.ddd"

    @property
    def display_name(self) -> str:
        return "FastAPI (DDD kit)"
