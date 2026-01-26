"""File hash registry for idempotent module installation (Phase 1).

Stores per-project hash of generated files to detect local user modifications
on subsequent installs / upgrades.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, Optional

REGISTRY_DIR = ".rapidkit"
HASH_FILE = "file-hashes.json"
SNAPSHOT_DIR = "snapshots"


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_hashes(project_root: Path) -> Dict[str, Any]:
    f = project_root / REGISTRY_DIR / HASH_FILE
    if not f.exists():
        return {
            "files": {}
        }  # shape: {"files": {"relative/path": {"hash": ..., "module": name, "version": v}}}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(data, dict):  # defensive
            return {"files": {}}
        return data
    except (OSError, json.JSONDecodeError):
        return {"files": {}}


def save_hashes(project_root: Path, data: Dict[str, Any]) -> None:
    d = project_root / REGISTRY_DIR
    d.mkdir(parents=True, exist_ok=True)
    (d / HASH_FILE).write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _snapshot_path(project_root: Path, hash_value: str) -> Path:
    return project_root / REGISTRY_DIR / SNAPSHOT_DIR / hash_value


def store_snapshot(project_root: Path, content: bytes) -> str:
    h = _sha256(content)
    p = _snapshot_path(project_root, h)
    if not p.exists():  # write-once
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    return h


def load_snapshot(project_root: Path, hash_value: str) -> Optional[bytes]:
    p = _snapshot_path(project_root, hash_value)
    return p.read_bytes() if p.exists() else None


def record_file_hash(
    registry: Dict[str, Any],
    rel_path: str,
    module: str,
    version: str,
    content: bytes,
    previous_hash: Optional[str] = None,
    snapshot: bool = False,
    project_root: Optional[Path] = None,
) -> None:
    files = registry.setdefault("files", {})
    new_hash = _sha256(content)
    existing = files.get(rel_path) or {}
    history = existing.get("history", [])
    # If an overwrite with previous_hash, push any existing previous_hash to history
    if previous_hash:
        prev_prev = existing.get("previous_hash")
        if prev_prev and prev_prev not in history:
            history.append(prev_prev)
    entry = {"hash": new_hash, "module": module, "version": version}
    if previous_hash and previous_hash != new_hash:
        entry["previous_hash"] = previous_hash
    if history:
        entry["history"] = history
    if snapshot and project_root is not None:
        with suppress(OSError):
            store_snapshot(project_root, content)
    files[rel_path] = entry


def file_was_modified(registry: Dict[str, Any], rel_path: str, content: bytes) -> bool:
    entry_val = registry.get("files", {}).get(rel_path)
    if not isinstance(entry_val, dict):
        return False  # no prior record; treat as new
    recorded = entry_val.get("hash")
    if not isinstance(recorded, str):
        return True  # corrupted entry -> treat as modified
    return recorded != _sha256(content)
