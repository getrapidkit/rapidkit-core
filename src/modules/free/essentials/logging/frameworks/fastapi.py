# pyright: reportMissingImports=false

"""FastAPI framework plugin for the Logging module."""

from __future__ import annotations

import importlib.util
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import (
    ensure_health_package,
    ensure_vendor_health_shim,
    synchronize_health_package,
)
from modules.shared.utils.health_specs import build_standard_health_spec


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-specific code."""

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
            "module": "templates/variants/fastapi/logging.py.j2",
            "routes": "templates/variants/fastapi/logging_routes.py.j2",
            "health_router": "templates/base/logging_health.py.j2",
            "integration_tests": "templates/tests/integration/test_logging_integration.j2",
            "e2e_tests": "templates/variants/fastapi/tests/test_logging_e2e.py",
            "config": "templates/variants/fastapi/logging_config.yaml.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "module": "src/modules/free/essentials/logging/logging.py",
            "routes": "src/modules/free/essentials/logging/routers/logging.py",
            "integration_tests": "tests/modules/free/essentials/logging/test_logging_integration.py",
            "e2e_tests": "tests/modules/e2e/free/essentials/logging/test_logging_e2e.py",
            "health_router": "src/health/logging.py",
            "config": "src/modules/free/essentials/logging/config/logging.yaml",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "include_fastapi_middleware": True,
            "module_kebab": (
                str(base_context.get("module_slug") or base_context.get("module_name") or "logging")
                .split("/")[-1]
                .replace("_", "-")
            ),
        }

    def validate_requirements(self) -> List[str]:
        errors: List[str] = []
        if importlib.util.find_spec("fastapi") is None:
            errors.append("FastAPI is required for the logging module fastapi variant")
        if importlib.util.find_spec("starlette") is None:
            errors.append("Starlette must be installed to enable request context middleware")
        return errors

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "essentials" / "logging"
        (base / "routers").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "essentials" / "logging").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "tests" / "modules" / "e2e" / "free" / "essentials" / "logging").mkdir(
            parents=True, exist_ok=True
        )
        (base / "config").mkdir(parents=True, exist_ok=True)
        # Generate a vendor-backed shim for logging (if configured) then ensure
        # the aggregator health package is updated to import the shim.
        # Best-effort generation: don't fail the generator if vendor shim cannot be
        # materialised in the local environment.
        with suppress(RuntimeError, OSError):
            module_root = Path(__file__).resolve().parents[1]
            spec = build_standard_health_spec(module_root)
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[("src.health.logging", "register_logging_health")],
        )
        synchronize_health_package(output_dir)

    def post_generation_hook(self, _output_dir: Path) -> None:
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://fastapi.tiangolo.com/",
            "settings": "https://fastapi.tiangolo.com/tutorial/settings/",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "app": {
                "title": "Logging with FastAPI",
                "version": "0.1.0",
            }
        }

    def get_dependencies(self) -> List[str]:
        return [
            "fastapi>=0.119.0",
            "starlette>=0.37.2",
            "python-json-logger>=2.0.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.3.0",
            "httpx>=0.28.0",
            "pytest-asyncio>=1.2.0",
        ]


class FastAPIStandardPlugin(FastAPIPlugin):
    """Alias plugin so kits targeting fastapi.standard reuse FastAPI behaviour."""

    @property
    def name(self) -> str:  # noqa: D401 - same behaviour with different name
        return "fastapi.standard"

    @property
    def display_name(self) -> str:
        return "FastAPI (standard kit)"


class FastAPIDDDPlugin(FastAPIPlugin):
    """Alias plugin for fastapi.ddd profile."""

    @property
    def name(self) -> str:  # noqa: D401
        return "fastapi.ddd"

    @property
    def display_name(self) -> str:
        return "FastAPI (DDD kit)"
