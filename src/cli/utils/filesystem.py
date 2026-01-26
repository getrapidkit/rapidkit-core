# src / cli / utils / filesystem.py
from pathlib import Path
from typing import List, Optional, Union


def find_main_py(project_root: Path, base_module: str = "") -> Optional[Path]:
    base_candidates: List[str] = ["main.py", "app/main.py", "src/main.py"]
    if base_module:
        base_candidates.append(f"{base_module}/main.py")
    for rel in base_candidates:
        candidate_path = project_root / rel
        if candidate_path.exists():
            return candidate_path
    return None


def create_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def find_project_root(target_project: Optional[str] = None) -> Optional[Path]:
    """Find the root directory of a RapidKit project.

    Reduced returns to satisfy lint; keeps logic readable.
    """
    result: Optional[Path] = None
    if target_project:
        base = Path.cwd()
        if target_project == "boilerplates" and (base / "boilerplates").exists():
            parent_dir = base / "boilerplates"
            choices = [p for p in sorted(parent_dir.iterdir()) if p.is_dir()]
            result = choices[0].resolve() if choices else None
        else:
            candidate = base / "boilerplates" / target_project
            if candidate.exists() and candidate.is_dir():
                if candidate.name == "boilerplates":
                    children = [p for p in sorted(candidate.iterdir()) if p.is_dir()]
                    result = children[0].resolve() if children else None
                else:
                    result = candidate.resolve()
    else:
        current = Path.cwd()
        fallback: Optional[Path] = None
        for parent in [current] + list(current.parents):
            strong, weak = _classify_project_root(parent)
            if strong:
                result = parent
                break
            if weak and fallback is None:
                fallback = parent
        if result is None and fallback is not None:
            result = fallback
    return result


def _classify_project_root(path: Path) -> tuple[bool, bool]:
    """Return (has_strong_marker, has_any_marker) for candidate project roots."""

    if not path.exists() or not path.is_dir():
        return (False, False)

    strong_markers = [".rapidkit"]
    weak_markers = [
        "pyproject.toml",
        ".env",
        "template.yaml",
        "registry.json",
        "snippet_registry.json",
    ]

    has_strong = any((path / marker).exists() for marker in strong_markers)
    if has_strong:
        return (True, True)

    has_weak = any((path / marker).exists() for marker in weak_markers)
    return (False, has_weak)


def _is_project_root(path: Path) -> bool:
    """Legacy helper retained for callers that only need a yes/no answer."""

    _, has_marker = _classify_project_root(path)
    return has_marker


PathLike = Union[str, Path]


def resolve_project_path(
    project_root: Path, root_path: Optional[PathLike], relative_path: PathLike
) -> Path:
    """Resolve a project-relative path without duplicating root prefixes."""

    rel = Path(relative_path)
    if rel.is_absolute():
        return rel

    normalized_root = Path(root_path) if root_path else Path(".")
    if str(normalized_root) in {"", "."}:
        return project_root / rel

    try:
        rel.relative_to(normalized_root)
    except ValueError:
        return project_root / normalized_root / rel
    return project_root / rel
