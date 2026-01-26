"""FastAPI DDD kit generator."""

from __future__ import annotations

from typing import Any, Dict

from kits.fastapi.standard.generator import FastAPIStandardGenerator


class FastAPIDDDGenerator(FastAPIStandardGenerator):
    """Generate a FastAPI project prestructured around DDD layers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._context_variables: Dict[str, Any] = {}

    def extra_context(self) -> Dict[str, Any]:  # pragma: no cover - exercised via parent tests
        """Extend the base context with DDD-specific metadata."""
        context = super().extra_context()
        context.update(
            {
                "architecture": "ddd",
                "layer_root": "src/app",
                "presentation_router_module": "src.app.presentation.api.router",
            }
        )
        return context
