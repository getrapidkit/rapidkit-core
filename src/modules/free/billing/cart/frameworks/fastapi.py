"""FastAPI framework plugin for the Cart module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package

MODULE_BASE = "src/modules/free/billing/cart"


class FastAPIPlugin(FrameworkPlugin):
    """Generate FastAPI bindings for the Cart runtime."""

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
            "adapter": "templates/variants/fastapi/cart.py.j2",
            "routes": "templates/variants/fastapi/cart_routes.py.j2",
            "health_router": "templates/variants/fastapi/cart_health.py.j2",
            "types": "templates/variants/fastapi/cart_types.py.j2",
            "config": "templates/variants/fastapi/cart_config.yaml.j2",
            "integration_tests": "templates/tests/integration/test_cart_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "adapter": f"{MODULE_BASE}/cart.py",
            "routes": f"{MODULE_BASE}/routers/cart.py",
            "health_router": f"{MODULE_BASE}/health/cart.py",
            "types": f"{MODULE_BASE}/types/cart.py",
            "config": "config/cart.yaml",
            "integration_tests": "tests/modules/integration/billing/cart/test_cart_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
        }

    def validate_requirements(self) -> List[str]:
        # Generation relies on FastAPI/Pydantic at runtime; generator has no additional requirements.
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "billing" / "cart"
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
                    '"""Generated package scaffold for Cart module."""\n',
                    encoding="utf-8",
                )

        (output_dir / "config").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "billing" / "cart").mkdir(
            parents=True, exist_ok=True
        )

        # Best-effort: generate vendor-backed health shim for cart
        from modules.shared.utils.health import ensure_vendor_health_shim
        from modules.shared.utils.health_specs import build_standard_health_spec

        with suppress(RuntimeError, OSError):
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[("src.health.cart", "register_cart_health")],
        )

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "fastapi": "https://fastapi.tiangolo.com/",
            "rapidkit": "https://docs.rapidkit.top/modules/billing/cart",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "cart": {
                "currency": "USD",
                "tax_rate": "0.07",
                "default_discount_code": "WELCOME10",
            }
        }

    def get_dependencies(self) -> List[str]:
        return [
            "fastapi>=0.111.0,<1.0",
            "pydantic>=2.12.2,<3.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.3.0",
        ]


__all__ = ["FastAPIPlugin"]
