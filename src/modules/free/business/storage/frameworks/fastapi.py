# pyright: reportMissingImports=false
"""FastAPI framework plugin for the File Storage module."""

from __future__ import annotations

import importlib
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin


class FastAPIPlugin(FrameworkPlugin):
    """Generate FastAPI bindings for the storage runtime."""

    MIN_FASTAPI_VERSION = (0, 95)

    @property
    def name(self) -> str:  # noqa: D401 - short alias
        return "fastapi"

    @property
    def language(self) -> str:  # noqa: D401 - short alias
        return "python"

    @property
    def display_name(self) -> str:  # noqa: D401 - short alias
        return "FastAPI"

    def get_template_mappings(self) -> Dict[str, str]:
        return {
            "core_module": "templates/variants/fastapi/storage.py.j2",
            "routes": "templates/variants/fastapi/storage_routes.py.j2",
            "health": "templates/variants/fastapi/storage_health.py.j2",
            "config": "templates/variants/fastapi/storage_config.yaml.j2",
            "integration_test": "templates/tests/integration/test_storage_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "core_module": "src/modules/free/business/storage/storage.py",
            "routes": "src/modules/free/business/storage/routers/storage.py",
            "health": "src/health/storage.py",
            "config": "config/storage.yaml",
            "integration_test": "tests/modules/integration/business/storage/test_storage_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "route_prefix": "/api/v1/storage",
            "health_endpoint": "/api/health/module/storage",
            "module_kebab": "storage",
        }

    def validate_requirements(self) -> list[str]:
        issues: list[str] = []
        try:
            fastapi_module = importlib.import_module("fastapi")
        except ImportError:
            issues.append("fastapi>=0.95.0,<1.0.0 is required for the storage module")
            return issues

        version_raw = getattr(fastapi_module, "__version__", None)
        if not isinstance(version_raw, str):
            issues.append("Unable to detect FastAPI version")
            return issues

        version_bits = version_raw.split(".")
        try:
            major = int(version_bits[0]) if version_bits else 0
            minor = int(version_bits[1]) if len(version_bits) > 1 else 0
        except ValueError:
            issues.append("Unable to parse FastAPI version")
            return issues

        if (major, minor) < self.MIN_FASTAPI_VERSION:
            issues.append("FastAPI 0.95.0 or newer is required")

        return issues

    def get_dependencies(self) -> list[str]:
        return [
            "fastapi>=0.95.0,<1.0.0",
            "python-multipart>=0.0.5",
            "aiofiles>=22.1.0",
            "pillow>=9.0.0",
        ]

    def get_dev_dependencies(self) -> list[str]:
        return [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "httpx>=0.23.0",
            "faker>=15.0.0",
        ]
