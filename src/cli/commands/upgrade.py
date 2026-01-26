import json
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import typer

from core.rendering.template_renderer import render_template
from core.services.config_loader import load_module_config
from core.services.file_hash_registry import (
    _sha256,
    load_hashes,
    record_file_hash,
    save_hashes,
    store_snapshot,
)
from core.services.module_manifest import load_manifest_or_none
from core.services.profile_utils import resolve_profile_chain

from ..ui.printer import print_error, print_info, print_success, print_warning
from ..utils.classifier import classify_file_status
from ..utils.filesystem import find_project_root
from ..utils.variables_prompt import prompt_for_variables

upgrade_app = typer.Typer(help="Upgrade generated files of a module to latest templates")


def _resolve_repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "src" / "modules").exists():
            return p
    return here.parents[4]


REPO_ROOT = _resolve_repo_root()
MODULES_PATH = REPO_ROOT / "src" / "modules"


def _compute_files(
    _module_name: str, profile: str, config: Dict[str, Any]
) -> Tuple[List[Tuple[str, Dict[str, Any]]], List[str]]:  # module name unused
    """Collect all file entries (with context) and active features for a module/profile."""
    profile_chain = resolve_profile_chain(profile, config)
    override_dict = config.get("files", {}).get("overrides", {})
    all_files: List[Tuple[str, Dict[str, Any]]] = []
    seen_paths: Set[str] = set()
    for p in profile_chain:
        entries = override_dict.get(p, [])
        for entry in entries:
            path = entry.get("path") if isinstance(entry, dict) else entry
            if path and path not in seen_paths:
                all_files.append((p, entry if isinstance(entry, dict) else {"path": entry}))
                seen_paths.add(path)
    raw_features = config.get("features") or {}
    if not isinstance(raw_features, dict):
        raw_features = {}
    active_features: List[str] = []
    for f, meta in raw_features.items():
        if meta is True:
            active_features.append(str(f))
            continue
        if meta is False or meta is None:
            continue
        if isinstance(meta, dict):
            profiles_list = meta.get("profiles") or []
            if isinstance(profiles_list, list) and profile in profiles_list:
                active_features.append(f)
    ff = config.get("features_files") or {}
    if not isinstance(ff, dict):
        ff = {}
    for feature in active_features:
        for entry in ff.get(feature, []):
            path = entry.get("path") if isinstance(entry, dict) else entry
            if path and path not in seen_paths:
                all_files.append((profile, entry if isinstance(entry, dict) else {"path": entry}))
                seen_paths.add(path)
    for section in ["unit_tests", "e2e_tests", "security_tests", "performance_tests"]:
        for feature in active_features:
            for entry in config.get(section, {}).get(feature, []):
                path = entry.get("path") if isinstance(entry, dict) else entry
                if path and path not in seen_paths:
                    all_files.append(
                        (profile, entry if isinstance(entry, dict) else {"path": entry})
                    )
                    seen_paths.add(path)
    ci_cd_files = config.get("ci_cd", {})
    if isinstance(ci_cd_files, dict):
        for sub_section in ci_cd_files.values():
            for entry in sub_section:
                path = (
                    (entry.get("path") or entry.get("template"))
                    if isinstance(entry, dict)
                    else entry
                )
                if path and path not in seen_paths:
                    all_files.append(
                        (profile, entry if isinstance(entry, dict) else {"path": entry})
                    )
                    seen_paths.add(path)
    else:
        for entry in ci_cd_files:
            path = entry.get("path") if isinstance(entry, dict) else entry
            if path and path not in seen_paths:
                all_files.append((profile, entry if isinstance(entry, dict) else {"path": entry}))
                seen_paths.add(path)
    return all_files, active_features


def _plan_or_apply_upgrade(
    name: str,
    profile: str,
    project_root: Path,
    config: Dict[str, Any],
    variables: Dict[str, Any],
    dry_run: bool,
    force_modified: bool,
    force_diverged: bool,
    allowed_statuses: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Core upgrade logic reused by single-module and batch flows."""
    hash_registry = load_hashes(project_root)
    root_path = config.get("root_path", "")
    all_files, _ = _compute_files(name, profile, config)
    actions: List[Dict[str, Any]] = []
    counts = dict.fromkeys(
        [
            "template_updated",
            "locally_modified",
            "diverged",
            "updated",
            "skipped",
        ],
        0,
    )
    for context, file_entry in all_files:
        rel = (
            (file_entry.get("path") or file_entry.get("template"))
            if isinstance(file_entry, dict)
            else file_entry
        )
        if not rel:
            continue
        template_file = file_entry.get("template") if isinstance(file_entry, dict) else None
        if template_file:
            template_path = MODULES_PATH / name / template_file
        else:
            template_path = (
                MODULES_PATH
                / name
                / "templates"
                / ("base" if context == "base" else f"overrides/{context}")
                / f"{rel}.j2"
            )
        dst = project_root / root_path / rel
        regenerated_content = None
        regenerated_hash = None
        if template_path.exists():
            try:
                regenerated_content = render_template(template_path, variables)
            except Exception as e:  # noqa: BLE001 - template engine variability
                print_warning(f"⚠️ Failed to render template {template_path}: {e}")
            else:
                regenerated_hash = _sha256(regenerated_content.encode("utf-8"))
        rel_record = str(dst.relative_to(project_root))
        entry = hash_registry.get("files", {}).get(rel_record)
        registry_hash = entry.get("hash") if entry else None
        if dst.exists():
            try:
                current_bytes = dst.read_bytes()
            except OSError:
                current_bytes = b""
            current_hash = _sha256(current_bytes)
        else:
            current_hash = None
        status = classify_file_status(dst.exists(), registry_hash, current_hash, regenerated_hash)
        do_update = False
        reason = None
        if allowed_statuses and status not in allowed_statuses:
            do_update = False
        elif status == "template_updated":
            do_update = True
            reason = "template changed"
        elif status == "locally_modified" and force_modified and regenerated_content is not None:
            do_update = True
            reason = "force-modified"
        elif status == "diverged" and force_diverged and regenerated_content is not None:
            do_update = True
            reason = "force-diverged"
        action = {
            "file": rel_record,
            "status": status,
            "will_update": do_update and not dry_run and regenerated_content is not None,
            "reason": reason,
        }
        if do_update and regenerated_content is None:
            action["will_update"] = False
            action["reason"] = "no_template_content"
        if status in counts:
            counts[status] += 1
        if do_update and action["will_update"]:
            counts["updated"] += 1
        else:
            counts["skipped"] += 1
        if action["will_update"]:
            previous_hash = registry_hash or current_hash
            if dst.exists():
                try:
                    existing_bytes = dst.read_bytes()
                except OSError:
                    existing_bytes = None
                else:
                    with suppress(OSError):
                        store_snapshot(project_root, existing_bytes)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(regenerated_content, encoding="utf-8")
            record_file_hash(
                hash_registry,
                rel_record,
                name,
                config.get("version", "?"),
                (regenerated_content or "").encode("utf-8"),
                previous_hash=previous_hash,
                snapshot=True,
                project_root=project_root,
            )
        actions.append(action)
    save_hashes(project_root, hash_registry)
    return {"module": name, "profile": profile, "summary": counts, "actions": actions}


@upgrade_app.command("module")
def upgrade_module(
    name: str,
    profile: str = typer.Option("fastapi/minimal", help="Profile used when originally adding"),
    project: str = typer.Option(None, help="Project name inside boilerplates"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change without writing"),
    force_modified: bool = typer.Option(
        False, "--force-modified", help="Also overwrite locally_modified files"
    ),
    force_diverged: bool = typer.Option(
        False, "--force-diverged", help="Also overwrite diverged files (last resort)"
    ),
    only_statuses: str = typer.Option("", help="Comma list of statuses eligible for overwrite"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON summary"),
) -> None:
    """Upgrade a single module's generated files.

    By default overwrites only files with status=template_updated.
    Use --force-modified / --force-diverged to expand overwrite set.
    """
    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)
    manifest = load_manifest_or_none(MODULES_PATH, name)
    if manifest:
        print_info(
            f"[bold green]Manifest:[/bold green] {manifest.effective_name} v{manifest.version} [dim]status={manifest.status}[/dim]"
        )
    else:
        print_warning("⚠️ No module.yaml manifest found (legacy mode)")
    try:
        config = load_module_config(name, profile)
    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(code=1) from None
    variables = prompt_for_variables(config.get("variables", {}))
    allowed = (
        {s.strip() for s in only_statuses.split(",") if s.strip()}
        if only_statuses.strip()
        else None
    )
    result = _plan_or_apply_upgrade(
        name,
        profile,
        project_root,
        config,
        variables,
        dry_run,
        force_modified,
        force_diverged,
        allowed_statuses=allowed,
    )
    if json_output:
        result["schema_version"] = "upgrade-v1"
        print(json.dumps(result, indent=2))
        return
    counts = result["summary"]
    for action in result["actions"]:
        if action["will_update"]:
            print_success(f"🛠  Updated: {action['file']} ({action.get('reason','')})")
        else:
            print_info(f"⏭ Skipped: {action['file']} [{action['status']}]")
    print_info("\n[bold magenta]=== Upgrade Summary ===[/bold magenta]")
    for k, v in counts.items():
        print_info(f"{k}: {v}")
    updated = sum(1 for a in result["actions"] if a["will_update"])
    print_success(f"Done. Updated {updated} files.")


@upgrade_app.command("batch")
def upgrade_batch(
    modules: str = typer.Option("*", help="Comma list of modules or * for all"),
    profile: str = typer.Option("fastapi/minimal", help="Profile context"),
    project: str = typer.Option(None, help="Project root name inside boilerplates"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry-run (no writes)"),
    force_modified: bool = typer.Option(
        False, "--force-modified", help="Also overwrite locally_modified"
    ),
    force_diverged: bool = typer.Option(False, "--force-diverged", help="Also overwrite diverged"),
    only_statuses: str = typer.Option("", help="Comma list of statuses eligible for overwrite"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON aggregate"),
) -> None:
    """Upgrade multiple modules in one pass."""
    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)
    if modules.strip() == "*":
        if MODULES_PATH.exists():
            selected = [p.name for p in (MODULES_PATH).iterdir() if (p / "module.yaml").exists()]
        else:
            selected = []
    else:
        selected = [m.strip() for m in modules.split(",") if m.strip()]
    aggregate: List[Dict[str, Any]] = []
    allowed = (
        {s.strip() for s in only_statuses.split(",") if s.strip()}
        if only_statuses.strip()
        else None
    )
    for m in selected:
        try:
            config = load_module_config(m, profile)
        except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
            print_warning(f"Skipping {m}: {e}")
            continue
        vars_cfg = config.get("variables", {})
        variables = {
            k: (v.get("default") if isinstance(v, dict) else None) for k, v in vars_cfg.items()
        }
        result = _plan_or_apply_upgrade(
            m,
            profile,
            project_root,
            config,
            variables,
            dry_run,
            force_modified,
            force_diverged,
            allowed_statuses=allowed,
        )
        aggregate.append(result)
        updated_count = sum(1 for a in result["actions"] if a["will_update"])
        print_info(f"[bold cyan]{m}[/bold cyan]: updated {updated_count} files")
    if json_output:
        print(
            json.dumps(
                {
                    "schema_version": "upgrade-batch-v1",
                    "profile": profile,
                    "results": aggregate,
                },
                indent=2,
            )
        )
    else:
        total_updates = sum(sum(1 for a in r["actions"] if a["will_update"]) for r in aggregate)
        print_success(
            f"Batch complete. Modules processed: {len(aggregate)} | Total updated files: {total_updates}"
        )
