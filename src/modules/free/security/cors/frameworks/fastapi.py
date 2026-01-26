# pyright: reportMissingImports=false
"""FastAPI framework plugin for the Cors module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim
from modules.shared.utils.health_specs import build_standard_health_spec


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-oriented Cors integrations."""

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
            "runtime_wrapper": "templates/variants/fastapi/cors.py.j2",
            "shared_types": "templates/base/cors_types.py.j2",
            "http_routes": "templates/variants/fastapi/cors_routes.py.j2",
            "integration_test": "templates/tests/integration/test_cors_integration.j2",
            "config_yaml": "templates/variants/fastapi/cors_config.yaml.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime_wrapper": "src/modules/free/security/cors/cors.py",
            "shared_types": "src/modules/free/security/cors/cors_types.py",
            "http_routes": "src/modules/free/security/cors/routers/cors.py",
            "integration_test": "tests/modules/integration/security/test_cors_integration.py",
            "config_yaml": "config/security/cors.yaml",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_relative_path"),
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "module_class_name": "Cors",
            "module_kebab": "cors",
            "config_output_relative": base_context.get("python_config_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        (output_dir / "src" / "modules" / "free" / "security" / "cors" / "routers").mkdir(
            parents=True,
            exist_ok=True,
        )
        (output_dir / "tests" / "modules" / "integration" / "security").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "config" / "security").mkdir(parents=True, exist_ok=True)
        try:
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)
        except (RuntimeError, OSError):
            pass

        ensure_health_package(
            output_dir,
            extra_imports=[("src.health.cors", "register_cors_health")],
        )

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "fastapi": "https://fastapi.tiangolo.com/",
            "cors": "https://fastapi.tiangolo.com/tutorial/cors/",
        }

    def get_dependencies(self) -> List[str]:
        return [
            "fastapi>=0.111.0,<1.0",
            "starlette>=0.37.2,<1.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.3.0",
            "httpx>=0.27.0",
        ]


class FastAPIStandardPlugin(FastAPIPlugin):
    """Alias plugin used when kits reference the fastapi.standard profile."""

    @property
    def name(self) -> str:  # noqa: D401 - inherits behaviour from base class
        return "fastapi.standard"

    @property
    def display_name(self) -> str:
        return "FastAPI (standard kit)"


class FastAPIDDDPlugin(FastAPIPlugin):
    """Alias plugin mapping fastapi.ddd to the canonical FastAPI implementation."""

    @property
    def name(self) -> str:  # noqa: D401
        return "fastapi.ddd"

    @property
    def display_name(self) -> str:
        return "FastAPI (DDD kit)"
