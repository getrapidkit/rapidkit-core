import json
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, Optional

import typer

from core.services.config_loader import load_module_config
from core.services.file_hash_registry import (
    _sha256,
    load_hashes,
    load_snapshot,
    save_hashes,
    store_snapshot,
)
from core.services.module_manifest import load_manifest_or_none
from core.services.profile_utils import resolve_profile_chain
from core.services.snippet_injector import rollback_snippet_injection

from ..ui.printer import print_error, print_info, print_success, print_warning
from ..utils.filesystem import find_project_root

rollback_app = typer.Typer(help="Rollback generated files to previous_hash snapshot")


def _resolve_repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "src" / "modules").exists():
            return p
    return here.parents[4]


REPO_ROOT = _resolve_repo_root()
MODULES_PATH = REPO_ROOT / "src" / "modules"


def _rollback_file(
    project_root: Path,
    rel_path: str,
    registry: Dict[str, Any],
    force: bool,
    dry_run: bool,
    template_reset: bool,
    template_lookup: Optional[Dict[str, Path]] = None,
) -> Dict[str, object]:
    raw_files = registry.get("files", {})
    if not isinstance(raw_files, dict):
        raw_files = {}
    files: Dict[str, Dict[str, Any]] = {k: v for k, v in raw_files.items() if isinstance(v, dict)}
    entry = files.get(rel_path)
    status: Dict[str, object] = {"file": rel_path}
    exit_early = True
    if not entry:
        status["status"] = "untracked"
    else:
        prev = entry.get("previous_hash")
        if not prev:
            status["status"] = "no_previous"
        else:
            abs_path = project_root / rel_path
            if not abs_path.exists():
                status["status"] = "missing_current"
            else:
                try:
                    current_bytes = abs_path.read_bytes()
                except OSError:
                    status["status"] = "unreadable"
                else:
                    current_hash = _sha256(current_bytes)
                    if current_hash != entry.get("hash") and not force:
                        status.update({"status": "hash_mismatch", "current_hash": current_hash})
                    else:
                        prev_bytes = load_snapshot(project_root, prev)
                        if prev_bytes is None:
                            recovered = False
                            if template_reset and template_lookup is not None:
                                tpl = template_lookup.get(rel_path)
                                if tpl and tpl.exists():
                                    try:
                                        regen = tpl.read_text(encoding="utf-8")
                                    except OSError:
                                        pass
                                    else:
                                        prev_bytes = regen.encode("utf-8")
                                        recovered = True
                            if not recovered or prev_bytes is None:
                                status.update(
                                    {
                                        "status": "snapshot_missing",
                                        "previous_hash": prev,
                                    }
                                )
                            else:
                                exit_early = False
                        else:
                            exit_early = False
                        if not exit_early:
                            if not dry_run and prev_bytes is not None:
                                with suppress(OSError):
                                    store_snapshot(project_root, current_bytes)
                                abs_path.write_bytes(prev_bytes)
                                history = entry.get("history", [])
                                cur_hash = entry.get("hash")
                                if cur_hash and cur_hash not in history:
                                    history.append(cur_hash)
                                entry["hash"] = prev
                                last = history.pop() if history else None
                                if last and last != prev:
                                    entry["previous_hash"] = last
                                else:
                                    entry.pop("previous_hash", None)
                                if history:
                                    entry["history"] = history
                                files[rel_path] = entry
                            status.update(
                                {
                                    "status": "rolled_back",
                                    "to_hash": prev,
                                    "dry_run": dry_run,
                                }
                            )
    return status


@rollback_app.command("module")
def rollback_module(
    name: str,
    project: str = typer.Option(None, help="Project name inside boilerplates"),
    profile: str = typer.Option(
        "fastapi/minimal",
        help="Profile (needed for --template-reset to locate template)",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be rolled back"),
    force: bool = typer.Option(False, "--force", help="Ignore current hash mismatch"),
    template_reset: bool = typer.Option(
        False,
        "--template-reset",
        help="If snapshot missing, regenerate template content as fallback baseline",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Rollback all module files to their previous_hash snapshot if available.

    Uses stored snapshots (written during add/upgrade overwrites). If snapshot missing, that file is reported as snapshot_missing.
    Hash mismatch (local edits since last record) blocks rollback unless --force provided.
    """
    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    manifest = load_manifest_or_none(MODULES_PATH, name)
    if manifest:
        print_info(
            f"[bold green]Manifest:[/bold green] {manifest.effective_name} v{manifest.version}"
        )
    registry = load_hashes(project_root)
    template_lookup: Optional[Dict[str, Path]] = None
    if template_reset:
        try:
            cfg = load_module_config(name, profile)
            profile_chain = resolve_profile_chain(profile, cfg)
            template_lookup = {}
            override_dict = cfg.get("files", {}).get("overrides", {})
            root_path = cfg.get("root_path", "")
            seen = set()
            for p in profile_chain:
                entries = override_dict.get(p, [])
                for entry in entries:
                    rel = entry.get("path") if isinstance(entry, dict) else entry
                    if not rel or rel in seen:
                        continue
                    seen.add(rel)
                    tpl = (
                        MODULES_PATH
                        / name
                        / "templates"
                        / ("base" if p == "base" else f"overrides/{p}")
                        / f"{rel}.j2"
                    )
                    template_lookup[str(Path(root_path) / rel if root_path else Path(rel))] = tpl
        except (OSError, json.JSONDecodeError):
            template_lookup = None
    targets = [p for p, meta in registry.get("files", {}).items() if meta.get("module") == name]
    results = [
        _rollback_file(
            project_root,
            rel,
            registry,
            force,
            dry_run,
            template_reset,
            template_lookup,
        )
        for rel in targets
    ]
    if not dry_run and any(r.get("status") == "rolled_back" for r in results):
        save_hashes(project_root, registry)
    summary: Dict[str, int] = {}
    for r in results:
        status_val = r.get("status")
        if isinstance(status_val, str):
            summary[status_val] = summary.get(status_val, 0) + 1
    payload = {
        "schema_version": "rollback-v1",
        "module": name,
        "summary": summary,
        "files": results,
        "dry_run": dry_run,
    }
    if json_output:
        print(json.dumps(payload, indent=2))
        return
    print_info("\n[bold magenta]=== Rollback Summary ===[/bold magenta]")
    for k, v in summary.items():
        print_info(f"  • {k}: {v}")
    if summary.get("rolled_back"):
        print_success(f"Rolled back {summary['rolled_back']} files.")
    if summary.get("snapshot_missing"):
        print_warning(
            f"{summary['snapshot_missing']} files missing snapshot content (cannot rollback)."
        )
    if summary.get("hash_mismatch"):
        print_warning(
            "Some files had local modifications; use --force to override hash mismatches."
        )
    print_success("Done.")


@rollback_app.command("snippet")
def rollback_snippet(
    key: str = typer.Option(..., "--key", "-k", help="Snippet registry key (e.g. <id>::<file.py>)"),
    project: str = typer.Option(None, help="Target project root (defaults to auto-detect)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Rollback a snippet injection by removing its injected marker block."""

    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    result = rollback_snippet_injection(project_root, key=key, dry_run=dry_run)
    if json_output:
        print(json.dumps({"schema_version": "snippet-rollback-v1", **result}, indent=2))
        status = result.get("status")
        raise typer.Exit(
            code=0 if status in {"rolled_back", "not_applied", "markers_not_found"} else 1
        )

    status = result.get("status")
    if status == "rolled_back":
        if dry_run:
            print_success(f"✅ Would rollback snippet: {key}")
        else:
            print_success(f"✅ Rolled back snippet: {key}")
        return
    if status == "not_applied":
        print_warning(
            f"⏭️ Snippet not applied (status={result.get('current_status')}). Nothing to rollback."
        )
        return
    if status == "markers_not_found":
        print_warning("⚠️ Markers not found in file; nothing removed.")
        return
    if status == "missing_entry":
        print_error("❌ Snippet key not found in snippet_registry.json")
        raise typer.Exit(code=1)
    if status == "missing_file":
        print_error("❌ Target file is missing; cannot rollback.")
        raise typer.Exit(code=1)

    print_error(f"❌ Rollback failed: {result.get('error') or status}")
    raise typer.Exit(code=1)
