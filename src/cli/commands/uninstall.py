import contextlib
import hashlib
import json
from typing import Any, Dict, List

import typer

from core.services.file_hash_registry import load_hashes, save_hashes

from ..ui.printer import print_error, print_info, print_success, print_warning
from ..utils.filesystem import find_project_root

uninstall_app = typer.Typer(help="Uninstall (remove) generated files of a module")


@uninstall_app.command("module")
def uninstall_module(
    name: str,
    project: str = typer.Option(None, help="Project name inside boilerplates"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be removed"),
    keep_modified: bool = typer.Option(
        True,
        "--keep-modified/--remove-modified",
        help="Skip files whose current hash != recorded",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    registry = load_hashes(project_root)
    raw_files = registry.get("files", {})
    if not isinstance(raw_files, dict):
        raw_files = {}
        registry["files"] = raw_files
    # normalize to only dict metadata entries (defensive)
    files_meta: Dict[str, Dict[str, Any]] = {
        k: v for k, v in raw_files.items() if isinstance(v, dict)
    }
    # ensure registry points to cleaned mapping (so removals persist)
    registry["files"] = files_meta
    targets = {p: meta for p, meta in files_meta.items() if meta.get("module") == name}
    removed: List[str] = []
    skipped: List[Dict[str, str]] = []
    for rel, meta in targets.items():
        abs_path = project_root / rel
        if not abs_path.exists():
            skipped.append({"file": rel, "reason": "missing"})
            continue
        with contextlib.suppress(OSError):
            current_hash = abs_path.read_bytes()
        if "current_hash" not in locals():  # read failed
            skipped.append({"file": rel, "reason": "unreadable"})
            continue
        cur_hash = hashlib.sha256(current_hash).hexdigest()
        if keep_modified and cur_hash != meta.get("hash"):
            skipped.append({"file": rel, "reason": "modified"})
            continue
        if not dry_run:
            with contextlib.suppress(OSError):
                abs_path.unlink()
            if abs_path.exists():  # unlink failed
                skipped.append({"file": rel, "reason": "unlink_failed"})
                continue
            # remove from registry
            files_meta.pop(rel, None)
            removed.append(rel)
        else:
            removed.append(rel)

    if not dry_run:
        save_hashes(project_root, registry)

    summary = {
        "module": name,
        "removed": removed,
        "skipped": skipped,
        "dry_run": dry_run,
    }
    if json_output:
        print(json.dumps(summary, indent=2))
        return
    print_info(f"Removed: {len(removed)} | Skipped: {len(skipped)}")
    if removed:
        print_info("[bold]Files Removed:[/bold]")
        for f in removed:
            print_success(f"• {f}")
    if skipped:
        print_warning("Skipped:")
        for s in skipped:
            print_warning(f"• {s['file']} ({s['reason']})")
    print_success("Done.")
