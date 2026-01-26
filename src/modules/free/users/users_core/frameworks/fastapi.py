"""FastAPI framework plugin for Users Core."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package


class FastAPIPlugin(FrameworkPlugin):
    """Generate FastAPI-ready Users Core runtime."""

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
            "users_runtime": "templates/variants/fastapi/users_core.py.j2",
            "users_types_runtime": "templates/variants/fastapi/users_core_types_runtime.py.j2",
            "users_init": "templates/variants/fastapi/__init__.py.j2",
            "users_models": "templates/variants/fastapi/users_core_models.py.j2",
            "users_dto": "templates/variants/fastapi/users_core_dto.py.j2",
            "users_errors": "templates/variants/fastapi/users_core_errors.py.j2",
            "users_repository": "templates/variants/fastapi/users_core_repository.py.j2",
            "users_settings": "templates/variants/fastapi/users_core_settings.py.j2",
            "users_service": "templates/variants/fastapi/users_core_service.py.j2",
            "users_in_memory_repository": "templates/variants/fastapi/users_core_in_memory_repository.py.j2",
            "users_dependencies": "templates/variants/fastapi/users_core_dependencies.py.j2",
            "users_router": "templates/variants/fastapi/users_core_router.py.j2",
            "users_metadata_routes": "templates/variants/fastapi/users_core_routes.py.j2",
            "users_config": "templates/variants/fastapi/users_core_config.yaml.j2",
            "users_integration_test": "templates/tests/integration/test_users_core_integration.py.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "users_runtime": "src/modules/free/users/users_core/users_core.py",
            "users_types_runtime": "src/modules/free/users/users_core/users_core_types.py",
            "users_init": "src/modules/free/users/users_core/core/users/__init__.py",
            "users_models": "src/modules/free/users/users_core/core/users/models.py",
            "users_dto": "src/modules/free/users/users_core/core/users/dto.py",
            "users_errors": "src/modules/free/users/users_core/core/users/errors.py",
            "users_repository": "src/modules/free/users/users_core/core/users/repository.py",
            "users_settings": "src/modules/free/users/users_core/core/users/settings.py",
            "users_service": "src/modules/free/users/users_core/core/users/service.py",
            "users_in_memory_repository": "src/modules/free/users/users_core/core/users/in_memory_repository.py",
            "users_dependencies": "src/modules/free/users/users_core/core/users/dependencies.py",
            "users_router": "src/modules/free/users/users_core/core/users/router.py",
            "users_metadata_routes": "src/modules/free/users/users_core/core/users/metadata_routes.py",
            "users_config": "src/modules/free/users/users_core/config/users_core.yaml",
            "users_integration_test": "tests/modules/free/users/users_core/test_users_core_integration.py",
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
            "vendor_health_relative": base_context.get("rapidkit_vendor_health_relative"),
            "vendor_types_relative": base_context.get("rapidkit_vendor_types_relative"),
            "config_relative": base_context.get("fastapi_config_relative"),
            "integration_test_relative": base_context.get("fastapi_test_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "users" / "users_core"
        (base / "core" / "users").mkdir(parents=True, exist_ok=True)
        (base / "config").mkdir(parents=True, exist_ok=True)
        (base).mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "users" / "users_core").mkdir(
            parents=True, exist_ok=True
        )

        # Best-effort: materialise vendor-backed health shim (`src/health/users_core.py`)
        from modules.shared.utils.health import ensure_vendor_health_shim
        from modules.shared.utils.health_specs import build_standard_health_spec

        with suppress(RuntimeError, OSError):
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[
                (
                    "src.health.users_core",
                    "register_users_core_health",
                ),
            ],
        )

        # Canonical health lives under src/health; do not emit module-local health files.

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "fastapi": "https://fastapi.tiangolo.com/",
            "pydantic": "https://docs.pydantic.dev/latest/",
        }

    def get_dependencies(self) -> List[str]:
        return [
            "fastapi>=0.111.0,<1.0",
            "pydantic>=2.12.2,<3.0",
            "email-validator>=2.1.1,<3.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.3.0",
            "pytest-asyncio>=0.25.0",
        ]
