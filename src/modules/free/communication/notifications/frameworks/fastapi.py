# pyright: reportMissingImports=false
"""FastAPI framework plugin for the Notifications module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-oriented notifications integrations."""

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
            "runtime": "templates/variants/fastapi/notifications.py.j2",
            "routes": "templates/variants/fastapi/notifications_routes.py.j2",
            "config": "templates/variants/fastapi/notifications_config.yaml.j2",
            "integration_tests": "templates/variants/fastapi/tests/test_notifications_integration.py.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime": "src/modules/free/communication/notifications/core/notifications.py",
            "routes": "src/modules/free/communication/notifications/routers/notifications.py",
            "health": "src/health/notifications.py",
            "config": "config/communication/notifications.yaml",
            "integration_tests": "tests/modules/free/integration/notifications/test_notifications_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_runtime_relative"),
            "module_class_name": "Notifications",
            "module_kebab": "notifications",
            "runtime": "python",
            "notification_types": ["email", "push", "sms"],
            "template_support": True,
            "delivery_providers": ["smtp", "sendgrid", "ses"],
        }

    def validate_requirements(self) -> List[str]:
        # Generation templates do not require extra prerequisites beyond vendor assets.
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "communication" / "notifications"
        (base / "core").mkdir(parents=True, exist_ok=True)
        (base / "routers").mkdir(parents=True, exist_ok=True)
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "config" / "communication").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "integration" / "notifications").mkdir(
            parents=True,
            exist_ok=True,
        )
        # Best-effort: try to materialise vendor-backed health shim into project
        from modules.shared.utils.health import ensure_vendor_health_shim
        from modules.shared.utils.health_specs import build_standard_health_spec

        with suppress(RuntimeError, OSError):
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[("src.health.notifications", "register_notifications_health")],
        )
