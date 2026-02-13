"""Shared versioning utilities for RapidKit modules.

This module provides a stable façade over :mod:`core.services.module_versioning` so
individual modules never have to reach into internal helpers directly. Import all
versioning helpers from here to guarantee consistent behaviour across the
codebase.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from core.services.module_versioning import (
    DEFAULT_CHANGE_DESCRIPTION,
    DEFAULT_EXCLUDED_DIRS,
    DEFAULT_EXCLUDED_FILES,
    DEFAULT_PENDING_CHANGELOG_FILENAME,
    DEFAULT_STATE_FILENAME,
    ensure_version_consistency as _ensure_version_consistency,
)

__all__ = [
    "DEFAULT_CHANGE_DESCRIPTION",
    "DEFAULT_EXCLUDED_DIRS",
    "DEFAULT_EXCLUDED_FILES",
    "DEFAULT_PENDING_CHANGELOG_FILENAME",
    "DEFAULT_STATE_FILENAME",
    "ensure_version_consistency",
    "get_module_content_hash",
    "bump_module_version",
    "validate_version_string",
]


def ensure_version_consistency(
    config: Mapping[str, Any],
    *,
    module_root: Path,
    change_description: str = DEFAULT_CHANGE_DESCRIPTION,
    state_filename: str = DEFAULT_STATE_FILENAME,
    excluded_dirs: Optional[Iterable[str]] = None,
    excluded_files: Optional[Iterable[str]] = None,
    changelog_metadata: Optional[Mapping[str, Any]] = None,
    pending_changelog_filename: Optional[str] = DEFAULT_PENDING_CHANGELOG_FILENAME,
    clear_pending_changelog: bool = True,
    auto_bump: bool = True,
) -> Tuple[Dict[str, Any], bool]:
    """Ensure version consistency for a module.

    Args:
        config: Module configuration dictionary
        module_root: Path to the module root directory
        change_description: Description for automated version changes
        state_filename: Name of the state file to track changes
        excluded_dirs: Directories to exclude from hash calculation
        excluded_files: Files to exclude from hash calculation
        changelog_metadata: Additional metadata for changelog entries
        pending_changelog_filename: Name of pending changelog file
        clear_pending_changelog: Whether to clear pending changelog after processing

    Returns:
        Tuple of (updated_config, version_was_bumped)
    """
    kwargs: Dict[str, Any] = {
        "change_description": change_description,
        "state_filename": state_filename,
        "excluded_dirs": excluded_dirs or DEFAULT_EXCLUDED_DIRS,
        "excluded_files": excluded_files or DEFAULT_EXCLUDED_FILES,
        "changelog_metadata": changelog_metadata,
        "pending_changelog_filename": pending_changelog_filename,
        "clear_pending_changelog": clear_pending_changelog,
    }
    try:
        if "auto_bump" in inspect.signature(_ensure_version_consistency).parameters:
            kwargs["auto_bump"] = auto_bump
    except (TypeError, ValueError):
        # Fallback for callables without introspectable signatures.
        pass

    updated, bumped = _ensure_version_consistency(
        module_root,
        config,
        **kwargs,
    )
    return updated, bumped


def get_module_content_hash(
    module_root: Path,
    *,
    excluded_dirs: Optional[Iterable[str]] = None,
    excluded_files: Optional[Iterable[str]] = None,
    state_filename: str = DEFAULT_STATE_FILENAME,
) -> str:
    """Calculate content hash for a module directory.

    Args:
        module_root: Path to the module root directory
        excluded_dirs: Directories to exclude from hash calculation
        excluded_files: Files to exclude from hash calculation
        state_filename: Name of the state file to track changes

    Returns:
        SHA256 hash of module contents
    """
    from core.services.module_versioning import _compute_module_hash

    return _compute_module_hash(
        module_root,
        excluded_dirs=excluded_dirs or DEFAULT_EXCLUDED_DIRS,
        excluded_files=excluded_files or DEFAULT_EXCLUDED_FILES,
        state_filename=state_filename,
    )


def bump_module_version(current_version: str, bump_type: str = "patch") -> str:
    """Bump a module version according to semantic versioning.

    Args:
        current_version: Current version string (e.g., "1.2.3")
        bump_type: Type of bump - "major", "minor", or "patch"

    Returns:
        New version string

    Raises:
        ValueError: If version format is invalid or bump_type is unsupported
    """
    from packaging.version import Version

    try:
        version = Version(current_version)
    except Exception as e:
        raise ValueError(f"Invalid version format: {current_version}") from e

    major, minor, patch = version.major, version.minor, version.micro

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Unsupported bump type: {bump_type}. Use 'major', 'minor', or 'patch'")


def validate_version_string(version: str) -> bool:
    """Validate if a string is a valid semantic version.

    Args:
        version: Version string to validate

    Returns:
        True if valid, False otherwise
    """
    from packaging.version import InvalidVersion, Version

    try:
        Version(version)
        return True
    except InvalidVersion:
        return False
