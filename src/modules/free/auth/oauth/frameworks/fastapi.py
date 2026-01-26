# pyright: reportMissingImports=false
"""FastAPI framework plugin for the OAuth module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim
from modules.shared.utils.health_specs import build_standard_health_spec


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-oriented OAuth integrations."""

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
            "oauth": "templates/variants/fastapi/oauth.py.j2",
            "oauth_types": "templates/base/oauth_types.py.j2",
            "routes": "templates/variants/fastapi/oauth_routes.py.j2",
            "config": "templates/variants/fastapi/oauth_config.yaml.j2",
            "integration_tests": "templates/tests/integration/test_oauth_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "oauth": "src/modules/free/auth/oauth/oauth.py",
            "oauth_types": "src/modules/free/auth/oauth/oauth_types.py",
            "routes": "src/modules/free/auth/oauth/routers/oauth.py",
            "config": "config/oauth.yaml",
            "integration_tests": "tests/modules/integration/auth/oauth/test_oauth_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "module_class_name": "OAuth",
            "oauth_providers": ["google", "github", "facebook", "twitter"],
            "jwt_support": True,
            "state_management": True,
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "auth" / "oauth"
        module_root.mkdir(parents=True, exist_ok=True)
        (module_root / "routers").mkdir(parents=True, exist_ok=True)
        (output_dir / "config").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "auth" / "oauth").mkdir(
            parents=True, exist_ok=True
        )
        try:
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)
        except (RuntimeError, OSError):
            pass

        ensure_health_package(
            output_dir,
            extra_imports=[
                ("src.health.oauth", "register_oauth_health"),
            ],
        )

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None
