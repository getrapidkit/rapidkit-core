"""Shared typing utilities for the middleware module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Protocol


class MiddlewareCallable(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - protocol stub
        ...


@dataclass(slots=True)
class MiddlewareDescriptor:
    """Describe a middleware entry in the execution pipeline."""

    name: str
    callable: MiddlewareCallable
    enabled: bool = True
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PipelineConfig:
    """Represent the resolved middleware pipeline configuration."""

    module: str
    entries: List[MiddlewareDescriptor] = field(default_factory=list)

    def enabled(self) -> Iterable[MiddlewareDescriptor]:
        return (entry for entry in self.entries if entry.enabled)
