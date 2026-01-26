"""FastAPI framework plugin for the Observability Core module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package


class FastAPIPlugin(FrameworkPlugin):
    """Plugin exposing FastAPI-specific integrations for Observability Core."""

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
            "runtime": "templates/variants/fastapi/observability_core.py.j2",
            "routes": "templates/variants/fastapi/observability_core_routes.py.j2",
            "config": "templates/variants/fastapi/observability_core_config.yaml.j2",
            "integration_tests": "templates/tests/integration/test_observability_core_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime": "src/modules/free/observability/core/observability_core.py",
            "routes": "src/modules/free/observability/core/routers/observability_core.py",
            "config": "config/observability/observability_core.yaml",
            "integration_tests": "tests/modules/integration/observability/test_observability_core_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_runtime_relative"),
            "metrics_endpoint": base_context.get("metrics_endpoint", "/metrics"),
            "config_output_relative": base_context.get("fastapi_config_relative"),
            "integration_test_relative": base_context.get("fastapi_test_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "observability" / "core"
        (base).mkdir(parents=True, exist_ok=True)
        (base / "routers").mkdir(parents=True, exist_ok=True)
        (output_dir / "config" / "observability").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "observability").mkdir(
            parents=True, exist_ok=True
        )
        # Best-effort: try to generate vendor-backed health shim for observability
        from modules.shared.utils.health import ensure_vendor_health_shim
        from modules.shared.utils.health_specs import build_standard_health_spec

        spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
        with suppress(RuntimeError, OSError):
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[
                (f"src.health.{spec.module_name}", f"register_{spec.module_name}_health")
            ],
        )

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_dependencies(self) -> List[str]:
        return [
            "fastapi>=0.111.0",
            "pydantic>=2.5.0",
            "prometheus-client>=0.20.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.3.0",
            "pytest-asyncio>=0.25.0",
            "httpx>=0.28.0",
        ]

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://fastapi.tiangolo.com/",
            "instrumentation": "https://fastapi.tiangolo.com/advanced/events/",
        }


__all__ = ["FastAPIPlugin"]
