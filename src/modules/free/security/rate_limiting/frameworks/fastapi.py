# pyright: reportMissingImports=false
"""FastAPI framework plugin for the Rate Limiting module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-oriented rate limiting integrations."""

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
            "runtime_wrapper": "templates/variants/fastapi/rate_limiting.py.j2",
            "dependencies": "templates/variants/fastapi/rate_limiting_dependencies.py.j2",
            "router": "templates/variants/fastapi/rate_limiting_router.py.j2",
            "metadata_routes": "templates/variants/fastapi/rate_limiting_routes.py.j2",
            "shared_types": "templates/base/rate_limiting_types.py.j2",
            "config_yaml": "templates/variants/fastapi/rate_limiting_config.yaml.j2",
            "integration_test": "templates/tests/integration/test_rate_limiting_integration.j2",
            "e2e_test": "templates/variants/fastapi/tests/test_rate_limiting_e2e.py",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime_wrapper": "src/modules/free/security/rate_limiting/__init__.py",
            "dependencies": "src/modules/free/security/rate_limiting/dependencies.py",
            "router": "src/modules/free/security/rate_limiting/router.py",
            "metadata_routes": "src/modules/free/security/rate_limiting/routes.py",
            "shared_types": "src/modules/free/security/rate_limiting/rate_limiting_types.py",
            "config_yaml": "config/security/rate_limiting.yaml",
            "integration_test": "tests/modules/integration/security/test_rate_limiting_integration.py",
            "e2e_test": "tests/modules/e2e/free/security/rate_limiting/test_rate_limiting_e2e.py",
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
            "config_relative": base_context.get("fastapi_config_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "security" / "rate_limiting"
        base.mkdir(parents=True, exist_ok=True)
        config_root = output_dir / "config" / "security"
        config_root.mkdir(parents=True, exist_ok=True)

        # Best-effort: attempt vendor-backed health shim materialisation
        from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim

        with suppress(RuntimeError, OSError):
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
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

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://fastapi.tiangolo.com/",
            "rate_limiting": "https://docs.rapidkit.top/modules/rate_limiting",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "default_rule": {
                "limit": 120,
                "windowSeconds": 60,
                "identityHeader": "X-RateLimit-Identity",
            }
        }

    def get_dependencies(self) -> List[str]:
        return ["fastapi>=0.115.0"]

    def get_dev_dependencies(self) -> List[str]:
        return ["pytest>=8.3.0", "httpx>=0.27.0"]
