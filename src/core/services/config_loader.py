# src / core / services / config_loader.py
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from cli.ui.printer import print_error, print_info, print_warning
from core.services.module_path_resolver import resolve_module_directory

"""
Path resolution logic:
- In development: core/services/config_loader.py -> parents[4] = repo root, then /src/modules
- In installed package: core/services/config_loader.py -> parents[3] = site-packages, then /modules
"""

# Try development path first (repo/src/modules), then installed path (site-packages/modules)
dev_modules_path = Path(__file__).resolve().parents[4] / "src" / "modules"
installed_modules_path = Path(__file__).resolve().parents[2] / "modules"
MODULES_PATH = dev_modules_path if dev_modules_path.exists() else installed_modules_path


def _normalize_profile_list(raw: Any) -> List[str]:
    """Convert profile metadata into a clean, de-duplicated list of strings."""

    if raw is None:
        return []

    candidates: List[Any]
    if isinstance(raw, str):
        candidates = [raw]
    elif isinstance(raw, (list, tuple, set)):
        candidates = list(raw)
    else:
        return []

    normalized: List[str] = []
    seen = set()
    for entry in candidates:
        if not isinstance(entry, str):
            continue
        candidate = entry.strip()
        if not candidate or candidate in seen:
            continue
        normalized.append(candidate)
        seen.add(candidate)
    return normalized


def _collect_profile_names(config: Dict[str, Any], profile_hint: Optional[str]) -> List[str]:
    """Return all profile identifiers declared in module config (falling back to hint)."""

    names: List[str] = []
    seen = set()

    def _add(value: Optional[str]) -> None:
        if not value:
            return
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            return
        names.append(cleaned)
        seen.add(cleaned)

    profiles_section = config.get("profiles")
    if isinstance(profiles_section, dict):
        for key in profiles_section:
            if isinstance(key, str):
                _add(key)
    elif isinstance(profiles_section, list):
        for entry in profiles_section:
            if isinstance(entry, str):
                # Accept legacy formats like "fastapi/standard: inherits=..."
                segment = entry.split(":", 1)[0]
                _add(segment)
            elif isinstance(entry, dict):
                maybe_name = entry.get("name") or entry.get("profile")
                if isinstance(maybe_name, str):
                    _add(maybe_name)

    if not names and profile_hint:
        _add(profile_hint)

    return names


def load_module_config(module_name: str, profile: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads and merges multiple YAML configuration files based on the selected profile.
    Supports base configuration, feature-specific files, and profile-specific overrides.

    Args:
        module_name (str): Name of the module (e.g., 'auth')
        profile (str, optional): Target profile (e.g., 'fastapi/enterprise')

    Returns:
        Dict: Merged configuration dictionary

    Raises:
        FileNotFoundError: If critical configuration file (base.yaml) is missing
        yaml.YAMLError: If YAML parsing fails for critical files
    """
    module_dir = resolve_module_directory(MODULES_PATH, module_name)
    module_path = module_dir / "config"
    config: Dict[str, Any] = {}

    # Debug: Log the module path (only in debug mode)
    is_debug = os.environ.get("RAPIDKIT_DEBUG", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if is_debug:
        print_info(f"🔍 Loading module config from: {module_path}")

    # Check if config directory exists
    if not module_path.exists():
        if is_debug:
            print_warning(f"⚠️ Config directory not found: {module_path}")
        return config

    def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, preserving nested structures."""
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(a.get(k), dict):
                a[k] = merge_dicts(a[k], v)
            else:
                a[k] = v
        return a

    # List of configuration files (base.yaml is critical, others are optional)
    config_files = [
        ("base.yaml", True),  # Critical
        ("profiles.yaml", False),
        ("features.yaml", False),
        ("docs.yaml", False),
        ("ci_cd.yaml", False),
        ("snippets.yaml", False),
        ("changelog.yaml", False),
    ]

    # 1. Load configuration files
    for fname, is_critical in config_files:
        file_path = module_path / fname
        if is_debug:
            print_info(f"🔍 Checking file: {file_path}")
        if not file_path.exists():
            if is_critical:
                print_error(f"❌ Critical config file not found: {file_path}")
                raise FileNotFoundError(f"Critical config file not found: {file_path}")
            if is_debug:
                print_warning(f"⚠️ Config file not found: {file_path}")
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                if is_debug:
                    print_warning(f"⚠️ Empty config file: {file_path}")
                continue
            config_data = yaml.safe_load(content)
            if config_data:
                config = merge_dicts(config, config_data)
                if is_debug:
                    print_info(f"✅ Loaded config: {file_path}")
            elif is_debug:
                print_warning(f"⚠️ No valid YAML data in: {file_path}")
        except yaml.YAMLError as e:
            if is_critical:
                print_error(f"❌ Invalid YAML in {file_path}: {e}")
                raise yaml.YAMLError(f"Invalid YAML in {file_path}: {e}") from e
            if is_debug:
                print_warning(f"⚠️ Invalid YAML in {file_path}: {e}")

    # 2. Load profile-specific override file if profile is provided
    if profile:
        framework = profile.split("/")[0]
        override_file = module_path / "overrides" / f"{framework}.yaml"
        if is_debug:
            print_info(f"🔍 Checking override file: {override_file}")
        if override_file.exists():
            try:
                content = override_file.read_text(encoding="utf-8")
                if not content.strip():
                    if is_debug:
                        print_warning(f"⚠️ Empty override file: {override_file}")
                else:
                    config_data = yaml.safe_load(content)
                    if config_data:
                        config = merge_dicts(config, config_data)
                        if is_debug:
                            print_info(f"✅ Loaded override: {override_file}")
                    elif is_debug:
                        print_warning(f"⚠️ No valid YAML data in: {override_file}")
            except yaml.YAMLError as e:
                if is_debug:
                    print_warning(f"⚠️ Invalid YAML in {override_file}: {e}")
        elif is_debug:
            print_warning(f"⚠️ Override file not found for profile {profile}: {override_file}")

    # 3. Validate critical fields / fallback to manifest for version
    missing_name = not config.get("name")
    missing_version = not config.get("version")
    if missing_version or missing_name:
        # Attempt lightweight fallback: read module.yaml manifest for version
        manifest_path = module_dir / "module.yaml"
        if manifest_path.exists():
            try:
                manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
                manifest_version = manifest_data.get("version")
                manifest_name = manifest_data.get("name")
                if manifest_version:
                    # manifest_version is a str (if present)
                    config["version"] = manifest_version
                    missing_version = False
                    if is_debug:
                        print_info(
                            f"ℹ️  Injected version from manifest fallback: {manifest_version}"
                        )
                if manifest_name and not config.get("name"):
                    config["name"] = manifest_name
                    missing_name = False
                    if is_debug:
                        print_info(f"ℹ️  Injected name from manifest fallback: {manifest_name}")
            except (
                OSError,
                yaml.YAMLError,
                UnicodeDecodeError,
            ) as e:  # pragma: no cover - defensive
                if is_debug:
                    print_warning(
                        f"⚠️ Could not read manifest for version fallback ({manifest_path}): {e}"
                    )

    if missing_name or missing_version:
        if missing_name:
            print_error(
                f"❌ Critical field 'name' missing in {module_name} configuration (base/config files)"
            )
        if missing_version:
            print_error(
                f"❌ Critical field 'version' missing in {module_name} configuration and manifest fallback"
            )
        if is_debug:
            print_info(f"🔍 Current config (post-fallback): {config}")
        raise ValueError(
            f"Critical fields missing: {[f for f, m in [('name', missing_name), ('version', missing_version)] if m]} in {module_name} configuration"
        )

    # 4. Normalize feature metadata to ensure profile-aware gating works consistently
    profile_hint = profile.strip() if isinstance(profile, str) else None
    declared_profiles = _collect_profile_names(config, profile_hint)
    fallback_profiles = declared_profiles or ([profile_hint] if profile_hint else [])

    features_section = config.get("features")
    if not isinstance(features_section, dict):
        features_section = {}
        config["features"] = features_section

    for _feature_name, meta in list(features_section.items()):
        if not isinstance(meta, dict):  # pragma: no cover - defensive guard
            continue
        normalized = _normalize_profile_list(meta.get("profiles"))
        if not normalized:
            normalized = list(fallback_profiles)
        meta["profiles"] = normalized
        if "enabled" not in meta:
            meta["enabled"] = True
        if "status" not in meta:
            meta["status"] = meta.get("status", "stable")

    module_slug = module_name.split("/")[-1].strip()
    if module_slug and module_slug not in features_section:
        features_section[module_slug] = {
            "description": config.get("display_name")
            or config.get("name")
            or f"{module_slug} feature",
            "profiles": list(fallback_profiles),
            "status": "implicit",
            "enabled": True,
        }
    elif module_slug:
        meta = features_section.get(module_slug)
        if isinstance(meta, dict):
            if not meta.get("profiles"):
                meta["profiles"] = list(fallback_profiles)
            normalized = _normalize_profile_list(meta.get("profiles"))
            meta["profiles"] = normalized or list(fallback_profiles)

    # Debug: Log final config
    if is_debug:
        print_info(f"🔍 Final merged config: {config}")
    return config
