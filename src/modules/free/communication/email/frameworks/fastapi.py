# pyright: reportMissingImports=false
"""FastAPI framework plugin for the Email module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim
from modules.shared.utils.health_specs import build_standard_health_spec


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-oriented Email integrations."""

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
            "runtime_wrapper": "templates/variants/fastapi/email.py.j2",
            "types": "templates/base/email_types.py.j2",
            "routes": "templates/variants/fastapi/email_routes.py.j2",
            "config": "templates/variants/fastapi/email_config.yaml.j2",
            "integration_test": "templates/variants/fastapi/tests/test_email_integration.py.j2",
            "tests_conftest": "templates/variants/fastapi/tests/conftest.py.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime_wrapper": "src/modules/free/communication/email/email.py",
            "types": "src/modules/free/communication/email/email_types.py",
            "routes": "src/modules/free/communication/email/routers/email.py",
            "config": "src/modules/free/communication/email/config/email.yaml",
            "integration_test": "tests/modules/free/communication/email/test_email_integration.py",
            "tests_conftest": "tests/modules/free/communication/email/conftest.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_runtime_relative"),
            "module_class_name": "Email",
            "module_kebab": "email",
        }

    def validate_requirements(self) -> list[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "communication" / "email"
        (base).mkdir(parents=True, exist_ok=True)
        (base / "routers").mkdir(parents=True, exist_ok=True)
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (base / "config").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "communication" / "email").mkdir(
            parents=True, exist_ok=True
        )
        try:
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)
        except (RuntimeError, OSError):
            pass

        ensure_health_package(
            output_dir,
            extra_imports=[("src.health.email", "register_email_health")],
        )


class FastAPIStandardPlugin(FastAPIPlugin):
    """Alias plugin mapping fastapi.standard to the canonical FastAPI implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias returns base plugin
        return "fastapi.standard"

    @property
    def display_name(self) -> str:
        return "FastAPI (standard kit)"


class FastAPIDDDPlugin(FastAPIPlugin):
    """Alias plugin mapping fastapi.ddd to the canonical FastAPI implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias returns base plugin
        return "fastapi.ddd"

    @property
    def display_name(self) -> str:
        return "FastAPI (DDD kit)"
