"""FastAPI framework plugin for the Db Mongo module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim
from modules.shared.utils.health_specs import build_standard_health_spec


class FastAPIPlugin(FrameworkPlugin):
    """Plugin exposing FastAPI-specific integrations for Db Mongo."""

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
            "runtime": "templates/variants/fastapi/db_mongo.py.j2",
            "routes": "templates/variants/fastapi/db_mongo_routes.py.j2",
            "config": "templates/variants/fastapi/db_mongo_config.yaml.j2",
            "integration_tests": "templates/tests/integration/test_db_mongo_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime": "src/modules/free/database/db_mongo/db_mongo.py",
            "routes": "src/modules/free/database/db_mongo/routers/db_mongo.py",
            "config": "config/database/db_mongo.yaml",
            "integration_tests": "tests/modules/integration/database/test_db_mongo_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_runtime_relative"),
            "health_timeout_ms": base_context.get("default_health_timeout_ms"),
            "config_output_relative": base_context.get("python_config_relative"),
            "integration_test_relative": base_context.get("python_test_relative"),
        }

    def validate_requirements(self) -> list[str]:  # noqa: D401
        """FastAPI requires Starlette/FastAPI packages at generation time."""

        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "database" / "db_mongo"
        module_root.mkdir(parents=True, exist_ok=True)
        (module_root / "routers").mkdir(parents=True, exist_ok=True)
        (output_dir / "config" / "database").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "database").mkdir(
            parents=True, exist_ok=True
        )
        spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
        with suppress(RuntimeError, OSError):
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            include_database=True,
            extra_imports=[
                (f"src.health.{spec.module_name}", f"register_{spec.module_name}_health")
            ],
        )

    def get_dependencies(self) -> list[str]:
        return [
            "fastapi>=0.111.0",
            "motor>=3.4.0",
        ]

    def get_dev_dependencies(self) -> list[str]:
        return ["pytest>=8.3.0", "httpx>=0.28.0"]


__all__ = ["FastAPIPlugin"]
