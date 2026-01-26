# pyright: reportMissingImports=false
"""FastAPI framework plugin for the Middleware module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import (
    ensure_health_package,
    ensure_vendor_health_shim,
    synchronize_health_package,
)
from modules.shared.utils.health_specs import build_standard_health_spec


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-oriented middleware integrations."""

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
            "module": "templates/variants/fastapi/middleware.py.j2",
            "health_runtime": "templates/base/middleware_health.py.j2",
            "router": "templates/variants/fastapi/middleware_routes.py.j2",
            "config": "templates/variants/fastapi/middleware_config.yaml.j2",
            "integration_tests": "templates/tests/integration/test_middleware_integration.j2",
            "e2e_tests": "templates/variants/fastapi/tests/test_middleware_e2e.py",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "module": "src/modules/free/essentials/middleware/middleware.py",
            "health_runtime": "src/health/middleware.py",
            "health": "src/health/middleware.py",
            "project_health": "src/health/middleware.py",
            "router": "src/modules/free/essentials/middleware/routers/middleware.py",
            "config": "src/modules/free/essentials/middleware/config/middleware.yaml",
            "integration_tests": "tests/modules/free/essentials/middleware/test_middleware_integration.py",
            "e2e_tests": "tests/modules/e2e/free/essentials/middleware/test_middleware_e2e.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        enriched = {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "module_class_name": "Middleware",
            "runtime": "python",
            "middleware_types": ["cors", "timing", "headers", "logging"],
        }
        slug_value = str(enriched.get("module_slug") or enriched.get("module_name") or "middleware")
        module_segment = slug_value.split("/")[-1]
        enriched.setdefault("module_kebab", module_segment.replace("_", "-"))
        return enriched

    def validate_requirements(self) -> List[str]:  # noqa: D401 - short alias
        # Generation does not require runtime dependencies
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "essentials" / "middleware"
        base.mkdir(parents=True, exist_ok=True)
        (base / "routers").mkdir(parents=True, exist_ok=True)
        (base / "config").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "essentials" / "middleware").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "tests" / "modules" / "e2e" / "free" / "essentials" / "middleware").mkdir(
            parents=True, exist_ok=True
        )
        # Best-effort generation — don't fail if vendor payload isn't available
        module_root = Path(__file__).resolve().parents[1]
        spec = build_standard_health_spec(module_root)
        with suppress(RuntimeError, OSError):
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[
                (
                    "src.health.middleware",
                    f"register_{spec.module_name}_health",
                )
            ],
        )
        synchronize_health_package(output_dir)


class FastAPIStandardPlugin(FastAPIPlugin):
    """Alias plugin mapping fastapi.standard to the canonical FastAPI implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias reroutes to FastAPI plugin
        return "fastapi.standard"

    @property
    def display_name(self) -> str:
        return "FastAPI (standard kit)"


class FastAPIDDDPlugin(FastAPIPlugin):
    """Alias plugin mapping fastapi.ddd to the canonical FastAPI implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias reroutes to FastAPI plugin
        return "fastapi.ddd"

    @property
    def display_name(self) -> str:
        return "FastAPI (DDD kit)"
