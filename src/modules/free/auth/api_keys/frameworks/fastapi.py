"""FastAPI framework plugin for the Api Keys module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim
from modules.shared.utils.health_specs import build_standard_health_spec


class FastAPIPlugin(FrameworkPlugin):
    """Plugin exposing FastAPI-specific integrations for Api Keys."""

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
            "runtime": "templates/variants/fastapi/api_keys.py.j2",
            "routes": "templates/variants/fastapi/api_keys_routes.py.j2",
            "config": "templates/variants/fastapi/api_keys_config.yaml.j2",
            "integration_test": "templates/tests/integration/test_api_keys_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime": "src/modules/free/auth/api_keys/api_keys.py",
            "routes": "src/modules/free/auth/api_keys/routers/api_keys.py",
            "config": "config/api_keys.yaml",
            "integration_test": "tests/modules/integration/auth/api_keys/test_api_keys_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_runtime_relative"),
        }

    def validate_requirements(self) -> List[str]:
        # Runtime dependencies are declared in the generated project requirements.
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "auth" / "api_keys"
        (module_root / "routers").mkdir(parents=True, exist_ok=True)
        (output_dir / "config").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "auth" / "api_keys").mkdir(
            parents=True, exist_ok=True
        )
        module_root = Path(__file__).resolve().parents[1]
        spec = build_standard_health_spec(module_root)
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
            "security": "https://fastapi.tiangolo.com/advanced/security/",
        }


__all__ = ["FastAPIPlugin"]
