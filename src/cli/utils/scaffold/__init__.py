"""Composable helpers shared by the module scaffolder."""

from __future__ import annotations

from .constants import (
    CLI_ROOT,
    MODULES_ROOT,
    PACKAGE_ROOT,
    REPO_ROOT,
    SRC_ROOT,
    UTILS_ROOT,
)
from .identifiers import derive_identifiers
from .result import ModuleScaffoldResult

__all__ = [
    "derive_identifiers",
    "ModuleScaffoldResult",
    "CLI_ROOT",
    "MODULES_ROOT",
    "PACKAGE_ROOT",
    "REPO_ROOT",
    "SRC_ROOT",
    "UTILS_ROOT",
]
