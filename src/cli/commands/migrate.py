from pathlib import Path
from typing import Optional

import typer

from ..ui.printer import print_error, print_info, print_success, print_warning
from ..utils.filesystem import find_project_root

migrate_app = typer.Typer(help="Migrate project files and layout")


def _ensure_init(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    init = path.parent / "__init__.py"
    if not init.exists():
        init.write_text("# RapidKit package init\n", encoding="utf-8")


def _write_alias(
    target: Path, import_from: str, module_name: str, slug: Optional[str] = None
) -> None:
    slug = slug or module_name
    content = f'''"""Compatibility alias for {module_name} health shim."""

from __future__ import annotations

from typing import Any

from {import_from} import {module_name} as _health_module


def __getattr__(item: str) -> Any:
    return getattr(_health_module, item)


router = getattr(_health_module, "router", None)
register_{module_name}_health = getattr(_health_module, "register_{module_name}_health")
build_health_router = getattr(_health_module, "build_health_router")
refresh_vendor_module = getattr(_health_module, "refresh_vendor_module")
DEFAULT_HEALTH_PREFIX = getattr(_health_module, "DEFAULT_HEALTH_PREFIX", "/api/health/module/{slug}")

__all__ = getattr(_health_module, "__all__", [])
'''
    _ensure_init(target)
    target.write_text(content, encoding="utf-8")


@migrate_app.command("health")
def migrate_health(
    project_root: Optional[Path] = None,
    mode: str = "move",
    dry_run: bool = False,
    yes: bool = False,
    leave_alias: bool = False,
) -> None:
    """Migrate legacy src/core/health Python health shims into the canonical src/health layout.

    New canonical-only behavior (defaults to strict move):
      - copy: Copy src/core/health/<..>.py -> src/health/<..>.py (original preserved). No compatibility alias by default.
      - move: Move src/core/health/<..>.py -> src/health/<..>.py (original removed). No compatibility alias by default.

    Use --leave-alias to leave a compatibility alias at the old path pointing to the new canonical path
    (useful for gradual upgrades, but not the default for the canonical-only decision).
    """

    root = project_root or find_project_root()
    if root is None:
        print_error("Unable to locate a project root. Run this inside a RapidKit project.")
        raise typer.Exit(code=1)

    src_core_health = root / "src" / "core" / "health"
    src_health = root / "src" / "health"

    if not src_core_health.exists():
        print_info("No legacy src/core/health folder found — nothing to migrate.")
        raise typer.Exit()

    files = [p for p in sorted(src_core_health.rglob("*.py")) if p.is_file()]
    if not files:
        print_info("No health shims found under src/core/health — nothing to migrate.")
        raise typer.Exit()

    print_info(f"Found {len(files)} health shim file(s) to migrate from {src_core_health}")

    planned = []
    for source in files:
        rel = source.relative_to(src_core_health)
        dest = src_health / rel
        planned.append((source, dest))

    if dry_run:
        print_info("Dry-run mode: planned operations")
        for s, d in planned:
            print_info(f"  {s} -> {d}")
        raise typer.Exit()

    if not yes:
        should = typer.confirm(f"Proceed to {mode} {len(planned)} file(s)?", default=True)
        if not should:
            print_info("Aborted by user")
            raise typer.Exit()

    for source, dest in planned:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if mode == "copy":
            # Create canonical file by copying original contents to src/health
            if dest.exists():
                print_warning(f"Skipping existing file {dest}")
            else:
                dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
                print_success(f"Created {dest}")
            # Optionally leave an alias at the legacy location importing from src.health
            if leave_alias:
                module_name = source.stem
                _write_alias(source, "src.health", module_name)
                print_success(f"Left compatibility alias at {source}")
        elif mode == "move":
            # Move the file; by default don't leave the old shim behind (strict canonical-only)
            final_dest_parent = dest.parent
            final_dest_parent.mkdir(parents=True, exist_ok=True)
            source.rename(dest)
            print_success(f"Moved {source} -> {dest}")
            # Optionally leave a compatibility alias at the old source path
            if leave_alias:
                module_name = dest.stem
                _write_alias(source, "src.health", module_name)
                print_success(f"Left compatibility alias at {source}")
        else:
            print_error(f"Unknown mode: {mode}. Use 'copy' or 'move'.")
            raise typer.Exit(code=2)

    print_success(
        "Migration complete — remember to run your project's tests and update imports if necessary."
    )
