import json
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict

import typer

from core.services.file_hash_registry import (
    _sha256,
    load_hashes,
    load_snapshot,
    record_file_hash,
    save_hashes,
    store_snapshot,
)
from core.services.module_manifest import load_manifest_or_none

from ..ui.printer import print_error, print_info, print_success, print_warning
from ..utils.filesystem import find_project_root

checkpoint_app = typer.Typer(help="Create rollback checkpoints for a module's files")


def _resolve_repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "src" / "modules").exists():
            return p
    return here.parents[4]


REPO_ROOT = _resolve_repo_root()
MODULES_PATH = REPO_ROOT / "src" / "modules"


@checkpoint_app.command("module")
def checkpoint_module(
    name: str,
    project: str = typer.Option(None, help="Project name inside boilerplates"),
    include_clean: bool = typer.Option(
        False, help="Also checkpoint files whose current hash matches registry"
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Capture current file content as a new baseline (records previous_hash & snapshot).

    Useful before making experimental edits: run checkpoint, edit files, then rollback will restore to the checkpoint.
    Limit: If the older baseline had no snapshot stored, rolling back beyond the checkpoint may show snapshot_missing.
    """
    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    manifest = load_manifest_or_none(MODULES_PATH, name)
    registry = load_hashes(project_root)
    files_meta: Dict[str, Dict[str, Any]] = registry.get("files", {})
    targets = {p: meta for p, meta in files_meta.items() if meta.get("module") == name}

    updated = []
    skipped = []
    for rel, meta in targets.items():
        abs_path = project_root / rel
        if not abs_path.exists():
            skipped.append({"file": rel, "reason": "missing"})
            continue
        try:
            current_bytes = abs_path.read_bytes()
        except OSError:
            skipped.append({"file": rel, "reason": "unreadable"})
            continue
        cur_hash = _sha256(current_bytes)
        if cur_hash == meta.get("hash") and not include_clean:
            skipped.append({"file": rel, "reason": "clean"})
            continue
        # snapshot current content (new baseline) BEFORE updating registry
        previous_hash = meta.get("hash")
        # Ensure previous baseline snapshot exists
        if previous_hash and load_snapshot(project_root, previous_hash) is None:
            # Only snapshot if current bytes still match previous hash (clean)
            if _sha256(current_bytes) == previous_hash:
                with suppress(OSError):
                    store_snapshot(project_root, current_bytes)
        # Snapshot current content (new baseline)
        with suppress(OSError):
            store_snapshot(project_root, current_bytes)
        # Update registry entry using record_file_hash to maintain history
        record_file_hash(
            registry,
            rel,
            meta.get("module", name),
            meta.get("version") or (manifest.version if manifest else "unknown"),
            current_bytes,
            previous_hash=previous_hash,
            snapshot=True,
            project_root=project_root,
        )
        updated.append(rel)

    if updated:
        save_hashes(project_root, registry)

    summary = {"module": name, "checkpointed": updated, "skipped": skipped}
    if json_output:

        print(json.dumps(summary, indent=2))
        return
    print_info(
        f"Checkpointed: {len(updated)} | Skipped: {len(skipped)} (use --include-clean to force clean files)"
    )
    if updated:
        print_success("Updated entries:")
        for f in updated:
            print_success(f"• {f}")
    if skipped:
        print_warning("Skipped:")
        for s in skipped:
            print_warning(f"• {s['file']} ({s['reason']})")
    print_success("Done.")
