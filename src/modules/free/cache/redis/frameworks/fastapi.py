# pyright: reportMissingImports=false

"""FastAPI framework plugin for the Redis module."""

from __future__ import annotations

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
    """Plugin for generating FastAPI-oriented Redis integration."""

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
            "client": "templates/variants/fastapi/redis_client.py.j2",
            "package": "templates/variants/fastapi/redis_package_init.py.j2",
            "facade": "templates/variants/fastapi/redis_module.py.j2",
            "routes": "templates/variants/fastapi/redis_routes.py.j2",
            "config": "templates/variants/fastapi/redis_config.yaml.j2",
            "integration_test": "templates/tests/integration/test_redis_integration.j2",
            "e2e_test": "templates/variants/fastapi/tests/test_redis_e2e.py",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "client": "src/modules/free/cache/redis/client.py",
            "package": "src/modules/free/cache/redis/__init__.py",
            "facade": "src/modules/free/cache/redis/redis.py",
            "routes": "src/modules/free/cache/redis/routers/redis.py",
            "config": "config/cache/redis.yaml",
            "integration_test": "tests/modules/free/cache/redis/test_redis_integration.py",
            "e2e_test": "tests/modules/e2e/free/cache/redis/test_redis_e2e.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "vendor_client_relative": base_context.get("rapidkit_vendor_client_relative"),
            "vendor_package_relative": base_context.get("rapidkit_vendor_package_relative"),
        }

    def validate_requirements(self) -> List[str]:
        # Generation itself only needs templates; runtime dependencies are declared separately.
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "cache" / "redis"
        base.mkdir(parents=True, exist_ok=True)
        (base / "routers").mkdir(parents=True, exist_ok=True)
        (output_dir / "config" / "cache").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "cache" / "redis").mkdir(
            parents=True, exist_ok=True
        )
        spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
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

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://fastapi.tiangolo.com/",
            "redis": "https://redis.io/docs/clients/python/",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "redis": {
                "url": "redis://localhost:6379/0",
                "preconnect": False,
                "connectRetries": 3,
                "connectBackoffBase": 0.5,
                "ttl": 3600,
            }
        }

    def get_dependencies(self) -> List[str]:
        return [
            "redis>=5.0.0,<6.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.3.0",
            "pytest-asyncio>=0.25.0",
            "httpx>=0.27.0",
        ]


class FastAPIStandardPlugin(FastAPIPlugin):
    """Alias plugin mapping fastapi.standard to the canonical FastAPI implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias reroutes to FastAPI plugin
        return "fastapi.standard"

    @property
    def display_name(self) -> str:
        return "FastAPI (standard kit)"


class FastAPIDDDPlugin(FastAPIPlugin):
    """Alias plugin mapping fastapi.ddd to the canonical FastAPI implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias reroutes to FastAPI plugin
        return "fastapi.ddd"

    @property
    def display_name(self) -> str:
        return "FastAPI (DDD kit)"
