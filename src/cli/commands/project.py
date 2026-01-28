from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, cast

import typer
from typing_extensions import Annotated

project_app = typer.Typer(help="Project utilities")


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return cast(Dict[str, Any], data)
        return None
    except (OSError, json.JSONDecodeError):
        return None


def _detect_project_root(start: Path) -> tuple[Optional[Path], str]:
    """Return (project_root, confidence).

    confidence:
      - strong: has .rapidkit/project.json
      - weak:   has .rapidkit (but missing project.json) OR other weak markers
      - none:   no marker found
    """

    start = start.resolve()
    weak_fallback: Optional[Path] = None

    for candidate in [start] + list(start.parents):
        rapidkit_dir = candidate / ".rapidkit"
        project_json = rapidkit_dir / "project.json"

        if rapidkit_dir.exists() and rapidkit_dir.is_dir() and project_json.exists():
            return candidate, "strong"

        if rapidkit_dir.exists() and rapidkit_dir.is_dir() and weak_fallback is None:
            weak_fallback = candidate

        if weak_fallback is None:
            for marker in ("pyproject.toml", "package.json", "template.yaml", "registry.json"):
                if (candidate / marker).exists():
                    weak_fallback = candidate
                    break

    if weak_fallback is not None:
        return weak_fallback, "weak"

    return None, "none"


def _detect_engine(start: Path, project_root: Optional[Path]) -> str:
    """Return one of: python|node|auto."""

    if project_root is not None:
        ctx = _read_json(project_root / ".rapidkit" / "context.json")
        engine = (ctx or {}).get("engine")
        if engine == "npm":
            return "node"
        return "python"

    # Not a RapidKit project; try a weak hint via package.json
    pkg = start / "package.json"
    if pkg.exists():
        data = _read_json(pkg) or {}
        for section in ("dependencies", "devDependencies"):
            dep_map = data.get(section)
            if isinstance(dep_map, dict) and any(str(k).startswith("rapidkit") for k in dep_map):
                return "node"

    return "python"


@project_app.command("detect")
def detect(
    path: Annotated[
        Optional[Path],
        typer.Option("--path", help="Path to inspect (defaults to current working directory)"),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json/--no-json", help="Emit JSON")] = True,
) -> None:
    """Detect whether the given path is inside a RapidKit project.

    This is designed as a stable contract for wrappers (e.g., npm CLI).
    """

    start = (path or Path.cwd()).resolve()
    project_root, confidence = _detect_project_root(start)

    markers: Dict[str, Any] = {
        "hasRapidkitDir": (
            bool(project_root and (project_root / ".rapidkit").exists())
            if project_root
            else bool((start / ".rapidkit").exists())
        ),
        "hasProjectJson": (
            bool(project_root and (project_root / ".rapidkit" / "project.json").exists())
            if project_root
            else bool((start / ".rapidkit" / "project.json").exists())
        ),
    }

    # If confidence is weak, markers refer to the weak fallback root when possible
    root_for_markers = project_root if project_root is not None else start
    markers.update(
        {
            "hasPyproject": (root_for_markers / "pyproject.toml").exists(),
            "hasPackageJson": (root_for_markers / "package.json").exists(),
        }
    )

    engine = _detect_engine(start, project_root if confidence == "strong" else None)

    payload: Dict[str, Any] = {
        "schema_version": 1,
        "input": str(start),
        "confidence": confidence,
        "isRapidkitProject": confidence == "strong",
        "projectRoot": str(project_root) if confidence == "strong" and project_root else None,
        "engine": engine,
        "markers": markers,
    }

    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False))
        return

    # Human output (minimal)
    if payload["isRapidkitProject"]:
        typer.echo(f"✅ RapidKit project: {payload['projectRoot']}")
    else:
        typer.echo("❌ Not a RapidKit project")
