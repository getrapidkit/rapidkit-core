"""Utilities for persisting and loading project metadata.

The metadata helps the CLI infer defaults (such as kit profile) when
executing commands from inside a generated project.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_METADATA_RELATIVE_PATH = Path(".rapidkit/project.json")


@dataclass
class ProjectMetadata:
    """Minimal metadata stored alongside generated projects."""

    kit_name: str
    profile: str
    created_at: str
    rapidkit_version: Optional[str] = None

    @classmethod
    def create(
        cls, kit_name: str, profile: str, rapidkit_version: Optional[str] = None
    ) -> "ProjectMetadata":
        return cls(
            kit_name=kit_name,
            profile=profile,
            rapidkit_version=rapidkit_version,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


def _metadata_path(project_root: Path) -> Path:
    return project_root / DEFAULT_METADATA_RELATIVE_PATH


def save_project_metadata(project_root: Path, metadata: ProjectMetadata) -> None:
    """Persist project metadata to the standard location."""

    path = _metadata_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(metadata)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def load_project_metadata(project_root: Path) -> Optional[ProjectMetadata]:
    """Load metadata if it exists; return ``None`` otherwise."""

    path = _metadata_path(project_root)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError):
        return None

    kit_name = payload.get("kit_name")
    profile = payload.get("profile")
    created_at = payload.get("created_at")
    if not kit_name or not profile or not created_at:
        return None

    return ProjectMetadata(
        kit_name=str(kit_name),
        profile=str(profile),
        created_at=str(created_at),
        rapidkit_version=payload.get("rapidkit_version"),
    )
