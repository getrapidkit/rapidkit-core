"""Helpers for resolving RapidKit package paths across source and installed layouts."""

from __future__ import annotations

import importlib
from functools import lru_cache
from pathlib import Path
from typing import Optional


def _package_dir(package: str) -> Optional[Path]:
    """Return the absolute directory for an installed package, if available."""

    try:
        module = importlib.import_module(package)
    except ImportError:
        return None
    file_path = getattr(module, "__file__", None)
    if not file_path:
        return None
    return Path(file_path).resolve().parent


@lru_cache(maxsize=None)
def resolve_repo_root(anchor: Optional[Path] = None) -> Path:
    """Resolve the repository root or site-packages root that hosts RapidKit packages."""

    origin = anchor or Path(__file__).resolve()
    resolved_origin = origin.resolve()
    start = resolved_origin
    if start.is_file():
        start = start.parent

    for candidate in [start] + list(start.parents):
        if candidate.parent == candidate:
            continue
        if (candidate / "src" / "modules").exists():
            return candidate
        if (candidate / "modules").exists():
            return candidate

    def _installed_root(package: str) -> Optional[Path]:
        package_dir = _package_dir(package)
        if package_dir is None:
            return None

        def _find_site_packages(path: Path) -> Optional[Path]:
            targets = {"site-packages", "dist-packages"}
            for ancestor in (path,) + tuple(path.parents):
                if ancestor.name.casefold() in targets:
                    return ancestor

            parts = path.parts
            path_cls = type(path)
            for idx in range(len(parts) - 1, -1, -1):
                if parts[idx].casefold() in targets:
                    prefix = parts[: idx + 1]
                    try:
                        return path_cls(*prefix)
                    except TypeError:  # pragma: no cover - defensive for exotic paths
                        return Path(*prefix)
            return None

        try:
            resolved_dir = package_dir.resolve()
        except OSError:  # pragma: no cover - handle broken environments gracefully
            resolved_dir = package_dir

        fallbacks: list[Path] = []

        def _append_candidate(candidate: Optional[Path]) -> None:
            if candidate is None:
                return
            if candidate in fallbacks:
                return
            fallbacks.append(candidate)

        for candidate_dir in (package_dir, resolved_dir):
            _append_candidate(_find_site_packages(candidate_dir))

        _append_candidate(package_dir.parent)

        parent = resolved_dir.parent
        if parent != resolved_dir:
            _append_candidate(parent)

        _append_candidate(package_dir)

        targets = {"site-packages", "dist-packages"}

        def _valid_installed_root(candidate: Path) -> bool:
            if candidate.parent == candidate:
                return False
            lowered = {part.casefold() for part in candidate.parts}
            if lowered & targets:
                return True
            try:
                package_dir.relative_to(candidate)
            except ValueError:
                return False
            return candidate in {package_dir.parent, package_dir}

        for candidate in fallbacks:
            if _valid_installed_root(candidate):
                return candidate

        return package_dir

    for package_name in ("modules", "cli"):
        installed_root = _installed_root(package_name)
        if installed_root is not None and installed_root.parent != installed_root:
            return installed_root
    # Best-effort fallback to the grandparent directory
    try:
        fallback = resolved_origin.parents[2]
    except IndexError:  # pragma: no cover - defensive guard for unusual environments
        fallback = start.parent
    if fallback.parent == fallback:
        return start.parent
    return fallback


@lru_cache(maxsize=None)
def resolve_src_root() -> Path:
    """Return the root directory that contains the RapidKit source packages."""

    repo_root = resolve_repo_root()
    src = repo_root / "src"
    if src.exists():
        return src
    return repo_root


@lru_cache(maxsize=None)
def resolve_modules_path() -> Path:
    """Return the path that contains the RapidKit modules tree."""

    repo_root = resolve_repo_root()
    for rel in (Path("src") / "modules", Path("modules")):
        candidate = repo_root / rel
        if candidate.exists():
            return candidate
    modules_dir = _package_dir("modules")
    if modules_dir is not None and modules_dir.exists():
        return modules_dir
    raise RuntimeError("Unable to locate the RapidKit modules directory.")


@lru_cache(maxsize=None)
def resolve_registry_path() -> Path:
    """Return the path to the distribution registry file (may not exist)."""

    return resolve_repo_root() / "registry.json"
