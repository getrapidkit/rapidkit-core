"""Data structures returned by the module scaffolder."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class ModuleScaffoldResult:
    """Summary of scaffold actions."""

    module_path: Path
    created_files: List[Path]
    skipped_files: List[Path]
    overwritten_files: List[Path]
    context: Dict[str, str]


__all__ = ["ModuleScaffoldResult"]
