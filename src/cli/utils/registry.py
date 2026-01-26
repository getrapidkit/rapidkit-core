from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ..ui.printer import print_success, print_warning


def _normalise_registry_entries(raw_entries: Any) -> List[Dict[str, Any]]:
    normalised: List[Dict[str, Any]] = []
    if not isinstance(raw_entries, list):
        return normalised
    for entry in raw_entries:
        if isinstance(entry, str):
            normalised.append({"slug": entry})
        elif isinstance(entry, dict):
            slug = entry.get("slug") or entry.get("module") or entry.get("name")
            if isinstance(slug, str) and slug:
                record = dict(entry)
                record["slug"] = slug
                normalised.append(record)
    return normalised


def update_registry(
    module_name: str,
    project_root: Path,
    *,
    version: str | None = None,
    display_name: str | None = None,
) -> None:
    """Update registry.json with installed module metadata."""

    registry_path = project_root / "registry.json"
    try:
        if not registry_path.exists():
            registry_path.write_text(
                json.dumps({"installed_modules": []}, indent=2), encoding="utf-8"
            )

        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"installed_modules": []}

        entries = _normalise_registry_entries(data.get("installed_modules", []))
        data["installed_modules"] = entries

        existing = next((item for item in entries if item.get("slug") == module_name), None)
        if existing is None:
            record: Dict[str, Any] = {"slug": module_name}
            if version:
                record["version"] = version
            if display_name:
                record["display_name"] = display_name
            entries.append(record)
            registry_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print_success(f"✅ Updated registry with module: {module_name}")
            return

        mutated = False
        if version and existing.get("version") != version:
            existing["version"] = version
            mutated = True
        if display_name and not existing.get("display_name"):
            existing["display_name"] = display_name
            mutated = True

        if mutated:
            registry_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print_success(f"🔄 Refreshed registry metadata for module: {module_name}")
    except (OSError, PermissionError) as e:
        print_warning(f"⚠️ Could not update registry: {e}")
