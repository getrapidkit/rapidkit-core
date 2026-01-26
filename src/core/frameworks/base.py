"""Base classes / contracts for framework adapters.

Adapters translate generic generation intents (routes, modules, configs) into
framework-specific file structures & code templates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Protocol


@dataclass
class GeneratedArtifact:
    path: str
    content: str
    overwrite: bool = False


class FrameworkAdapter(Protocol):  # pragma: no cover - interface
    name: str

    @classmethod
    def detect(cls, project_root: str) -> bool:
        """Return True if project_root looks like this framework's project."""
        raise NotImplementedError

    @classmethod
    def initialize_project(
        cls, project_root: str, options: Dict[str, Any]
    ) -> Iterable[GeneratedArtifact]:
        """Yield artifacts needed to init a new project for this framework."""
        raise NotImplementedError

    @classmethod
    def add_module(
        cls, project_root: str, module: str, options: Dict[str, Any]
    ) -> Iterable[GeneratedArtifact]:
        """Yield artifacts for adding a logical module (domain, feature)."""
        raise NotImplementedError

    @classmethod
    def add_resource(
        cls, project_root: str, resource: str, options: Dict[str, Any]
    ) -> Iterable[GeneratedArtifact]:
        """Yield artifacts for adding a resource (e.g., model + CRUD endpoints)."""
        raise NotImplementedError

    @classmethod
    def normalize_options(cls, options: Dict[str, Any]) -> Dict[str, Any]:
        return options
