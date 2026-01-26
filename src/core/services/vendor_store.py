"""Utilities for storing and retrieving vendor copies of module files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

VENDOR_DIR = ".rapidkit/vendor"


def _vendor_base(project_root: Path) -> Path:
    return project_root / VENDOR_DIR


def _module_path(base: Path, module: str, version: str) -> Path:
    parts = [segment for segment in module.split("/") if segment]
    return base.joinpath(*parts, version)


def vendor_file_path(project_root: Path, module: str, version: str, rel_path: str) -> Path:
    base = _vendor_base(project_root)
    return _module_path(base, module, version) / rel_path


def store_vendor_file(
    project_root: Path,
    module: str,
    version: str,
    rel_path: str,
    content: bytes,
) -> Path:
    """Persist a vendor copy of a generated file and return its path."""

    target = vendor_file_path(project_root, module, version, rel_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


def load_vendor_file(
    project_root: Path,
    module: Optional[str],
    version: Optional[str],
    rel_path: str,
) -> Optional[bytes]:
    if not module or not version:
        return None

    candidate = vendor_file_path(project_root, module, version, rel_path)
    if not candidate.exists():
        return None

    try:
        return candidate.read_bytes()
    except OSError:
        return None
