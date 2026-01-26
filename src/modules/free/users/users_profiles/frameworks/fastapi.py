"""FastAPI framework plugin for Users Profiles."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package


class FastAPIPlugin(FrameworkPlugin):
    """Generate FastAPI-ready Users Profiles runtime."""

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
            "profiles_runtime_bridge": "templates/variants/fastapi/users_profiles_runtime.py.j2",
            "profiles_types_runtime": "templates/variants/fastapi/users_profiles_types_runtime.py.j2",
            "profiles_init": "templates/variants/fastapi/profiles_init.py.j2",
            "profiles_models": "templates/variants/fastapi/profiles_models.py.j2",
            "profiles_dto": "templates/variants/fastapi/profiles_dto.py.j2",
            "profiles_errors": "templates/variants/fastapi/profiles_errors.py.j2",
            "profiles_repository": "templates/variants/fastapi/profiles_repository.py.j2",
            "profiles_in_memory_repository": "templates/variants/fastapi/profiles_in_memory_repository.py.j2",
            "profiles_service": "templates/variants/fastapi/profiles_service.py.j2",
            "profiles_settings": "templates/variants/fastapi/profiles_settings.py.j2",
            "profiles_dependencies": "templates/variants/fastapi/profiles_dependencies.py.j2",
            "profiles_router": "templates/variants/fastapi/profiles_router.py.j2",
            "profiles_metadata_routes": "templates/variants/fastapi/users_profiles_routes.py.j2",
            "profiles_runtime": "templates/variants/fastapi/users_profiles.py.j2",
            "profiles_config": "templates/variants/fastapi/users_profiles_config.yaml.j2",
            "integration_test": "templates/tests/integration/test_users_profiles_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "profiles_runtime_bridge": "src/modules/free/users/users_profiles/users_profiles.py",
            "profiles_types_runtime": "src/modules/free/users/users_profiles/users_profiles_types.py",
            "profiles_init": "src/modules/free/users/users_profiles/core/users/profiles/__init__.py",
            "profiles_models": "src/modules/free/users/users_profiles/core/users/profiles/models.py",
            "profiles_dto": "src/modules/free/users/users_profiles/core/users/profiles/dto.py",
            "profiles_errors": "src/modules/free/users/users_profiles/core/users/profiles/errors.py",
            "profiles_repository": "src/modules/free/users/users_profiles/core/users/profiles/repository.py",
            "profiles_in_memory_repository": "src/modules/free/users/users_profiles/core/users/profiles/in_memory_repository.py",
            "profiles_service": "src/modules/free/users/users_profiles/core/users/profiles/service.py",
            "profiles_settings": "src/modules/free/users/users_profiles/core/users/profiles/settings.py",
            "profiles_dependencies": "src/modules/free/users/users_profiles/core/users/profiles/dependencies.py",
            "profiles_router": "src/modules/free/users/users_profiles/core/users/profiles/router.py",
            "profiles_metadata_routes": "src/modules/free/users/users_profiles/core/users/profiles/metadata_routes.py",
            "profiles_runtime": "src/modules/free/users/users_profiles/core/users/profiles/runtime.py",
            "profiles_config": "config/users/users_profiles.yaml",
            "integration_test": "tests/modules/integration/users/test_users_profiles_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_relative_path"),
            "vendor_health_relative": base_context.get("rapidkit_vendor_health_relative"),
            "vendor_types_relative": base_context.get("rapidkit_vendor_types_relative"),
            "config_relative": base_context.get("fastapi_config_relative"),
            "integration_test_relative": base_context.get("fastapi_test_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "users" / "users_profiles"
        (base / "core" / "users" / "profiles").mkdir(parents=True, exist_ok=True)
        (output_dir / "config" / "users").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "users").mkdir(
            parents=True, exist_ok=True
        )

        # Best-effort: materialise vendor-backed health shim (`src/health/users_profiles.py`)
        from modules.shared.utils.health import ensure_vendor_health_shim
        from modules.shared.utils.health_specs import build_standard_health_spec

        with suppress(RuntimeError, OSError):
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[
                (
                    "src.health.users_profiles",
                    "register_users_profiles_health",
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
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.3.0",
            "pytest-asyncio>=0.25.0",
        ]
