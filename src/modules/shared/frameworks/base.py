"""Base framework plugin interface for code generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Mapping


class FrameworkPlugin(ABC):
    """Base class for framework-specific code generation plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Framework name (e.g., 'fastapi', 'nestjs', 'django')."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Programming language (e.g., 'python', 'typescript')."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable framework name for UI/display purposes."""

    @abstractmethod
    def get_template_mappings(self) -> Dict[str, str]:
        """Map logical template names to template file paths."""

    @abstractmethod
    def get_output_paths(self) -> Dict[str, str]:
        """Map logical template names to output paths relative to project root."""

    @abstractmethod
    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        """Add framework-specific context variables."""

    @abstractmethod
    def validate_requirements(self) -> List[str]:
        """Validate that all requirements for this framework are met."""

    def get_dependencies(self) -> List[str]:
        """Return runtime dependencies for the framework."""
        return []

    def get_dev_dependencies(self) -> List[str]:
        """Return development-only dependencies for the framework."""
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:  # noqa: B027
        """Hook called before code generation starts."""

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: B027
        """Hook called after code generation completes."""

    def get_documentation_urls(self) -> Dict[str, str]:
        """Return framework-specific documentation URLs."""
        return {}

    def get_example_configurations(self) -> Dict[str, Any]:
        """Return example configuration values for this framework."""
        return {}
