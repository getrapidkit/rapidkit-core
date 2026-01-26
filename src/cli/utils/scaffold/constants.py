"""Shared constants for module scaffolding utilities."""

from __future__ import annotations

from pathlib import Path

# Resolve repository roots relative to this file to avoid relying on CWD.
PACKAGE_ROOT = Path(__file__).resolve().parent
UTILS_ROOT = PACKAGE_ROOT.parent
CLI_ROOT = UTILS_ROOT.parent
SRC_ROOT = CLI_ROOT.parent
REPO_ROOT = SRC_ROOT.parent

MODULES_ROOT = REPO_ROOT / "src" / "modules"

REPOSITORY_INTEGRATION_SUFFIX = "integration"

REPOSITORY_TEST_SUFFIXES = (
    "generator",
    "overrides",
    "runtime",
    "adapters",
    "validation",
    "error_handling",
    "health_check",
    "framework_variants",
    "vendor_layer",
    "configuration",
    "versioning",
    "standard_module",
)

__all__ = [
    "PACKAGE_ROOT",
    "UTILS_ROOT",
    "CLI_ROOT",
    "SRC_ROOT",
    "REPO_ROOT",
    "MODULES_ROOT",
    "REPOSITORY_TEST_SUFFIXES",
    "REPOSITORY_INTEGRATION_SUFFIX",
]
