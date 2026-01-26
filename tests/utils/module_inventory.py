"""Utilities for discovering RapidKit module matrices used in end-to-end tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple

import yaml

from core.services.config_loader import MODULES_PATH
from modules.free import get_registry

# Map variant keys as defined in manifests to the runtime profiles used by the CLI.
_VARIANT_TO_PROFILE = {
    "fastapi": "fastapi/standard",
    "fastapi.standard": "fastapi/standard",
    "nestjs": "nestjs/standard",
    "nestjs.standard": "nestjs/standard",
}

# Compatibility states from the registry that we consider runnable in automation.
_SUPPORTED_KIT_STATES = {
    "supported",
    "active",
    "stable",
}

_ALLOWED_STATUS_ENV = "RAPIDKIT_TEST_ALLOWED_STATUSES"
_DEFAULT_ALLOWED_STATUSES: Tuple[str, ...] = ("active", "stable", "beta", "draft")
_EXCLUDED_MODULES_ENV = "RAPIDKIT_TEST_EXCLUDED_MODULES"


def _normalize_tokens(raw: Iterable[str]) -> Tuple[str, ...]:
    tokens: List[str] = []
    for item in raw:
        value = item.strip().lower()
        if not value:
            continue
        if value == "all":
            return ("all",)
        tokens.append(value)
    seen = set()
    ordered: List[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            ordered.append(token)
    return tuple(ordered)


def _load_yaml(path: Path) -> Mapping[str, object]:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, UnicodeDecodeError):
        return {}
    return data or {}


def _is_profile_supported(module_registry_name: str, profile: str, registry) -> bool:
    status = registry.get_kit_status(module_registry_name, profile)
    if status is None:
        return True
    return status.lower() in _SUPPORTED_KIT_STATES


def _discover_profiles(
    manifest: Mapping[str, object], module_registry_name: str, registry
) -> Tuple[str, ...]:
    generation = manifest.get("generation") if isinstance(manifest, Mapping) else {}
    variants = generation.get("variants") if isinstance(generation, Mapping) else {}
    profiles: List[str] = []

    if isinstance(variants, Mapping):
        for key, profile in _VARIANT_TO_PROFILE.items():
            variant_key = key
            if variant_key in variants:
                if _is_profile_supported(module_registry_name, profile, registry):
                    profiles.append(profile)
            else:
                alt_key = key.replace(".", "/")
                if alt_key in variants and _is_profile_supported(
                    module_registry_name, profile, registry
                ):
                    profiles.append(profile)

    deduped: List[str] = []
    seen = set()
    for profile in profiles:
        if profile not in seen:
            seen.add(profile)
            deduped.append(profile)
    return tuple(deduped)


def _is_module_verified(module_dir: Path) -> bool:
    verify_path = module_dir / "module.verify.json"
    if not verify_path.exists():
        return False
    try:
        payload = json.loads(verify_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return False
    return bool(payload.get("valid"))


def _allowed_statuses() -> Tuple[str, ...]:
    raw = os.environ.get(_ALLOWED_STATUS_ENV)
    if not raw:
        return _DEFAULT_ALLOWED_STATUSES
    tokens = _normalize_tokens(raw.split(","))
    return tokens or _DEFAULT_ALLOWED_STATUSES


def _excluded_modules() -> Tuple[str, ...]:
    raw = os.environ.get(_EXCLUDED_MODULES_ENV)
    if not raw:
        return ()
    return _normalize_tokens(raw.split(","))


def _should_include_status(status: str, allowed: Tuple[str, ...]) -> bool:
    if not status:
        return False
    normalized = status.lower()
    if not allowed:
        return normalized == "active"
    if "all" in allowed:
        return True
    return normalized in allowed


def discover_active_free_module_matrix() -> Dict[str, Tuple[str, ...]]:
    """Return a module/profile matrix for eligible & verified free modules."""

    registry = get_registry()
    statuses = _allowed_statuses()
    excluded = set(_excluded_modules())
    matrix: Dict[str, Tuple[str, ...]] = {}

    modules_root = MODULES_PATH / "free"
    if not modules_root.exists():
        return matrix

    manifest_paths = sorted(modules_root.rglob("module.yaml"))

    for manifest_path in manifest_paths:
        module_dir = manifest_path.parent
        if not _is_module_verified(module_dir):
            continue

        manifest = _load_yaml(manifest_path)
        if not isinstance(manifest, Mapping):
            continue

        manifest_status = str(manifest.get("status", "")).lower()
        if not _should_include_status(manifest_status, statuses):
            continue

        registry_name = str(manifest.get("name") or module_dir.name)
        cli_name = module_dir.relative_to(MODULES_PATH).as_posix()

        lowered_cli = cli_name.lower()
        if lowered_cli in excluded or registry_name.lower() in excluded:
            continue

        profiles = _discover_profiles(manifest, registry_name, registry)
        if not profiles:
            continue

        matrix[cli_name] = profiles

    return dict(sorted(matrix.items()))
