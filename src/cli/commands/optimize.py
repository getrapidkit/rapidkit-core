import re
import shutil
import subprocess  # nosec
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from core.services.snippet_optimizer import remove_inject_markers

from ..ui.printer import print_info, print_success, print_warning

opt_app = typer.Typer()


def _find_executable(name: str) -> str:
    """Return absolute path to executable or raise RuntimeError."""
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required executable '{name}' not found in PATH")
    return path


def _safe_project_name(name: str) -> str:
    """Validate project name to avoid path-injection. Allows letters, numbers, dot, underscore, dash."""
    if not re.fullmatch(r"[A-Za-z0-9._\-]+", name):
        raise ValueError("Invalid project name")
    return name


@opt_app.callback(invoke_without_command=True)
def optimize(
    project: Optional[str] = typer.Option(None, help="Project name inside boilerplates"),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--no-dry-run",
        help="Show changes without writing files",
    ),
    backup: bool = typer.Option(
        True,
        "--backup/--no-backup",
        help="Create a git commit backup before changes if repo is git",
    ),
    yes: bool = typer.Option(False, "--yes", help="Apply changes without confirmation"),
) -> None:
    """Remove inject markers across a boilerplate project.

    Usage: rapidkit optimize --project <name> [--dry-run]
    """
    proj = project or "test"
    try:
        proj = _safe_project_name(proj)
    except ValueError as e:
        print_warning(f"⚠️ {e}")
        raise typer.Exit(1) from None

    project_root = Path(__file__).resolve().parents[3] / "boilerplates" / proj
    if not project_root.exists():
        print_warning(f"⚠️ Project root not found: {project_root}")
        raise typer.Exit(1)

    print_info(f"🔍 Scanning project: {project_root} (dry_run={dry_run})")

    if backup and not dry_run:
        # try to create a git backup commit (use absolute git path)
        try:
            git_bin = _find_executable("git")
            try:
                subprocess.run([git_bin, "-C", str(project_root), "add", "-A"], check=True)  # nosec
                subprocess.run(
                    [
                        git_bin,
                        "-C",
                        str(project_root),
                        "commit",
                        "-m",
                        "chore: backup before rapidkit optimize",
                    ],
                    check=True,
                )  # nosec
                print_info("🔐 Created git backup commit in project repository")
            except subprocess.CalledProcessError as e:
                # common case: nothing to commit or git error
                print_warning(
                    f"⚠️ Git commit failed (no changes or error): {e}; attempting local copy backup"
                )
                raise RuntimeError("git-commit-failed") from None
        except RuntimeError:
            # fallback: local copy backup
            try:
                backup_root = project_root.parent / f"{proj}_backup"
                if backup_root.exists():
                    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                    backup_root = project_root.parent / f"{proj}_backup_{ts}"
                shutil.copytree(project_root, backup_root)
                print_info(f"🔐 Created local backup at: {backup_root}")
            except (OSError, shutil.Error) as e:
                print_warning(f"⚠️ Local backup failed: {e}; continuing")

    # First pass: preview changes (or perform if not dry_run)
    modified, skipped = remove_inject_markers(project_root, dry_run=dry_run)

    if not modified:
        print_success("✅ No inject markers found or nothing to change")
        raise typer.Exit(0)

    print_info(f"⚠️ Files that would be modified: {len(modified)}")
    for p in modified:
        try:
            rel = p.relative_to(project_root)
        except ValueError:
            rel = p
        print_info(f" - {rel}")

    if dry_run:
        print_info("⚠️ Dry-run mode; no files written. Re-run with --dry-run=false --yes to apply.")
        raise typer.Exit(0)

    if not yes:
        confirm = typer.confirm("Apply changes to these files? (y/N)")
        if not confirm:
            print_info("Aborted by user")
            raise typer.Exit(0)

    # Apply changes (second pass writes files)
    modified_written, skipped_after = remove_inject_markers(project_root, dry_run=False)
    print_success(f"✅ Removed inject markers from {len(modified_written)} files")
    if skipped_after:
        print_warning(f"⚠️ Some files skipped: {len(skipped_after)}")
