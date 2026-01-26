"""FastAPI framework plugin for the Auth Core module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package


class FastAPIPlugin(FrameworkPlugin):
    """Generate FastAPI-friendly authentication core runtime."""

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
            "runtime": "templates/variants/fastapi/core.py.j2",
            "dependencies": "templates/variants/fastapi/dependencies.py.j2",
            "jwt_advanced": "templates/variants/fastapi/jwt_advanced.py.j2",
            "rbac": "templates/variants/fastapi/rbac.py.j2",
            "core_types": "templates/base/core_types.py.j2",
            "routes": "templates/variants/fastapi/core_routes.py.j2",
            "config": "templates/variants/fastapi/core_config.yaml.j2",
            "integration_tests": "templates/tests/integration/test_auth_core_integration.j2",
            "feature_tests": "templates/tests/integration/test_core_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime": "src/modules/free/auth/core/auth/core.py",
            "dependencies": "src/modules/free/auth/core/auth/dependencies.py",
            "jwt_advanced": "src/modules/free/auth/core/auth/jwt_advanced.py",
            "rbac": "src/modules/free/auth/core/auth/rbac.py",
            "core_types": "src/modules/free/auth/core/auth/core_types.py",
            "routes": "src/modules/free/auth/core/routers/auth_core.py",
            "config": "src/modules/free/auth/core/config/auth_core.yaml",
            "integration_tests": "tests/modules/free/auth/core/test_auth_core_integration.py",
            "feature_tests": "tests/modules/free/auth/core/test_core_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
        }

    def validate_requirements(self) -> List[str]:
        # Generation relies exclusively on the standard library.
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "auth" / "core"
        (base / "auth").mkdir(parents=True, exist_ok=True)
        (base / "routers").mkdir(parents=True, exist_ok=True)
        (base / "config").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "auth" / "core").mkdir(
            parents=True, exist_ok=True
        )
        # Try to materialise vendor-backed health shim for this module (best-effort)
        from modules.shared.utils.health import ensure_vendor_health_shim
        from modules.shared.utils.health_specs import build_standard_health_spec

        with suppress(RuntimeError, OSError):
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[
                (
                    "src.health.auth_core",
                    "register_auth_core_health",
                ),
            ],
        )

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "fastapi": "https://fastapi.tiangolo.com/",
            "security": "https://fastapi.tiangolo.com/advanced/security/",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "auth_core": {
                "iterations": 390_000,
                "salt_bytes": 32,
                "token_ttl_seconds": 1_800,
                "issuer": "RapidKit",
            }
        }

    def get_dependencies(self) -> List[str]:
        return [
            "pydantic>=2.12.2,<3.0",  # aligns with RapidKit baseline
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.3.0",  # consistent with core test tooling
        ]
