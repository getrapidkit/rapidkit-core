"""FastAPI plugin for Ai Assistant module scaffolding."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)
MODULE_BASE = "src/modules/free/ai/ai_assistant"


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
            "runtime": "templates/variants/fastapi/ai_assistant.py.j2",
            "router": "templates/variants/fastapi/ai_assistant_routes.py.j2",
            "health": "templates/variants/fastapi/ai_assistant_health.py.j2",
            "integration": "templates/tests/integration/test_ai_assistant_integration.j2",
            "config": "templates/variants/fastapi/ai_assistant_config.yaml.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "runtime": f"{MODULE_BASE}/ai_assistant.py",
            "router": f"{MODULE_BASE}/routers/ai/ai_assistant.py",
            "health": "src/health/ai_assistant.py",
            "integration": "tests/modules/free/integration/ai/ai_assistant/test_ai_assistant_integration.py",
            "config": "config/ai_assistant.yaml",
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
        return ["fastapi>=0.110.0"]

    def get_dev_dependencies(self) -> List[str]:
        return ["pytest-asyncio>=0.23.0", "httpx>=0.27.0"]

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "ai" / "ai_assistant"
        (base / "routers" / "ai").mkdir(parents=True, exist_ok=True)
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "config").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "integration" / "ai" / "ai_assistant").mkdir(
            parents=True,
            exist_ok=True,
        )

        # Best-effort: generate vendor-backed health shim for this module
        from modules.shared.utils.health import ensure_health_package, ensure_vendor_health_shim

        module_root = Path(__file__).resolve().parents[1]
        spec = build_standard_health_spec(module_root)
        with suppress(RuntimeError, OSError):
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

    def post_generation_hook(self, output_dir: Path) -> None:
        _ = output_dir


class FastAPIStandardPlugin(FastAPIPlugin):
    """Alias plugin so kits can reference fastapi.standard explicitly."""

    @property
    def name(self) -> str:  # pragma: no cover - simple alias
        return "fastapi.standard"

    @property
    def display_name(self) -> str:  # pragma: no cover - simple alias
        return "FastAPI (standard kit)"


class FastAPIDDDPlugin(FastAPIPlugin):
    """Alias plugin for the FastAPI DDD kit profile."""

    @property
    def name(self) -> str:  # pragma: no cover - simple alias
        return "fastapi.ddd"

    @property
    def display_name(self) -> str:  # pragma: no cover - simple alias
        return "FastAPI (DDD kit)"
