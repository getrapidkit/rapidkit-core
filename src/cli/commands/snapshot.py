import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import typer

from core.rendering.template_renderer import render_template
from core.services.config_loader import load_module_config
from core.services.file_hash_registry import (
    _sha256,
    load_hashes,
    load_snapshot,
    save_hashes,
    store_snapshot,
)
from core.services.profile_utils import resolve_profile_chain

from ..ui.printer import print_error, print_info, print_success, print_warning
from ..utils.filesystem import find_project_root

snapshot_app = typer.Typer(help="Snapshot utilities (backfill missing snapshots)")


def _resolve_repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "src" / "modules").exists():
            return p
    return here.parents[4]


REPO_ROOT = _resolve_repo_root()
MODULES_PATH = REPO_ROOT / "src" / "modules"


def _normalize_rel_path(rel: str | Path) -> str:
    return str(rel).replace("\\", "/")


def _build_template_mapping(module: str, profile: str, config: Dict[str, Any]) -> Dict[str, Path]:
    mapping: Dict[str, Path] = {}
    profile_chain = resolve_profile_chain(profile, config)
    override_dict = config.get("files", {}).get("overrides", {})
    root_path = config.get("root_path", "")
    seen = set()
    for p in profile_chain:
        entries = override_dict.get(p, [])
        for entry in entries:
            rel = entry.get("path") if isinstance(entry, dict) else entry
            if not rel:
                continue
            combined = Path(root_path) / rel if root_path else Path(rel)
            key = _normalize_rel_path(combined)
            if key in seen:
                continue
            seen.add(key)
            tpl = (
                MODULES_PATH
                / module
                / "templates"
                / ("base" if p == "base" else f"overrides/{p}")
                / f"{rel}.j2"
            )
            mapping[key] = tpl
    return mapping


@snapshot_app.command("backfill")
def snapshot_backfill(
    project: str = typer.Option(None, help="Project name inside boilerplates"),
    module: Optional[str] = typer.Option(
        None, help="Limit to a specific module (else all recorded files)"
    ),
    profile: str = typer.Option(
        "fastapi/minimal", help="Profile used for template lookup when needed"
    ),
    attempt_template: bool = typer.Option(
        True,
        "--attempt-template/--no-attempt-template",
        help="Try rendering template to reconstruct missing previous snapshots",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Backfill missing snapshots for current and previous hashes.

    Strategy:
    - Ensure every current hash has a snapshot (store current bytes if missing).
    - If previous_hash snapshot missing and attempt_template enabled: try to regenerate template; if rendered hash matches previous_hash, store it.
    - Does NOT guess previous content if cannot verify hash (safety). Those remain missing.
    """
    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    registry = load_hashes(project_root)
    files_meta: Dict[str, Dict[str, Any]] = registry.get("files", {})
    targets = (
        {p: meta for p, meta in files_meta.items() if meta.get("module") == module}
        if module
        else files_meta
    )

    template_mapping_cache: Dict[str, Dict[str, Path]] = {}
    variables_cache: Dict[str, Dict[str, Any]] = {}

    stats = {
        "current_snapshots_added": 0,
        "previous_snapshots_added": 0,
        "previous_missing": 0,
        "previous_unverified": 0,
        "current_missing_files": 0,
    }
    details = []

    for rel, meta in targets.items():
        abs_path = project_root / rel
        if not abs_path.exists():
            stats["current_missing_files"] += 1
            details.append({"file": rel, "status": "missing"})
            continue
        try:
            content = abs_path.read_bytes()
        except OSError:
            details.append({"file": rel, "status": "unreadable"})
            continue
        cur_hash = _sha256(content)
        if load_snapshot(project_root, cur_hash) is None:
            try:
                store_snapshot(project_root, content)
                stats["current_snapshots_added"] += 1
                details.append({"file": rel, "action": "snapshotted_current"})
            except OSError:
                details.append({"file": rel, "status": "snapshot_failed_current"})

        prev = meta.get("previous_hash")
        if prev and load_snapshot(project_root, prev) is None:
            if attempt_template and meta.get("module"):
                raw_mod = meta.get("module")
                if not isinstance(raw_mod, str) or not raw_mod:
                    stats["previous_missing"] += 1
                    details.append({"file": rel, "status": "no_module_name"})
                    continue
                mod_name: str = raw_mod
                # Build mapping if not cached
                if mod_name not in template_mapping_cache:
                    try:
                        cfg = load_module_config(mod_name, profile)
                        template_mapping_cache[mod_name] = _build_template_mapping(
                            mod_name, profile, cfg
                        )
                        variables_cache[mod_name] = {
                            k: v.get("default") for k, v in cfg.get("variables", {}).items()
                        }
                    except (OSError, json.JSONDecodeError):
                        template_mapping_cache[mod_name] = {}
                        variables_cache[mod_name] = {}
                norm_rel = _normalize_rel_path(rel)
                tpl_path = template_mapping_cache[mod_name].get(norm_rel)
                if tpl_path and tpl_path.exists():
                    try:
                        rendered = render_template(
                            tpl_path, variables_cache.get(mod_name, {})
                        ).encode("utf-8")
                        if _sha256(rendered) == prev:
                            store_snapshot(project_root, rendered)
                            stats["previous_snapshots_added"] += 1
                            details.append(
                                {
                                    "file": rel,
                                    "action": "snapshotted_previous_via_template",
                                }
                            )
                            continue
                        stats["previous_unverified"] += 1
                        details.append(
                            {
                                "file": rel,
                                "status": "template_hash_mismatch",
                                "expected": prev,
                                "got": _sha256(rendered),
                            }
                        )
                        continue
                    except OSError as e:
                        details.append(
                            {
                                "file": rel,
                                "status": "template_render_failed",
                                "error": str(e),
                            }
                        )
                        stats["previous_unverified"] += 1
                        continue
            stats["previous_missing"] += 1
            details.append({"file": rel, "status": "previous_snapshot_missing"})

    # Persist (no registry modification needed, just snapshots written)
    save_hashes(project_root, registry)

    summary = {"module": module, "stats": stats, "details": details}
    if json_output:
        print(json.dumps(summary, indent=2))
        return
    print_info(
        f"Current snapshots added: {stats['current_snapshots_added']} | Previous snapshots added: {stats['previous_snapshots_added']} | Previous missing: {stats['previous_missing']} | Previous unverified: {stats['previous_unverified']}"
    )
    if stats["previous_missing"]:
        print_warning("Some previous snapshots still missing (cannot rollback those yet).")
    if stats["previous_unverified"]:
        print_warning("Template hash mismatch for some; unsafe to fabricate snapshot.")
    print_success("Done.")


@snapshot_app.command("gc")
def snapshot_gc(
    project: str = typer.Option(None, help="Project name inside boilerplates"),
    keep: int = typer.Option(200, help="Maximum number of snapshot files to retain"),
    max_age_days: int = typer.Option(
        0, help="Delete snapshots older than this many days (0 = ignore age)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deleted"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON summary"),
) -> None:
    """Garbage collect snapshot files to control storage growth.

    Retention logic (both filters can apply):
      1. Age filter: if max_age_days>0 delete snapshots whose mtime older than threshold.
      2. Count filter: after age removals, if total still > keep, delete oldest until count==keep.

    Safety: Only removes files under .rapidkit/snapshots/.
    """
    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)
    snap_dir = project_root / ".rapidkit" / "snapshots"
    if not snap_dir.exists():
        if json_output:
            print(json.dumps({"deleted": 0, "kept": 0, "reason": "no_dir"}))
            return
        print_info("No snapshots directory.")
        return
    files = [p for p in snap_dir.iterdir() if p.is_file()]
    now = datetime.utcnow().timestamp()
    age_threshold = now - max_age_days * 86400 if max_age_days > 0 else None
    age_deleted = []
    remaining = []
    for f in files:
        try:
            st = f.stat()
        except OSError:
            remaining.append((f, now))
            continue
        if age_threshold and st.st_mtime < age_threshold:
            age_deleted.append(f)
        else:
            remaining.append((f, st.st_mtime))
    count_deleted = []
    # Apply count retention
    if keep > 0 and len(remaining) > keep:
        remaining.sort(key=lambda x: x[1])  # oldest first
        overflow = remaining[:-keep]
        count_deleted = [f for f, _ in overflow]
        remaining = remaining[-keep:]
    to_delete = list({*age_deleted, *count_deleted})
    if not dry_run:
        for f in to_delete:
            try:
                f.unlink()
            except OSError:
                continue
    result = {
        "schema_version": "snapshot-gc-v1",
        "deleted": len(to_delete),
        "deleted_age": len(age_deleted),
        "deleted_count": len(count_deleted),
        "kept": len(remaining),
        "dry_run": dry_run,
        "keep_limit": keep,
        "max_age_days": max_age_days,
    }
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print_info(
            f"Snapshots kept: {result['kept']} | deleted(age={result['deleted_age']}, count={result['deleted_count']})"
        )
        if dry_run:
            print_warning("Dry-run: no files removed.")
        print_success("GC complete.")
