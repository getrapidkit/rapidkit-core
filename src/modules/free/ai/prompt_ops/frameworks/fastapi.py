"""FastAPI plugin for Prompt Ops module scaffolding."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]


class FastAPIPlugin(FrameworkPlugin):
    """Provide FastAPI-specific template and output mappings."""

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
            "runtime": "templates/variants/fastapi/prompt_ops.py.j2",
            "router": "templates/variants/fastapi/prompt_ops_routes.py.j2",
            "health": "templates/variants/fastapi/prompt_ops_health.py.j2",
            "integration": "templates/tests/integration/test_prompt_ops_integration.j2",
            "e2e": "templates/variants/fastapi/tests/test_prompt_ops_e2e.py",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime": "src/modules/free/ai/prompt_ops/prompt_ops.py",
            "router": "src/modules/free/ai/prompt_ops/routers/ai/prompt_ops.py",
            "health": "src/health/ai/prompt_ops.py",
            "integration": "tests/modules/free/integration/ai/prompt_ops/test_prompt_ops_integration.py",
            "e2e": "tests/modules/e2e/free/ai/prompt_ops/test_prompt_ops_e2e.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        enriched = dict(base_context)
        enriched.update(
            {
                "framework": "fastapi",
                "framework_display_name": "FastAPI",
                "language": "python",
            }
        )
        return enriched

    def validate_requirements(self) -> List[str]:
        return []

    def get_dependencies(self) -> List[str]:
        return ["fastapi>=0.139.0,<1.0.0"]

    def get_dev_dependencies(self) -> List[str]:
        return ["pytest-asyncio>=1.3.0,<2.0", "httpx>=0.27.0"]

    def pre_generation_hook(self, output_dir: Path) -> None:
        (output_dir / "src" / "modules" / "free" / "ai" / "prompt_ops" / "routers" / "ai").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        spec = build_standard_health_spec(MODULE_ROOT)
        with suppress(RuntimeError, OSError):
            ensure_vendor_health_shim(output_dir, spec=spec)
        ensure_health_package(
            output_dir,
            extra_imports=[
                (
                    f"src.health.ai.{spec.module_name}",
                    f"register_{spec.module_name}_health",
                )
            ],
        )

    def post_generation_hook(self, output_dir: Path) -> None:
        _ = output_dir
