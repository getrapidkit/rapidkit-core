"""FastAPI framework plugin for the Security Headers module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI integrations."""

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
            "runtime_wrapper": "templates/variants/fastapi/security_headers.py.j2",
            "http_routes": "templates/variants/fastapi/security_headers_routes.py.j2",
            "config_yaml": "templates/variants/fastapi/security_headers_config.yaml.j2",
            "integration_test": "templates/tests/integration/test_security_headers_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime_wrapper": "src/modules/free/security/security_headers/security_headers.py",
            "http_routes": "src/modules/free/security/security_headers/routers/security_headers.py",
            "config_yaml": "config/security/security_headers.yaml",
            "integration_test": "tests/modules/integration/security/test_security_headers_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "module_class_name": "SecurityHeaders",
            "module_kebab": "security-headers",
            "vendor_runtime_relative": base_context.get("rapidkit_vendor_relative_path"),
            "config_relative": base_context.get("fastapi_config_relative"),
        }

    def validate_requirements(self) -> list[str]:  # noqa: D401
        """FastAPI requires the fastapi and starlette packages."""

        # Requirements are documented for the generated project; nothing to validate here.
        return []

    def get_dependencies(self) -> list[str]:
        return ["fastapi>=0.111", "starlette>=0.37"]

    def pre_generation_hook(self, output_dir: Path) -> None:
        base_root = output_dir / "src" / "modules" / "free" / "security" / "security_headers"
        security_root = base_root
        routers_root = base_root / "routers"
        config_root = output_dir / "config" / "security"
        tests_root = output_dir / "tests" / "modules" / "integration" / "security"

        for path in (security_root, routers_root, config_root, tests_root):
            path.mkdir(parents=True, exist_ok=True)

        package_root = security_root
        if not (package_root / "__init__.py").exists():
            (package_root / "__init__.py").write_text("", encoding="utf-8")

        # Best-effort: materialise vendor-backed health shim
        from modules.shared.utils.health import ensure_vendor_health_shim
        from modules.shared.utils.health_specs import build_standard_health_spec

        with suppress(RuntimeError, OSError):
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[("src.health.security_headers", "register_security_headers_health")],
        )


__all__ = ["FastAPIPlugin"]
