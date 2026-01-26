from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from core.frameworks import available, get

from ..ui.printer import print_error, print_info, print_success

frameworks_app = typer.Typer(help="Inspect and use framework adapters")


@frameworks_app.command("list")
def list_frameworks(json_output: bool = typer.Option(False, "--json")) -> None:
    data = {name: cls.__name__ for name, cls in available().items()}
    if json_output:
        print_info(json.dumps(data, indent=2))
    else:
        print_info("Available frameworks:")
        for name, cls_name in data.items():
            print_success(f"  • {name} -> {cls_name}")
        if not data:
            print_error("(none)")


@frameworks_app.command("detect")
def detect_framework(path: Path) -> None:
    """
    Detect frameworks in the given path.
    """
    root = path.resolve()
    matched = []
    for name, cls in available().items():
        try:
            if cls.detect(str(root)):
                matched.append(name)
        except (OSError, ValueError, RuntimeError) as e:  # defensive narrowing
            print_error(f"{name} detect error: {e}")
    if not matched:
        print_error("No known framework detected")
        raise typer.Exit(code=1)
    print_success("Detected frameworks: " + ", ".join(matched))


@frameworks_app.command("scaffold")
def scaffold(
    framework: str = typer.Argument(),  # noqa: B008
    project_name: str = typer.Option("app", "--name"),  # noqa: B008
    package: Optional[str] = typer.Option(None, "--package"),  # noqa: B008
    include_tests: bool = typer.Option(
        True, "--include-tests/--skip-tests", help="Include test files"
    ),  # noqa: B008
    output: Path = typer.Option(Path("."), "--output", exists=True),  # noqa: B008
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),  # noqa: B008
) -> None:
    try:
        adapter_cls = get(framework)
    except KeyError as e:
        print_error(str(e))
        raise typer.Exit(code=1) from None
    opts = {
        "project_name": project_name,
        "package": package or project_name,
        "include_tests": include_tests,
    }
    artifacts = list(adapter_cls.initialize_project(str(output), opts))
    for art in artifacts:
        dest = output / art.path
        if dest.exists() and not force:
            print_info(f"Skip existing: {art.path}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(art.content, encoding="utf-8")
        print_success(f"Wrote {art.path}")
    print_success("Scaffold complete")
