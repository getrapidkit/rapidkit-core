# pyright: reportMissingImports=false

"""FastAPI framework plugin for settings module code generation."""

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
    """Plugin for generating FastAPI-specific settings code."""

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
        """Map logical template names to FastAPI-specific template files."""
        return {
            "init": "templates/base/__init__.py.j2",
            "settings": "templates/variants/fastapi/settings.py.j2",
            "custom_sources": "templates/variants/fastapi/custom_sources.py.j2",
            "hot_reload": "templates/variants/fastapi/hot_reload.py.j2",
            "settings_health": "templates/base/settings_health.py.j2",
            "settings_types": "templates/base/settings_types.py.j2",
            "router": "templates/variants/fastapi/settings_routes.py.j2",
            "integration_tests": "templates/tests/integration/test_settings_integration.j2",
            "e2e_tests": "templates/variants/fastapi/tests/test_settings_e2e.py",
        }

    def get_output_paths(self) -> Dict[str, str]:
        """Map logical names to FastAPI output file paths."""
        return {
            "init": "src/modules/free/essentials/settings/__init__.py",
            "settings": "src/modules/free/essentials/settings/settings.py",
            "custom_sources": "src/modules/free/essentials/settings/custom_sources.py",
            "hot_reload": "src/modules/free/essentials/settings/hot_reload.py",
            "settings_health": "src/health/settings.py",
            "project_health": "src/health/settings.py",
            "settings_types": "src/modules/free/essentials/settings/settings_types.py",
            "router": "src/modules/free/essentials/settings/routers/settings.py",
            "integration_tests": "tests/modules/free/essentials/settings/test_settings_integration.py",
            "e2e_tests": "tests/modules/e2e/free/essentials/settings/test_settings_e2e.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        """Add FastAPI-specific context variables."""
        enriched = {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "import_statement": "from fastapi import FastAPI",
            "framework_features": {
                "async_support": True,
                "dependency_injection": True,
                "middleware_support": True,
                "cors_enabled": True,
                "validation_builtin": True,
            },
            "settings_class_inheritance": "BaseSettings",
            "config_dict_class": "SettingsConfigDict",
            "source_classes": {
                "dotenv": "DotEnvSettingsSource",
                "secrets": "SecretsSettingsSource",
                "custom": "CustomConfigSource",
            },
        }
        slug_value = str(
            enriched.get("module_slug") or enriched.get("rapidkit_vendor_module") or "settings"
        )
        module_segment = slug_value.split("/")[-1]
        module_kebab = module_segment.replace("_", "-")
        module_title = module_segment.replace("_", " ").title() or "Settings"
        enriched.setdefault("module_kebab", module_kebab)
        enriched.setdefault("module_name", module_segment)
        enriched.setdefault("module_title", module_title)
        return enriched

    def validate_requirements(self) -> List[str]:
        """Validate FastAPI-specific requirements."""

        errors: List[str] = []
        min_python = (3, 10)
        min_fastapi_version = (0, 119, 0)

        if sys.version_info < min_python:
            errors.append(
                "FastAPI requires Python 3.10+; upgrade your runtime before generating code"
            )

        fastapi_available = False
        version_str: str | None = None

        if "fastapi" in sys.modules:
            fastapi_available = True
            version_str = getattr(sys.modules["fastapi"], "__version__", None)
        else:
            try:
                fastapi_spec = importlib.util.find_spec("fastapi")
            except ValueError:  # pragma: no cover - defensive for mocked modules
                fastapi_spec = None

            if fastapi_spec is not None:
                fastapi_available = True

        if fastapi_available and version_str is None:
            try:
                version_str = importlib_metadata.version("fastapi")
            except importlib_metadata.PackageNotFoundError:  # pragma: no cover - defensive
                version_str = None

        if not fastapi_available:
            errors.append(
                "FastAPI is not installed. Install it with: pip install 'fastapi>=0.119.0'"
            )
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
        """Get FastAPI-specific dependencies."""
        return [
            "fastapi>=0.119.0",
            "uvicorn[standard]>=0.37.0",  # For running FastAPI apps
            "pydantic-settings>=2.4.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        """Get development dependencies for FastAPI."""
        return [
            "pytest-asyncio>=1.2.0",
            "httpx>=0.28.0",  # For testing FastAPI apps
            "fastapi[all]>=0.119.0",  # Includes all optional dependencies
            "pydantic-settings>=2.4.0",
        ]

    def pre_generation_hook(self, output_dir: Path) -> None:
        """Prepare FastAPI-specific setup before generation."""
        base = output_dir / "src" / "modules" / "free" / "essentials" / "settings"
        init_file = output_dir / "src" / "__init__.py"
        if not init_file.exists():
            init_file.parent.mkdir(parents=True, exist_ok=True)
            init_file.write_text('"""FastAPI application package."""\n')

        (base / "routers").mkdir(parents=True, exist_ok=True)
        (base / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "essentials" / "settings").mkdir(
            parents=True, exist_ok=True
        )
        # Generate a standardized vendor-backed shim and then ensure aggregator package
        module_root = Path(__file__).resolve().parents[1]
        spec = build_standard_health_spec(module_root)
        with suppress(RuntimeError, OSError):
            ensure_vendor_health_shim(output_dir, spec=spec)
        # Create the aggregator and public proxies for built-in health modules.
        ensure_health_package(
            output_dir,
            extra_imports=[
                (
                    "src.health.settings",
                    f"register_{spec.module_name}_health",
                )
            ],
        )
        synchronize_health_package(output_dir)

    def post_generation_hook(self, output_dir: Path) -> None:
        """Perform FastAPI-specific cleanup after generation."""
        # Could add FastAPI-specific post-processing here
        # For example, formatting Python files with black
        # pass

    def get_documentation_urls(self) -> Dict[str, str]:
        """Get FastAPI documentation URLs."""
        return {
            "framework_docs": "https://fastapi.tiangolo.com/",
            "tutorial": "https://fastapi.tiangolo.com/tutorial/",
            "deployment": "https://fastapi.tiangolo.com/deployment/",
            "settings_guide": "https://fastapi.tiangolo.com/tutorial/settings/",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        """Get example FastAPI configurations."""
        return {
            "app": {
                "title": "My FastAPI App",
                "version": "1.0.0",
                "description": "A FastAPI application with settings management",
            },
            "server": {
                "host": "127.0.0.1",  # Use localhost for security in development
                "port": 8000,
                "reload": True,
            },
            "cors": {
                "allow_origins": ["http://localhost:3000", "http://localhost:8080"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            },
            "database": {
                "url": "postgresql://user:password@localhost/dbname",
                "pool_size": 10,
                "max_overflow": 20,
            },
        }


class FastAPIStandardPlugin(FastAPIPlugin):
    """Alias plugin used by the fastapi.standard kit profile."""

    @property
    def name(self) -> str:  # noqa: D401 - inherits behaviour from parent
        return "fastapi.standard"

    @property
    def display_name(self) -> str:
        return "FastAPI (standard kit)"


class FastAPIDDDPlugin(FastAPIPlugin):
    """Alias plugin so fastapi.ddd kit resolves to the FastAPI implementation."""

    @property
    def name(self) -> str:  # noqa: D401
        return "fastapi.ddd"

    @property
    def display_name(self) -> str:
        return "FastAPI (DDD kit)"
