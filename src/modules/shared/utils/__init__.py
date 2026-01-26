"""Shared module utilities and helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


def load_module_manifest(module_root: Path) -> Dict[str, Any]:
    """Load and parse module manifest file."""
    manifest_path = module_root / "module.json"
    if not manifest_path.exists():
        return {}

    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Failed to load module manifest: {e}") from e


def get_module_version(module_root: Path) -> str:
    """Get module version from manifest or default."""
    manifest = load_module_manifest(module_root)
    version = manifest.get("version", "0.1.0")
    return str(version)


def normalize_module_name(name: str) -> str:
    """Normalize module name for consistent formatting."""
    return name.lower().replace("-", "_").replace(" ", "_")


def resolve_module_path(base_path: Path, module_name: str) -> Path:
    """Resolve full path to a module directory."""
    normalized_name = normalize_module_name(module_name)
    return base_path / normalized_name


def merge_configurations(
    base_config: Mapping[str, Any], override_config: Mapping[str, Any]
) -> Dict[str, Any]:
    """Deep merge two configuration dictionaries."""
    result = dict(base_config)

    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configurations(result[key], value)
        else:
            result[key] = value

    return result


def validate_module_structure(module_root: Path) -> bool:
    """Validate basic module directory structure."""
    required_files = ["module.json"]
    required_dirs: list[str] = []

    for file_name in required_files:
        if not (module_root / file_name).exists():
            return False

    return all((module_root / dir_name).is_dir() for dir_name in required_dirs)


def format_module_identifier(module_name: str, version: Optional[str] = None) -> str:
    """Format a module identifier with optional version."""
    normalized_name = normalize_module_name(module_name)
    if version:
        return f"{normalized_name}@{version}"
    return normalized_name


def extract_module_dependencies(module_root: Path) -> Dict[str, str]:
    """Extract module dependencies from manifest."""
    manifest = load_module_manifest(module_root)
    deps = manifest.get("dependencies", {})
    return {str(k): str(v) for k, v in deps.items()} if isinstance(deps, dict) else {}


def is_valid_module_name(name: str) -> bool:
    """Check if a module name is valid."""
    if not name:
        return False

    # Must start with letter or underscore
    if not (name[0].isalpha() or name[0] == "_"):
        return False

    # Must contain only letters, numbers, underscores, and hyphens
    return all(c.isalnum() or c in "_-" for c in name)


def get_module_metadata(module_root: Path) -> Dict[str, Any]:
    """Get comprehensive module metadata."""
    manifest = load_module_manifest(module_root)

    return {
        "name": manifest.get("name", module_root.name),
        "version": manifest.get("version", "0.1.0"),
        "description": manifest.get("description", ""),
        "author": manifest.get("author", ""),
        "license": manifest.get("license", ""),
        "dependencies": manifest.get("dependencies", {}),
        "tags": manifest.get("tags", []),
        "created_at": manifest.get("created_at", ""),
        "updated_at": manifest.get("updated_at", ""),
    }
