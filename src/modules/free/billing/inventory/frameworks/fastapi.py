"""FastAPI framework plugin for the Inventory module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package

MODULE_BASE = "src/modules/free/billing/inventory"


class FastAPIPlugin(FrameworkPlugin):
    """Generate FastAPI bindings for the Inventory runtime."""

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
            "adapter": "templates/variants/fastapi/inventory.py.j2",
            "routes": "templates/variants/fastapi/inventory_routes.py.j2",
            "health_router": "templates/variants/fastapi/inventory_health.py.j2",
            "types": "templates/variants/fastapi/inventory_types.py.j2",
            "config": "templates/variants/fastapi/inventory_config.yaml.j2",
            "integration_tests": "templates/tests/integration/test_inventory_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "adapter": f"{MODULE_BASE}/inventory.py",
            "routes": f"{MODULE_BASE}/routers/inventory.py",
            "health_router": f"{MODULE_BASE}/health/inventory.py",
            "types": f"{MODULE_BASE}/types/inventory.py",
            "config": "config/inventory.yaml",
            "integration_tests": "tests/modules/integration/billing/inventory/test_inventory_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "api_prefix": f"/api/{base_context.get('module_kebab', 'inventory')}",
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "billing" / "inventory"
        package_dirs = [
            output_dir / "src",
            output_dir / "src" / "modules",
            output_dir / "src" / "modules" / "free",
            output_dir / "src" / "modules" / "free" / "billing",
            module_root,
            module_root / "routers",
            module_root / "health",
            module_root / "types",
        ]

        for package_dir in package_dirs:
            package_dir.mkdir(parents=True, exist_ok=True)
            init_file = package_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text(
                    '"""Generated package scaffold for Inventory module."""\n',
                    encoding="utf-8",
                )

        (output_dir / "config").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "billing" / "inventory").mkdir(
            parents=True, exist_ok=True
        )

        # Best-effort: generate vendor-backed health shim for inventory
        from modules.shared.utils.health import ensure_vendor_health_shim
        from modules.shared.utils.health_specs import build_standard_health_spec

        with suppress(RuntimeError, OSError):
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[("src.health.inventory", "register_inventory_health")],
        )

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "fastapi": "https://fastapi.tiangolo.com/",
            "inventory": "https://docs.rapidkit.top/modules/billing/inventory",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "inventory": {
                "defaults": {
                    "default_currency": "usd",
                    "low_stock_threshold": 5,
                }
            }
        }

    def get_dependencies(self) -> List[str]:
        return [
            "fastapi>=0.111.0,<1.0",
            "pydantic>=2.12.2,<3.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.2.0",
            "pytest-asyncio>=0.23.0",
        ]


__all__ = ["FastAPIPlugin"]
