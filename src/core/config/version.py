from __future__ import annotations

from importlib import import_module, metadata
from pathlib import Path
from typing import Iterable, Optional

from packaging import version as packaging_version

CURRENT_VERSION = "0.3.1"


def check_min_version(min_version: str, current_version: str) -> None:
    if min_version and packaging_version.parse(current_version) < packaging_version.parse(
        min_version
    ):
        raise RuntimeError(
            f"RapidKit version {current_version} is lower than required {min_version}"
        )


def _resolve_metadata_version(names: Iterable[str]) -> Optional[str]:
    for name in names:
        try:
            resolved = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
        except ValueError:  # pragma: no cover - defensive guard
            continue
        else:
            if resolved:
                return resolved
    return None


def _read_module_version(*module_names: str) -> Optional[str]:
    for module_name in module_names:
        try:
            module = import_module(module_name)
        except ImportError:
            continue

        candidate = getattr(module, "__version__", None)
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def _read_pyproject_version() -> Optional[str]:
    project_root = Path(__file__).resolve().parents[3]
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return None

    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:  # pragma: no cover - I/O failure fallback
        return None

    active_section: Optional[str] = None
    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            section_name = line.strip("[]").strip().lower()
            active_section = section_name if section_name in {"tool.poetry", "project"} else None
            continue

        if active_section in {"tool.poetry", "project"} and line.startswith("version"):
            _, _, remainder = line.partition("=")
            candidate = remainder.strip().strip("\"'")
            if candidate:
                return candidate

    return None


def get_version() -> str:
    """Return the installed RapidKit package version if available, else fall back."""
    resolved = _resolve_metadata_version(["rapidkit-core", "rapidkit_core", "rapidkit"])
    if resolved:
        return resolved

    module_version = _read_module_version("rapidkit", "core", "src")
    if module_version:
        return module_version

    pyproject_version = _read_pyproject_version()
    if pyproject_version:
        return pyproject_version

    return CURRENT_VERSION


def get_cli_version() -> str:
    """Return the RapidKit global CLI version if available."""
    resolved = _resolve_metadata_version(["rapidkit-cli", "rapidkit_cli", "rapidkit"])
    if resolved:
        return resolved

    module_version = _read_module_version("cli", "rapidkit")
    if module_version:
        return module_version

    pyproject_version = _read_pyproject_version()
    if pyproject_version:
        return pyproject_version

    return CURRENT_VERSION
