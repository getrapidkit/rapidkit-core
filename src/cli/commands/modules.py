import getpass
import hashlib
import json
import json as _json
import os
import time
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, cast

import typer
from packaging import version as semver
from rich.table import Table

from core.config.version import CURRENT_VERSION
from core.module_sign import verify_manifest_multi
from core.services.config_loader import load_module_config
from core.services.file_hash_registry import (
    _sha256,
    load_hashes,
    load_snapshot,
    record_file_hash,
    save_hashes,
)
from core.services.module_structure_validator import (
    _module_generates_legacy_health_targets,
    validate_module_structure,
)
from core.services.module_validator import load_all_specs, validate_spec
from core.services.vendor_store import load_vendor_file

from ..ui.printer import console, print_error, print_info, print_success, print_warning
from ..utils.filesystem import find_project_root
from ..utils.module_structure_cli import (
    DEFAULT_MODULES_ROOT,
    collect_validation_results,
    ensure_module_validation,
    ensure_structure_spec_ready,
    scaffold_module,
    scaffold_result_to_dict,
    scaffold_summary_lines,
    validation_result_to_dict,
    validation_results_to_dict,
    validation_summary_lines,
)
from ..utils.module_validation import (
    apply_parity_to_verification,
    collect_parity_failures,
    collect_parity_reports,
    parity_reports_to_dict,
    render_parity_table,
)
from ..utils.scaffold.blueprints import list_blueprint_keys

BLUEPRINT_CHOICES = list_blueprint_keys()


yaml: Any
try:
    import yaml as _yaml
except ImportError:  # pragma: no cover
    yaml = None
else:
    yaml = _yaml

yaml_error_type: Type[BaseException] = RuntimeError
if yaml is not None:
    yaml_error_type = cast(
        Type[BaseException],
        getattr(yaml, "YAMLError", RuntimeError),  # noqa: B009 - fallback when attribute missing
    )

YAML_ERROR_TYPES: Tuple[Type[BaseException], ...] = (yaml_error_type,)


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def yaml_dump(data: Any) -> str:
    """Dump data to YAML string, falling back to JSON if yaml is not available."""
    if yaml is not None:
        safe_dump = getattr(yaml, "safe_dump", None)
        if callable(safe_dump):
            extra_exceptions: List[Type[BaseException]] = []
            yaml_error = getattr(yaml, "YAMLError", None)
            if isinstance(yaml_error, type) and issubclass(yaml_error, BaseException):
                extra_exceptions.append(yaml_error)
            with suppress(AttributeError, TypeError, *extra_exceptions):
                return cast(str, safe_dump(data, sort_keys=False, allow_unicode=True))

    # Fallback to JSON if PyYAML is not installed or an error occurs during dumping
    return _json.dumps(data, indent=2, sort_keys=False)


modules_app = typer.Typer(help="Module utilities: summary, validation, signing")

# Module-level default values to avoid B008
DEFAULT_SKIP_UNCHANGED = True
DEFAULT_CI = False
DEFAULT_JSON_OUT = False
DEFAULT_AUDIT_LOG = "sign_audit.log"

DESCRIPTION_TRUNCATE_LIMIT = 60
SHORT_DESCRIPTION_LIMIT = 50
MAX_MODULE_SUGGESTIONS = 10
TRUNCATION_SUFFIX = "..."
SKIPPED_MODULES_DISPLAY_LIMIT = 5


def truncate_text(text: str, limit: int) -> str:
    """Return text truncated to limit while appending the configured suffix."""
    if limit <= len(TRUNCATION_SUFFIX):
        return text[:limit]
    if len(text) <= limit:
        return text
    return text[: limit - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX


def _pretty_module_name(raw: str) -> str:
    cleaned = raw.replace("_", " ").replace("-", " ").strip()
    if not cleaned:
        return raw
    return cleaned.title()


def _load_yaml_dict(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        raise RuntimeError(f"PyYAML is required to parse {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except YAML_ERROR_TYPES as exc:  # pragma: no cover - depends on PyYAML runtime
        raise RuntimeError(f"Failed to parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} must contain a mapping at top level")
    return cast(Dict[str, Any], data)


def _load_verification_metadata(module_dir: Path, filename: Optional[str]) -> Dict[str, Any]:
    if not filename:
        return {}
    path = module_dir / filename
    if not path.exists():
        return {}
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(metadata, dict):
        return {}
    return metadata


def _build_module_record(
    slug: str,
    module_dir: Path,
    manifest: Dict[str, Any],
    config_base: Dict[str, Any],
    tree_hash: Optional[str],
    spec_version: int,
    verification_file: Optional[str],
    checked_at: Optional[str],
) -> Dict[str, Any]:
    segments = slug.split("/")
    tier = segments[0] if segments else ""
    category = segments[1] if len(segments) > 1 else ""
    name = str(manifest.get("name") or config_base.get("name") or segments[-1])
    display_name = str(
        config_base.get("display_name") or manifest.get("display_name") or _pretty_module_name(name)
    )
    version = str(manifest.get("version") or config_base.get("version") or "0.0.0")
    status = str(manifest.get("status") or "unknown")
    tier_value = str(manifest.get("tier") or tier or "free")
    tags_raw = manifest.get("tags") or []
    tags = [str(tag) for tag in tags_raw if isinstance(tag, str)]
    capabilities_raw = manifest.get("capabilities") or []
    capabilities = [str(cap) for cap in capabilities_raw if isinstance(cap, str)]
    description = str(config_base.get("description") or manifest.get("description") or "")

    return {
        "slug": slug,
        "name": name,
        "display_name": display_name,
        "version": version,
        "category": category,
        "tier": tier_value,
        "status": status,
        "description": description,
        "tags": tags,
        "capabilities": capabilities,
        "module_path": module_dir.as_posix(),
        "validation": {
            "valid": True,
            "spec_version": spec_version,
            "tree_hash": tree_hash,
            "verification_file": verification_file,
            "verification_path": (
                (module_dir / verification_file).as_posix() if verification_file else None
            ),
            "checked_at": checked_at,
        },
    }


def _discover_free_manifest_paths(modules_root: Path) -> List[Path]:
    return sorted(modules_root.glob("free/*/*/module.yaml"))


def _module_matches_filter(recorded: Optional[str], requested: Optional[str]) -> bool:
    if not requested:
        return True
    if not recorded:
        return False
    requested_norm = requested.strip()
    if not requested_norm:
        return True
    if recorded == requested_norm:
        return True
    return recorded.endswith(f"/{requested_norm}")


@modules_app.command("status")
def modules_status(
    module: Optional[str] = typer.Argument(
        None,
        help="Limit report to a specific module name (accepts either 'tier/name' or plain name).",
    ),
    project: Optional[str] = typer.Option(
        None, help="Project name inside boilerplates (defaults to current working directory)."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine readable JSON output."),
) -> None:
    """Report per-file status for installed modules within a project."""

    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    registry = load_hashes(project_root)
    files_meta: Dict[str, Any] = registry.get("files", {}) or {}

    records: List[Dict[str, Any]] = []
    for rel_path, meta in sorted(files_meta.items()):
        if not isinstance(meta, dict):
            continue
        recorded_module = cast(Optional[str], meta.get("module"))
        if not _module_matches_filter(recorded_module, module):
            continue

        abs_path = project_root / rel_path
        current_hash = meta.get("hash") if isinstance(meta.get("hash"), str) else None
        current_snapshot = (
            load_snapshot(project_root, current_hash) is not None if current_hash else False
        )
        previous_hash = (
            meta.get("previous_hash") if isinstance(meta.get("previous_hash"), str) else None
        )
        previous_snapshot = (
            load_snapshot(project_root, previous_hash) is not None if previous_hash else False
        )
        recorded_version = meta.get("version") if isinstance(meta.get("version"), str) else None

        if abs_path.exists():
            try:
                bytes_content = abs_path.read_bytes()
            except OSError:
                status = "unreadable"
                computed_hash = None
            else:
                computed_hash = _sha256(bytes_content)
                status = "clean" if current_hash and computed_hash == current_hash else "modified"
        else:
            status = "missing"
            computed_hash = None

        vendor_bytes = load_vendor_file(project_root, recorded_module, recorded_version, rel_path)
        vendor_hash = _sha256(vendor_bytes) if vendor_bytes is not None else None
        matches_vendor = bool(vendor_hash and computed_hash and vendor_hash == computed_hash)

        recoverable = status == "clean" or (
            current_hash is not None and (status in {"modified", "missing"}) and current_snapshot
        )
        if not recoverable and vendor_bytes is not None:
            recoverable = True

        records.append(
            {
                "file": rel_path,
                "module": recorded_module,
                "version": recorded_version,
                "status": status,
                "recorded_hash": current_hash,
                "computed_hash": computed_hash,
                "current_snapshot": current_snapshot,
                "previous_snapshot": previous_snapshot,
                "vendor_available": vendor_bytes is not None,
                "vendor_hash": vendor_hash,
                "matches_vendor": matches_vendor,
                "recoverable": recoverable,
            }
        )

    if module and not any(_module_matches_filter(r.get("module"), module) for r in records):
        print_warning(f"⚠️ No tracked files found for module '{module}'.")

    if json_output:
        summary = {
            "project": str(project_root),
            "module": module,
            "files": records,
            "counts": {
                "clean": sum(1 for r in records if r["status"] == "clean"),
                "modified": sum(1 for r in records if r["status"] == "modified"),
                "missing": sum(1 for r in records if r["status"] == "missing"),
                "unreadable": sum(1 for r in records if r["status"] == "unreadable"),
            },
        }
        print(json.dumps(summary, indent=2))
        return

    if not records:
        print_info("No tracked module files found in this project.")
        return

    table = Table(title="Module file status", show_header=True, header_style="bold cyan")
    table.add_column("File", style="white", overflow="fold")
    table.add_column("Module", style="magenta")
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Snapshots", style="green")
    table.add_column("Vendor", style="cyan")

    for entry in records:
        snap_badge = []
        snap_badge.append("cur✓" if entry["current_snapshot"] else "cur✗")
        snap_badge.append("prev✓" if entry["previous_snapshot"] else "prev✗")
        vendor_badge = "—"
        if entry["vendor_available"]:
            vendor_badge = "match" if entry["matches_vendor"] else "drift"

        table.add_row(
            entry["file"],
            entry.get("module") or "—",
            str(entry.get("version") or "—"),
            entry["status"],
            "/".join(snap_badge),
            vendor_badge,
        )

    console.print(table)

    totals = {
        "clean": sum(1 for r in records if r["status"] == "clean"),
        "modified": sum(1 for r in records if r["status"] == "modified"),
        "missing": sum(1 for r in records if r["status"] == "missing"),
        "unreadable": sum(1 for r in records if r["status"] == "unreadable"),
    }

    print_info(
        "Summary — Clean: {clean}, Modified: {modified}, Missing: {missing}, Unreadable: {unreadable}".format(
            **totals
        )
    )


@modules_app.command("scaffold")
def modules_scaffold(
    name: str = typer.Argument(..., help="Module name (snake-case)."),
    category: str = typer.Option(
        "core",
        "--category",
        "-c",
        help="Module category path under the tier (default: core).",
    ),
    tier: str = typer.Option(
        "free",
        "--tier",
        "-t",
        help="Module tier (free, pro, enterprise, ...).",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Optional description used in README and metadata.",
    ),
    blueprint: str = typer.Option(
        "baseline",
        "--blueprint",
        "-b",
        help=f"Blueprint profile applied to the scaffold. Choices: {', '.join(BLUEPRINT_CHOICES)}.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files when the module directory already exists.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview generated files without writing to disk.",
    ),
    modules_root: Path = typer.Option(  # noqa: B008
        DEFAULT_MODULES_ROOT,
        "--modules-root",
        help="Root directory where modules live (default: src/modules).",
        resolve_path=True,
        show_default=False,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine readable JSON output instead of human readable text.",
    ),
) -> None:
    """Scaffold a RapidKit module using the shared ModuleScaffolder."""

    try:
        result = scaffold_module(
            tier=tier,
            category=category,
            module_name=name,
            description=description,
            blueprint=blueprint,
            force=force,
            dry_run=dry_run,
            modules_root=modules_root,
        )
    except ValueError as exc:
        print_error(f"❌ {exc}")
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(scaffold_result_to_dict(result, dry_run), indent=2))
        return

    for line in scaffold_summary_lines(result, dry_run):
        console.print(line)
    if not dry_run:
        print_success("Module scaffold complete.")


@modules_app.command("diff")
def modules_diff(
    module: Optional[str] = typer.Argument(
        None,
        help="Limit diff to a specific module name (accepts either 'tier/name' or plain name).",
    ),
    from_version: Optional[str] = typer.Option(
        None, "--from", help="Source version to compare from (recorded hash if not specified)."
    ),
    to_version: Optional[str] = typer.Option(
        None, "--to", help="Target version to compare to (current files if not specified)."
    ),
    project: Optional[str] = typer.Option(
        None, help="Project name inside boilerplates (defaults to current working directory)."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine readable JSON output."),
) -> None:
    """Show differences between module versions or current vs recorded state."""

    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    registry = load_hashes(project_root)
    files_meta: Dict[str, Any] = registry.get("files", {}) or {}

    changes: List[Dict[str, Any]] = []

    for rel_path, meta in sorted(files_meta.items()):
        if not isinstance(meta, dict):
            continue
        recorded_module = cast(Optional[str], meta.get("module"))
        if not _module_matches_filter(recorded_module, module):
            continue

        abs_path = project_root / rel_path
        recorded_version = meta.get("version") if isinstance(meta.get("version"), str) else None
        current_hash = meta.get("hash") if isinstance(meta.get("hash"), str) else None

        # Determine what to compare
        from_hash = None
        to_hash = None
        from_content = None
        to_content = None

        # Get "from" content
        if from_version:
            # Compare specific versions via vendor files
            from_content = load_vendor_file(project_root, recorded_module, from_version, rel_path)
            if from_content is not None:
                from_hash = _sha256(from_content)
        elif current_hash:
            # Compare recorded vs current
            snapshot = load_snapshot(project_root, current_hash)
            if snapshot:
                from_content = snapshot
                from_hash = current_hash

        # Get "to" content
        if to_version:
            # Compare to specific version via vendor files
            to_content = load_vendor_file(project_root, recorded_module, to_version, rel_path)
            if to_content is not None:
                to_hash = _sha256(to_content)
        elif abs_path.exists():
            # Compare to current file
            try:
                to_content = abs_path.read_bytes()
                to_hash = _sha256(to_content)
            except OSError:
                to_content = None

        # Determine change type
        change_type = "unchanged"
        if from_content != to_content:
            if from_content is None and to_content is not None:
                change_type = "added"
            elif from_content is not None and to_content is None:
                change_type = "removed"
            elif from_content is not None and to_content is not None:
                change_type = "modified"

        if change_type != "unchanged":
            changes.append(
                {
                    "file": rel_path,
                    "module": recorded_module,
                    "version": recorded_version,
                    "change_type": change_type,
                    "from_hash": from_hash,
                    "to_hash": to_hash,
                    "from_version": from_version,
                    "to_version": to_version or "current",
                }
            )

    if json_output:
        print(
            json.dumps(
                {
                    "project": str(project_root),
                    "module": module,
                    "from_version": from_version,
                    "to_version": to_version,
                    "changes": changes,
                    "counts": {
                        "added": sum(1 for c in changes if c["change_type"] == "added"),
                        "removed": sum(1 for c in changes if c["change_type"] == "removed"),
                        "modified": sum(1 for c in changes if c["change_type"] == "modified"),
                    },
                },
                indent=2,
            )
        )
        return

    if not changes:
        if from_version or to_version:
            print_info(
                f"✅ No differences found between {from_version or 'recorded'} and {to_version or 'current'}."
            )
        else:
            print_info("✅ All files match recorded state.")
        return

    table = Table(title="Module file differences", show_header=True, header_style="bold cyan")
    table.add_column("File", style="white", overflow="fold")
    table.add_column("Module", style="magenta")
    table.add_column("Change", style="yellow")
    table.add_column("From", style="red")
    table.add_column("To", style="green")

    for change in changes:
        from_desc = change["from_version"] or "recorded"
        to_desc = change["to_version"]

        table.add_row(
            change["file"],
            change.get("module") or "—",
            change["change_type"].upper(),
            from_desc,
            to_desc,
        )

    console.print(table)

    totals = {
        "added": sum(1 for c in changes if c["change_type"] == "added"),
        "removed": sum(1 for c in changes if c["change_type"] == "removed"),
        "modified": sum(1 for c in changes if c["change_type"] == "modified"),
    }

    print_info(
        "Summary — Added: {added}, Removed: {removed}, Modified: {modified}".format(**totals)
    )


@modules_app.command("apply")
def modules_apply(
    module: str = typer.Argument(
        ..., help="Module name to apply updates for (accepts either 'tier/name' or plain name)."
    ),
    target_version: str = typer.Option(..., "--target", help="Target version to apply."),
    project: Optional[str] = typer.Option(
        None, help="Project name inside boilerplates (defaults to current working directory)."
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run/--no-dry-run", help="Show what would be changed without applying."
    ),
    force: bool = typer.Option(
        False, "--force", help="Force apply even when conflicts are detected."
    ),
) -> None:
    """Apply module updates to target version."""

    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    print_info(f"🔄 Applying {module} to version {target_version}...")
    if dry_run:
        print_info("📋 DRY RUN - No changes will be made")
    if force:
        print_warning("⚠️ FORCE mode enabled - conflicts will be overwritten")

    # Load current registry
    registry = load_hashes(project_root)
    files_meta: Dict[str, Any] = registry.get("files", {}) or {}

    # Validate target version exists by checking if any vendor files exist for this module/version
    target_files: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    changes: List[Dict[str, Any]] = []

    for rel_path, meta in files_meta.items():
        if not isinstance(meta, dict):
            continue
        recorded_module = cast(Optional[str], meta.get("module"))
        if not _module_matches_filter(recorded_module, module):
            continue

        abs_path = project_root / rel_path
        recorded_version = meta.get("version") if isinstance(meta.get("version"), str) else None
        current_hash = meta.get("hash") if isinstance(meta.get("hash"), str) else None

        # Check if target version vendor file exists
        target_content = load_vendor_file(project_root, recorded_module, target_version, rel_path)
        if target_content is None:
            print_warning(f"⚠️ Target version {target_version} not available for {rel_path}")
            continue

        target_hash = _sha256(target_content)
        target_files.append(
            {
                "rel_path": rel_path,
                "abs_path": abs_path,
                "recorded_version": recorded_version,
                "current_hash": current_hash,
                "target_hash": target_hash,
                "target_content": target_content,
            }
        )

        # Check current file state
        current_content = None
        current_computed_hash = None
        if abs_path.exists():
            try:
                current_content = abs_path.read_bytes()
                current_computed_hash = _sha256(current_content)
            except OSError:
                pass

        # Determine if file was modified
        is_modified = (
            current_hash != current_computed_hash
            if current_hash and current_computed_hash
            else False
        )
        is_missing = not abs_path.exists()

        # Check for conflicts (modified files that would be overwritten)
        if is_modified and target_hash != current_computed_hash:
            conflicts.append(
                {
                    "file": rel_path,
                    "reason": "modified",
                    "current_hash": current_computed_hash,
                    "target_hash": target_hash,
                }
            )
        elif is_missing:
            conflicts.append(
                {
                    "file": rel_path,
                    "reason": "missing",
                    "current_hash": None,
                    "target_hash": target_hash,
                }
            )

        # Determine change type
        change_type = "unchanged"
        if target_hash != current_hash:
            if current_hash is None:
                change_type = "added"
            elif target_content != current_content:
                change_type = "modified"

        if change_type != "unchanged":
            changes.append(
                {
                    "file": rel_path,
                    "change_type": change_type,
                    "from_version": recorded_version,
                    "to_version": target_version,
                    "from_hash": current_hash,
                    "to_hash": target_hash,
                }
            )

    if not target_files:
        print_error(f"❌ No files found for module '{module}' at version {target_version}")
        raise typer.Exit(code=1)

    # Report conflicts
    if conflicts and not force:
        print_error(f"❌ {len(conflicts)} conflict(s) detected:")
        for conflict in conflicts:
            print_error(f"  • {conflict['file']} ({conflict['reason']})")
        print_error("💡 Use --force to overwrite conflicts or resolve them manually")
        raise typer.Exit(code=1)

    if conflicts and force:
        print_warning(f"⚠️ Overwriting {len(conflicts)} conflict(s) due to --force flag")

    # Show changes
    if changes:
        table = Table(title="Changes to apply", show_header=True, header_style="bold cyan")
        table.add_column("File", style="white", overflow="fold")
        table.add_column("Change", style="yellow")
        table.add_column("From", style="red")
        table.add_column("To", style="green")

        for change in changes:
            table.add_row(
                change["file"],
                change["change_type"].upper(),
                change["from_version"] or "none",
                change["to_version"],
            )

        console.print(table)

        totals = {
            "added": sum(1 for c in changes if c["change_type"] == "added"),
            "modified": sum(1 for c in changes if c["change_type"] == "modified"),
        }
        print_info(f"Summary — Added: {totals['added']}, Modified: {totals['modified']}")
    else:
        print_info("✅ No changes needed - already at target version")

    if dry_run:
        print_info("💡 Use --no-dry-run to apply these changes")
        return

    # Apply changes
    print_info("🔄 Applying changes...")

    # Update files and registry
    for file_info in target_files:
        rel_path = cast(str, file_info["rel_path"])
        abs_path = cast(Path, file_info["abs_path"])
        target_content = cast(bytes, file_info["target_content"])
        target_hash = cast(str, file_info["target_hash"])
        current_hash = cast(Optional[str], file_info["current_hash"])

        # Write new content
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(target_content)

        # Update registry
        record_file_hash(
            registry,
            rel_path,
            module,
            target_version,
            target_content,
            previous_hash=current_hash,
            snapshot=True,
            project_root=project_root,
        )

    # Save updated registry
    save_hashes(project_root, registry)

    print_success(f"✅ Successfully applied {module} to version {target_version}")
    print_info("📸 Snapshots created for rollback capability")


@modules_app.command("snapshot")
def modules_snapshot(
    module: Optional[str] = typer.Argument(
        None,
        help="Limit snapshot to a specific module name (accepts either 'tier/name' or plain name).",
    ),
    project: Optional[str] = typer.Option(
        None, help="Project name inside boilerplates (defaults to current working directory)."
    ),
) -> None:
    """Create snapshots of current module file states."""

    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    print_info(f"📸 Creating snapshots for {module or 'all modules'}...")

    # Load current registry
    registry = load_hashes(project_root)
    files_meta: Dict[str, Any] = registry.get("files", {}) or {}

    snapshots_created = 0
    snapshots_skipped = 0

    for rel_path, meta in sorted(files_meta.items()):
        if not isinstance(meta, dict):
            continue
        recorded_module = cast(Optional[str], meta.get("module"))
        if not _module_matches_filter(recorded_module, module):
            continue

        abs_path = project_root / rel_path
        # Check if file exists and get current content
        if not abs_path.exists():
            print_warning(f"⚠️ Skipping {rel_path} - file does not exist")
            snapshots_skipped += 1
            continue

        try:
            current_content = abs_path.read_bytes()
        except OSError as e:
            print_warning(f"⚠️ Skipping {rel_path} - cannot read file: {e}")
            snapshots_skipped += 1
            continue

        computed_hash = _sha256(current_content)

        # Check if snapshot already exists
        from core.services.file_hash_registry import load_snapshot

        existing_snapshot = load_snapshot(project_root, computed_hash)
        if existing_snapshot is not None:
            # Snapshot already exists, no need to recreate
            snapshots_skipped += 1
            continue

        # Create new snapshot
        from core.services.file_hash_registry import store_snapshot

        stored_hash = store_snapshot(project_root, current_content)

        # Update registry entry with snapshot reference and metadata
        meta_copy = dict(meta)  # Create a copy to avoid modifying the original
        meta_copy["snapshot_hash"] = stored_hash
        meta_copy["snapshot_created"] = datetime.now(timezone.utc).isoformat()
        meta_copy["snapshot_message"] = (
            f"Snapshot created via CLI for {recorded_module or 'unknown module'}"
        )

        # Update the registry
        files_meta[rel_path] = meta_copy

        snapshots_created += 1
        print_info(f"� Created snapshot for {rel_path}")

    # Save updated registry
    from core.services.file_hash_registry import save_hashes

    save_hashes(project_root, registry)

    print_success(f"✅ Created {snapshots_created} snapshots")
    if snapshots_skipped > 0:
        print_info(f"⏭️ Skipped {snapshots_skipped} files (already have snapshots or unavailable)")


@modules_app.command("sign-all")
def sign_all(
    private_key: str = typer.Option(..., help="Ed25519 private key (base64)"),
    skip_unchanged: bool = DEFAULT_SKIP_UNCHANGED,
    ci: bool = DEFAULT_CI,
    json_out: bool = DEFAULT_JSON_OUT,
    audit_log: str = DEFAULT_AUDIT_LOG,
) -> None:
    """Sign all modules with Ed25519 key, skipping unchanged if desired. Logs all events."""
    if not MODULES_PATH.exists():
        print_error("Modules root not found")
        raise typer.Exit(1)
    import hashlib
    import time

    results = []
    audit_entries = []
    errors = 0
    audit_log_path = os.environ.get("RAPIDKIT_AUDIT_LOG", audit_log)
    user = getpass.getuser()
    for module_dir in sorted(MODULES_PATH.iterdir()):
        if not module_dir.is_dir():
            continue
        mf = module_dir / "module.yaml"
        if not mf.exists():
            continue
        try:
            with mf.open(encoding="utf-8") as f:
                manifest = yaml.safe_load(f) if yaml is not None else _json.load(f)
        except (OSError, ValueError, RuntimeError, AttributeError) as e:
            results.append({"module": module_dir.name, "status": "error", "error": str(e)})
            errors += 1
            continue

        # Collect file hashes (reuse logic from scripts/module_signer.py)

        def collect_files(module_dir: Path, manifest: Dict[str, Any]) -> Dict[str, str]:
            file_hashes: Dict[str, str] = {}
            # 1. config_sources
            for rel in manifest.get("config_sources", []):
                p = module_dir / rel
                if p.exists() and p.is_file():
                    file_hashes[rel] = hash_file(p)
            # 2. overrides (fastapi.yaml)
            overrides_path = module_dir / "config/overrides/fastapi.yaml"
            if overrides_path.exists():
                try:
                    text = overrides_path.read_text(encoding="utf-8")
                    overrides = None
                    if yaml is not None:
                        try:
                            overrides = yaml.safe_load(text)
                        except YAML_ERROR_TYPES:
                            overrides = None
                    if overrides is None:
                        try:
                            overrides = _json.loads(text)
                        except _json.JSONDecodeError:
                            overrides = {}
                    for flavor, variants in (
                        overrides.get("files", {}).get("overrides", {}) or {}
                    ).items():
                        for variant, files in variants.items():
                            for entry in files:
                                rel_path = entry["path"] if isinstance(entry, dict) else entry
                                p = module_dir / rel_path
                                if p.exists() and p.is_file():
                                    file_hashes[f"overrides/{flavor}/{variant}/{rel_path}"] = (
                                        hash_file(p)
                                    )
                except (OSError, AttributeError):
                    pass
            # 3. templates/ (recursive)
            templates_dir = module_dir / "templates"
            if templates_dir.exists() and templates_dir.is_dir():
                for root, _dirs, files in os.walk(templates_dir):
                    for fname in files:
                        fpath = Path(root) / fname
                        rel = str(fpath.relative_to(module_dir))
                        if fpath.is_file():
                            file_hashes[rel] = hash_file(fpath)
            return file_hashes

        file_hashes = collect_files(module_dir, manifest)
        manifest["file_hashes"] = file_hashes
        # Multi-signer: signers field (list of public keys, base64)
        signers = manifest.get("signers")
        if not signers:
            # Try to load from signing.pub or .pubs file
            pub_path = module_dir / "signing.pub"
            if pub_path.exists():
                pubkey = pub_path.read_text(encoding="utf-8").strip()
                signers = [pubkey]
                manifest["signers"] = signers
        # Remove signature and signature-related fields before signing
        manifest_for_sign = dict(manifest)
        for k in ["signature", "signer_id", "signature_version"]:
            manifest_for_sign.pop(k, None)
        manifest_json = _json.dumps(manifest_for_sign, sort_keys=True)
        prev_sig = manifest.get("signature")
        prev_signer_id = manifest.get("signer_id")
        prev_sig_ver = manifest.get("signature_version")
        unchanged = False
        # Multi-signer skip logic: verify with any signer
        if skip_unchanged and prev_sig and signers:
            try:
                sig_obj = {
                    "signature": prev_sig,
                    "signer_id": prev_signer_id,
                    "signature_version": prev_sig_ver or "v1",
                }
                manifest_for_verify = dict(manifest)
                for k in ["signature", "signer_id", "signature_version"]:
                    manifest_for_verify.pop(k, None)
                manifest_json_verify = _json.dumps(manifest_for_verify, sort_keys=True)
                if verify_manifest_multi(manifest_json_verify, sig_obj, signers):
                    unchanged = True
            except (OSError, ValueError, RuntimeError) as e:
                raise RuntimeError(
                    f"Error verifying previous signature for {module_dir.name}"
                ) from e
        if unchanged:
            results.append({"module": module_dir.name, "status": "skipped", "reason": "unchanged"})
            continue
        try:
            # use absolute import so mypy and tools can resolve the module
            from core.module_sign import sign_manifest

            sig_obj = sign_manifest(manifest_json, private_key, signature_version="v1")
            manifest["signature"] = sig_obj["signature"]
            manifest["signer_id"] = sig_obj["signer_id"]
            manifest["signature_version"] = sig_obj["signature_version"]
            # Ensure current public key is in signers
            sk = private_key
            import base64

            import nacl.signing

            pk = nacl.signing.SigningKey(base64.b64decode(sk)).verify_key
            pubkey = base64.b64encode(pk.encode()).decode("utf-8")
            if "signers" not in manifest:
                manifest["signers"] = [pubkey]
            elif pubkey not in manifest["signers"]:
                manifest["signers"].append(pubkey)
            with mf.open("w", encoding="utf-8") as f:
                if yaml is not None:
                    yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True)
                else:
                    _json.dump(manifest, f, indent=2)
            results.append({"module": module_dir.name, "status": "signed"})
            audit_entries.append(
                {
                    "event": "sign",
                    "module": module_dir.name,
                    "timestamp": time.time(),
                    "user": user,
                    "status": "signed",
                    "signer_id": sig_obj["signer_id"],
                    "signature_version": sig_obj["signature_version"],
                    "hash": hashlib.sha256(manifest_json.encode("utf-8")).hexdigest(),
                }
            )
        except (OSError, ValueError, RuntimeError) as e:
            results.append({"module": module_dir.name, "status": "error", "error": str(e)})
            errors += 1
    # Write audit log
    try:
        with open(audit_log_path, "a", encoding="utf-8") as f:
            for entry in audit_entries:
                f.write(_json.dumps(entry) + "\n")
    except OSError:
        pass
    if json_out or ci:
        print(_json.dumps({"results": results, "errors": errors}))
    else:
        for r in results:
            if r["status"] == "signed":
                print_success(f"✅ Signed: {r['module']}")
            elif r["status"] == "skipped":
                print_success(f"⏩ Skipped (unchanged): {r['module']}")
            else:
                print_error(f"❌ {r['module']}: {r.get('error')}")
    if errors:
        raise typer.Exit(2)
    print_success(
        f"All modules processed. Signed: {len([r for r in results if r['status']=='signed'])}, Skipped: {len([r for r in results if r['status']=='skipped'])}"
    )


@modules_app.command("verify-all")
def verify_all(
    public_keys: Optional[str] = typer.Option(
        None,
        help="Comma-separated list of Ed25519 public keys (base64) for multi-signer",
    ),
    ci: bool = typer.Option(False, "--ci", help="CI mode: JSON output, nonzero exit on error"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON output"),
    skip_signature: bool = typer.Option(
        False, "--skip-signature", help="Skip signature verification (development only)"
    ),
) -> None:
    """Verify all module signatures and hashes (multi-signer aware)."""
    if not MODULES_PATH.exists():
        print_error("Modules root not found")
        raise typer.Exit(1)

    from core.module_sign import verify_manifest_multi

    audit_log_path = os.environ.get("RAPIDKIT_AUDIT_LOG", "audit.log")
    user = getpass.getuser()
    verify_audit = []

    results = []
    errors = 0
    # Load allowed signer_ids from policy file or env
    allowed_signer_ids = None
    policy_path = os.environ.get("RAPIDKIT_SIGNER_POLICY", "signer_policy.json")
    if os.path.exists(policy_path):
        try:
            with open(policy_path, "r", encoding="utf-8") as pf:
                allowed_signer_ids = set(_json.load(pf).get("allowed_signer_ids", []))
        except OSError as e:
            if not json_out and not ci:
                print_warning(f"Policy file error: {e}")
    else:
        allowed_signer_ids_env = os.environ.get("RAPIDKIT_ALLOWED_SIGNER_IDS")
        if allowed_signer_ids_env:
            allowed_signer_ids = {s.strip() for s in allowed_signer_ids_env.split(",") if s.strip()}

    for module_dir in sorted(MODULES_PATH.iterdir()):
        if not module_dir.is_dir():
            continue
        mf = module_dir / "module.yaml"
        if not mf.exists():
            continue
        if yaml is not None:
            try:
                with mf.open(encoding="utf-8") as f:
                    manifest_text = f.read()
            except (OSError, AttributeError, ValueError, RuntimeError) as exc:
                results.append({"module": module_dir.name, "status": "error", "error": str(exc)})
                errors += 1
                continue
            try:
                manifest = yaml.safe_load(manifest_text)
            except YAML_ERROR_TYPES as exc:
                results.append({"module": module_dir.name, "status": "error", "error": str(exc)})
                errors += 1
                continue
        else:
            try:
                with mf.open(encoding="utf-8") as f:
                    manifest = _json.load(f)
            except (OSError, ValueError, RuntimeError, AttributeError) as exc:
                results.append({"module": module_dir.name, "status": "error", "error": str(exc)})
                errors += 1
                continue
        # Remove signature and signature-related fields before verification
        manifest_for_verify = dict(manifest)
        for k in ["signature", "signer_id", "signature_version"]:
            manifest_for_verify.pop(k, None)
        manifest_json = _json.dumps(manifest_for_verify, sort_keys=True)
        sig = manifest.get("signature")
        signer_id = manifest.get("signer_id")
        sig_ver = manifest.get("signature_version", "v1")
        signers = manifest.get("signers") or []
        # If the user provided public_keys, only allow those
        if public_keys:
            pubkeys = [k.strip() for k in public_keys.split(",") if k.strip()]
        else:
            pubkeys = signers
        if not sig:
            results.append({"module": module_dir.name, "status": "missing_signature"})
            errors += 1
            continue
        try:
            sig_obj = {
                "signature": sig,
                "signer_id": signer_id,
                "signature_version": sig_ver,
            }
            # If a policy is active, only accept allowed signer_ids
            if allowed_signer_ids is not None and signer_id not in allowed_signer_ids:
                results.append(
                    {
                        "module": module_dir.name,
                        "status": "forbidden_signer",
                        "signer_id": signer_id,
                        "signature_version": sig_ver,
                        "policy": "forbidden",
                    }
                )
                errors += 1
                continue
            # Skip signature verification if requested
            if skip_signature:
                ok = True
                if not json_out and not ci:
                    print_warning(
                        f"⚠️ Skipping signature verification for {module_dir.name} (--skip-signature)"
                    )
            else:
                ok = verify_manifest_multi(manifest_json, sig_obj, pubkeys)
            event = {
                "event": "verify",
                "module": module_dir.name,
                "timestamp": time.time(),
                "user": user,
                "signer_id": signer_id,
                "signature_version": sig_ver,
            }
            if ok:
                results.append(
                    {
                        "module": module_dir.name,
                        "status": "valid",
                        "signer_id": signer_id,
                        "signature_version": sig_ver,
                    }
                )
                event["status"] = "valid"
            else:
                results.append(
                    {
                        "module": module_dir.name,
                        "status": "invalid_signature",
                        "signer_id": signer_id,
                        "signature_version": sig_ver,
                    }
                )
                event["status"] = "invalid_signature"
                errors += 1
            verify_audit.append(event)
        except OSError as e:
            results.append({"module": module_dir.name, "status": "error", "error": str(e)})
            errors += 1
    try:
        with open(audit_log_path, "a", encoding="utf-8") as f:
            for entry in verify_audit:
                f.write(_json.dumps(entry) + "\n")
    except OSError:
        pass
    if json_out or ci:
        print(_json.dumps({"results": results, "errors": errors}))
    else:
        for r in results:
            if r["status"] == "valid":
                print_success(
                    f"✅ Valid: {r['module']}  [signer: {r.get('signer_id','?')}] [ver: {r.get('signature_version','?')}]"
                )
            elif r["status"] == "missing_signature":
                print_warning(f"⚠️ No signature: {r['module']}")
            elif r["status"] == "forbidden_signer":
                print_error(
                    f"⛔ Forbidden signer: {r['module']}  [signer: {r.get('signer_id','?')}] (policy)"
                )
            elif r["status"] == "invalid_signature":
                print_error(
                    f"❌ Invalid signature: {r['module']}  [signer: {r.get('signer_id','?')}] [ver: {r.get('signature_version','?')}]"
                )
            else:
                print_error(f"❌ {r['module']}: {r.get('error')}")
        print_success(
            f"All modules verified. Valid: {len([r for r in results if r['status']=='valid'])}, Errors: {errors}"
        )
    if errors:
        raise typer.Exit(2)


@modules_app.command("list")
def modules_list(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed info"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine readable JSON output."),
) -> None:
    """
    📋 List spec-compliant free-tier modules discovered in the workspace.

    The listing is derived from actual module directories (`src/modules/free/...`). Entries are
    included only when the structure validator reports a valid `module.verify.json` snapshot.

    Examples:
      rapidkit modules list
      rapidkit modules list --category core
      rapidkit modules list --tag auth
      rapidkit modules list --detailed
    """
    modules_root = MODULES_PATH
    manifest_paths = _discover_free_manifest_paths(modules_root)

    if not manifest_paths:
        print_warning("😕 No free-tier modules discovered under src/modules/free.")
        return

    records: List[Dict[str, Any]] = []
    invalid_modules: List[Tuple[str, List[str]]] = []

    for manifest_path in manifest_paths:
        try:
            slug = manifest_path.parent.relative_to(modules_root).as_posix()
        except ValueError:
            continue

        validation = validate_module_structure(slug, modules_root=modules_root)
        if not validation.valid:
            invalid_modules.append((slug, validation.messages))
            continue

        try:
            manifest_data = _load_yaml_dict(manifest_path)
        except RuntimeError as exc:
            invalid_modules.append((slug, [str(exc)]))
            continue

        try:
            config_base = _load_yaml_dict(manifest_path.parent / "config" / "base.yaml")
        except RuntimeError:
            config_base = {}

        verification_meta = _load_verification_metadata(
            manifest_path.parent, validation.verification_file
        )

        record = _build_module_record(
            slug=slug,
            module_dir=manifest_path.parent,
            manifest=manifest_data,
            config_base=config_base,
            tree_hash=validation.tree_hash,
            spec_version=validation.spec_version,
            verification_file=validation.verification_file,
            checked_at=verification_meta.get("checked_at") if verification_meta else None,
        )
        record["validation"]["messages"] = validation.messages
        records.append(record)

    records.sort(key=lambda r: ((r.get("category") or ""), (r.get("display_name") or "").lower()))

    filtered = list(records)
    if category:
        category_lower = category.lower()
        filtered = [
            rec for rec in filtered if str(rec.get("category", "")).lower() == category_lower
        ]

    if tag:
        tag_lower = tag.lower()
        filtered = [
            rec
            for rec in filtered
            if any(tag_lower == t.lower() for t in rec.get("tags", []) if isinstance(t, str))
        ]

    if not filtered:
        print_warning("😕 No standard modules matched the provided filters.")
        if invalid_modules and not json_output:
            skipped = ", ".join(slug for slug, _ in invalid_modules[:SKIPPED_MODULES_DISPLAY_LIMIT])
            if len(invalid_modules) > SKIPPED_MODULES_DISPLAY_LIMIT:
                skipped += ", ..."
            print_warning(
                f"Skipped {len(invalid_modules)} module(s) failing structure validation: {skipped}"
            )
        return

    if json_output:
        if detailed:
            console.print_json(json.dumps(filtered, indent=2))
            return

        payload: List[Dict[str, Any]] = []
        for rec in filtered:
            description_text = rec.get("description") or ""
            payload.append(
                {
                    "name": rec.get("name"),
                    "display_name": rec.get("display_name"),
                    "version": rec.get("version"),
                    "category": rec.get("category"),
                    "status": rec.get("status"),
                    "description": truncate_text(description_text, DESCRIPTION_TRUNCATE_LIMIT),
                    "tags": rec.get("tags", []),
                    "slug": rec.get("slug"),
                    "validation": rec.get("validation"),
                }
            )
        console.print_json(json.dumps(payload, indent=2))
        return

    if detailed:
        for rec in filtered:
            console.rule(
                f"[bold blue]📦 {rec.get('display_name', rec.get('name', 'Unknown'))}[/bold blue]"
            )
            console.print(f"[bold]Slug:[/bold] {rec.get('slug')}")
            console.print(f"[bold]Name:[/bold] {rec.get('name')}")
            console.print(f"[bold]Version:[/bold] {rec.get('version')}")
            console.print(f"[bold]Category:[/bold] {rec.get('category')}")
            console.print(f"[bold]Tier:[/bold] {rec.get('tier')}")
            console.print(f"[bold]Status:[/bold] {rec.get('status')}")
            tags_line = ", ".join(rec.get("tags", []))
            if tags_line:
                console.print(f"[bold]Tags:[/bold] {tags_line}")
            caps_line = ", ".join(rec.get("capabilities", []))
            if caps_line:
                console.print(f"[bold]Capabilities:[/bold] {caps_line}")
            description_text = rec.get("description")
            if description_text:
                console.print(f"[bold]Description:[/bold] {description_text}")
            console.print(f"[bold]Path:[/bold] {rec.get('module_path')}")

            validation = rec.get("validation", {})
            console.print(
                "[bold]Validation:[/bold] spec v{spec} | tree {tree}".format(
                    spec=validation.get("spec_version"),
                    tree=validation.get("tree_hash") or "—",
                )
            )
            if validation.get("verification_file"):
                console.print(f"  Verification file: {validation.get('verification_file')}")
            if validation.get("checked_at"):
                console.print(f"  Checked at: {validation.get('checked_at')}")
            if validation.get("messages"):
                console.print("  Messages:")
                for message in validation.get("messages", []):
                    console.print(f"    - {message}")
            console.print()

        if invalid_modules:
            skipped = ", ".join(slug for slug, _ in invalid_modules[:SKIPPED_MODULES_DISPLAY_LIMIT])
            if len(invalid_modules) > SKIPPED_MODULES_DISPLAY_LIMIT:
                skipped += ", ..."
            print_warning(
                f"Skipped {len(invalid_modules)} module(s) failing structure validation: {skipped}"
            )
        return

    table = Table(title="📦 Standard Modules")
    table.add_column("Module", style="cyan", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Category", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Description", style="white")

    for rec in filtered:
        description_raw = rec.get("description") or ""
        description_text = (
            truncate_text(description_raw, DESCRIPTION_TRUNCATE_LIMIT) if description_raw else "—"
        )
        table.add_row(
            rec.get("display_name", rec.get("name", "")),
            rec.get("version", ""),
            rec.get("category", ""),
            rec.get("status", ""),
            description_text,
        )

    console.print(table)
    console.print(f"\n📊 Total: {len(filtered)} module(s)")

    if invalid_modules:
        skipped = ", ".join(slug for slug, _ in invalid_modules[:SKIPPED_MODULES_DISPLAY_LIMIT])
        if len(invalid_modules) > SKIPPED_MODULES_DISPLAY_LIMIT:
            skipped += ", ..."
        print_warning(
            f"Skipped {len(invalid_modules)} module(s) failing structure validation: {skipped}"
        )


@modules_app.command("info")
def modules_info(
    name: str = typer.Argument(..., help="Module name to get information about"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine readable JSON output."),
) -> None:
    """
    🔍 Show detailed information about a specific module.

    Examples:
      rapidkit modules info settings
      rapidkit modules info auth --json
    """
    try:
        from modules.free import get_registry
    except ImportError as exc:
        print_error(f"❌ Failed to load module registry: {exc}")
        raise typer.Exit(1) from exc

    try:
        registry = get_registry()
    except (AttributeError, OSError, RuntimeError, ValueError) as exc:
        print_error(f"❌ Failed to read module registry: {exc}")
        raise typer.Exit(1) from exc

    module = registry.get_module(name)

    if not module:
        print_error(f"❌ Module '{name}' not found.")
        available = [str(mod_name) for mod_name in registry.modules]
        if available:
            suggestions = ", ".join(available[:MAX_MODULE_SUGGESTIONS])
            suffix = TRUNCATION_SUFFIX if len(available) > MAX_MODULE_SUGGESTIONS else ""
            print_info(f"Available modules: {suggestions}{suffix}")
        raise typer.Exit(1)

    if json_output:
        console.print_json(json.dumps(module, indent=2))
        return

    console.rule(f"[bold blue]📦 {module.get('name', 'Unknown Module')}[/bold blue]")

    console.print(f"[bold]Name:[/bold] {module.get('name')}")
    console.print(f"[bold]Version:[/bold] {module.get('version')}")
    console.print(f"[bold]Category:[/bold] {module.get('category')}")
    console.print(f"[bold]Priority:[/bold] {module.get('priority')}")
    console.print(f"[bold]Status:[/bold] {module.get('status', 'unknown')}")

    tags = module.get("tags", [])
    if tags:
        console.print(f"[bold]Tags:[/bold] {', '.join(tags)}")

    description = module.get("description", "")
    if description:
        console.print(f"[bold]Description:[/bold] {description}")

    dependencies = module.get("dependencies", [])
    if dependencies:
        console.print(f"[bold]Dependencies:[/bold] {', '.join(dependencies)}")

    capabilities = module.get("capabilities", [])
    if capabilities:
        console.print(f"[bold]Capabilities:[/bold] {', '.join(capabilities)}")

    kit_support = registry.get_kit_support(name)
    if kit_support:
        console.print("[bold]Kit Support:[/bold]")
        for kit, status in kit_support.items():
            status_icon = {
                "supported": "✅",
                "experimental": "⚠️",
                "planned": "🗓️",
                "unsupported": "❌",
            }.get(status.lower(), "❓")
            console.print(f"  {status_icon} {kit}: {status}")

    testing = module.get("testing", {})
    if testing:
        console.print("[bold]Testing:[/bold]")
        console.print(f"  Coverage minimum: {testing.get('coverage_min', 'N/A')}%")
        console.print(f"  Integration tests: {testing.get('integration_tests', False)}")
        console.print(f"  E2E tests: {testing.get('e2e_tests', False)}")

    documentation = module.get("documentation", {})
    if documentation:
        console.print("[bold]Documentation:[/bold]")
        if documentation.get("readme"):
            console.print(f"  README: {documentation['readme']}")
        if documentation.get("api_docs"):
            console.print(f"  API Docs: {documentation['api_docs']}")
        examples = documentation.get("examples", [])
        if examples:
            console.print(f"  Examples: {', '.join(examples)}")


# Module management commands (summary / validate).

# Path resolution logic:
# - In development: src/cli/commands/modules.py -> parents[3] = repo root, then /src/modules
# - In installed package: cli/commands/modules.py -> parents[2] = site-packages, then /modules

# Try development path first (repo/src/modules), then installed path (site-packages/modules)
dev_modules_path = Path(__file__).resolve().parents[3] / "src" / "modules"
installed_modules_path = Path(__file__).resolve().parents[2] / "modules"

if dev_modules_path.exists():
    REPO_ROOT = Path(__file__).resolve().parents[3]
    MODULES_PATH = dev_modules_path
else:
    REPO_ROOT = Path(__file__).resolve().parents[2]
    MODULES_PATH = installed_modules_path


def _collect_module_rows(verbose: bool) -> List[Dict[str, Any]]:
    """Internal: collect module data as list of dicts (single source for table/JSON)."""
    specs = load_all_specs(MODULES_PATH)
    rows: List[Dict[str, Any]] = []
    for spec in sorted(specs.values(), key=lambda s: s.name):
        try:
            cfg = load_module_config(spec.name)
        except (OSError, json.JSONDecodeError):
            cfg = {}
        raw_profiles = cfg.get("profiles")
        profiles_cfg: Dict[str, Any] = raw_profiles if isinstance(raw_profiles, dict) else {}
        raw_features = cfg.get("features")
        features_cfg: Dict[str, Any] = raw_features if isinstance(raw_features, dict) else {}
        raw_depends = cfg.get("depends_on")
        depends_on_cfg: Dict[str, Any] = raw_depends if isinstance(raw_depends, dict) else {}
        dep_names: Set[str] = set()
        for deps in depends_on_cfg.values():
            if isinstance(deps, list):
                for d in deps:
                    if isinstance(d, dict):
                        name = d.get("name")
                        if isinstance(name, str) and name:
                            dep_names.add(name)
        tags: List[str] = []
        tag_val = cfg.get("tags")
        if isinstance(tag_val, list):
            tags = [t for t in tag_val if isinstance(t, str)]
        elif getattr(spec, "tags", None):
            # spec.tags could be any sequence; coerce defensively
            try:
                tags = [t for t in list(spec.tags) if isinstance(t, str)]
            except (
                TypeError,
                ValueError,
                AttributeError,
            ):  # pragma: no cover - defensive
                tags = []
        raw_variables = cfg.get("variables")
        variables_cfg: Dict[str, Any] = raw_variables if isinstance(raw_variables, dict) else {}
        dev_deps_raw = cfg.get("dev_dependencies")
        dev_deps: List[Any] = dev_deps_raw if isinstance(dev_deps_raw, list) else []
        dev_dep_names = {
            str(d.get("name"))
            for d in dev_deps
            if isinstance(d, dict) and isinstance(d.get("name"), str)
        }
        row = {
            "name": spec.effective_name,
            "module": spec.name,
            "version": spec.version,
            "status": spec.status,
            "access": getattr(spec, "access", "free"),
            "maturity": getattr(spec, "maturity", "stable"),
            "profiles": len(profiles_cfg),
            "features": len(features_cfg),
            "deps": len(dep_names),
            "vars": len(variables_cfg),
            "dev_deps": len(dev_dep_names),
            "root": cfg.get("root_path", "-") or "-",
            "tags": tags[:6],
        }
        if not verbose:
            # Trim extended fields for non-verbose scenarios if needed later
            pass
        rows.append(row)
    return rows


@modules_app.command("summary")
def summary(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show extended columns (Vars / DevDeps / Root)"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output JSON instead of table"),
) -> None:
    """Show enterprise summary of all modules (harmonized view).

    Uses merged config to derive counts (profiles, features, deps, variables, dev deps).
    Add --verbose for extra technical columns.
    """
    if not MODULES_PATH.exists():
        print_error("Modules root not found")
        raise typer.Exit(1)
    rows = _collect_module_rows(verbose)
    if json_out:
        console.print_json(
            data={
                "schema_version": "modules-summary-v1",
                "core_version": CURRENT_VERSION,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "modules": rows,
            }
        )
        return
    table = Table(title="RapidKit Modules Summary", show_lines=False)
    table.add_column("Name", style="cyan", overflow="fold")
    table.add_column("Version", style="green")
    table.add_column("Status", style="magenta")
    table.add_column("Access", style="yellow")
    table.add_column("Maturity", style="white")
    table.add_column("Profiles", justify="right")
    table.add_column("Features", justify="right")
    table.add_column("Deps", justify="right")
    if verbose:
        table.add_column("Vars", justify="right")
        table.add_column("DevDeps", justify="right")
        table.add_column("Root", overflow="fold")
    table.add_column("Tags", overflow="fold")
    for r in rows:
        row_list = [
            r["name"],
            r["version"],
            r["status"],
            r["access"],
            r["maturity"],
            str(r["profiles"]),
            str(r["features"]),
            str(r["deps"]),
        ]
        if verbose:
            row_list.extend([str(r["vars"]), str(r["dev_deps"]), r.get("root", "-")])
        row_list.append(",".join(r["tags"]) if r["tags"] else "-")
        table.add_row(*row_list)
    console.print(table)


@modules_app.command("validate-structure")
def modules_validate_structure(
    modules: Optional[List[str]] = typer.Argument(  # noqa: B008
        None,
        help="Specific module slugs to validate (e.g. 'free/essentials/settings').",
        metavar="MODULE",
    ),
    modules_root: Path = typer.Option(  # noqa: B008
        DEFAULT_MODULES_ROOT,
        "--modules-root",
        help="Root directory containing modules (default: src/modules).",
        resolve_path=True,
        show_default=False,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine readable JSON summary of the results.",
    ),
    fail_fast: bool = typer.Option(
        False,
        "--fail-fast",
        help="Stop after the first failing module instead of reporting all results.",
    ),
    ensure: Optional[str] = typer.Option(
        None,
        "--ensure",
        metavar="MODULE",
        help="Ensure a module slug is valid and raise on failure.",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Attempt automatic fixes before running validations via scripts/fix_health_shim_violations.py.",
    ),
) -> None:
    """Validate module directory structures against the canonical STRUCTURE.yaml spec."""

    # Optional autofix run before validating. When requested, attempt to run
    # a repository-local fixer script so callers can apply automated fixes
    # before validations execute. The test suite monkeypatches subprocess.run
    # so we intentionally call subprocess.run here rather than trying to import
    # the script as a Python module.
    if fix:
        # This subprocess call is executing a repository-local maintenance script
        # with a fixed, trusted executable and path (no untrusted input).
        # Silence Bandit here as the usage is intentional and controlled. (B404/B603)
        import subprocess  # nosec
        import sys

        repo_root = Path(__file__).resolve().parents[3]
        script = repo_root / "scripts" / "fix_health_shim_violations.py"
        if script.exists():
            subprocess.run([sys.executable, str(script)], check=True)  # nosec

    try:
        ensure_structure_spec_ready()
    except (FileNotFoundError, ValueError) as exc:
        print_error(f"error: {exc}")
        raise typer.Exit(code=2) from exc

    if ensure:
        result, error = ensure_module_validation(ensure, modules_root)
        if json_output:
            typer.echo(json.dumps(validation_result_to_dict(result), indent=2))
        else:
            _, lines = validation_summary_lines([result], fail_fast=False)
            for line in lines:
                console.print(line)
        if error:
            print_error(str(error))
            raise typer.Exit(code=1) from error
        return

    results = collect_validation_results(modules, modules_root)
    exit_code, lines = validation_summary_lines(results, fail_fast)

    if json_output:
        typer.echo(json.dumps(validation_results_to_dict(results, modules_root), indent=2))
    else:
        for line in lines:
            console.print(line)

    if exit_code != 0:
        raise typer.Exit(code=exit_code)


@modules_app.command("vet")
def modules_vet(
    modules: Optional[List[str]] = typer.Argument(  # noqa: B008
        None,
        help="Specific module slugs to vet (e.g. 'free/essentials/settings').",
        metavar="MODULE",
    ),
    modules_root: Path = typer.Option(  # noqa: B008
        DEFAULT_MODULES_ROOT,
        "--modules-root",
        help="Root directory containing modules (default: src/modules).",
        resolve_path=True,
        show_default=False,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine readable JSON summary of structure and parity checks.",
    ),
    fail_fast: bool = typer.Option(
        False,
        "--fail-fast",
        help="Stop summarising structure results after the first failure.",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Attempt automatic fixes before validations via scripts/fix_health_shim_violations.py.",
    ),
) -> None:
    """Run structure and parity validations together for RapidKit modules."""

    if fix:
        # This subprocess call is executing a repository-local maintenance script
        # with a fixed, trusted executable and path (no untrusted input).
        # Silence Bandit here as the usage is intentional and controlled. (B404/B603)
        import subprocess  # nosec
        import sys

        repo_root = Path(__file__).resolve().parents[3]
        script = repo_root / "scripts" / "fix_health_shim_violations.py"
        if script.exists():
            subprocess.run([sys.executable, str(script)], check=True)  # nosec

    try:
        ensure_structure_spec_ready()
    except (FileNotFoundError, ValueError) as exc:
        print_error(f"error: {exc}")
        raise typer.Exit(code=2) from exc

    structure_results = collect_validation_results(modules, modules_root)
    structure_exit_code, structure_lines = validation_summary_lines(structure_results, fail_fast)

    parity_reports = collect_parity_reports(modules_root, modules)

    structure_by_slug = {result.module: result for result in structure_results}
    for report in parity_reports:
        structure_result = structure_by_slug.get(report.slug)
        verification_file = structure_result.verification_file if structure_result else None
        apply_parity_to_verification(report, verification_file)

    parity_failures = collect_parity_failures(parity_reports)

    if json_output:
        payload = {
            "structure": validation_results_to_dict(structure_results, modules_root),
            "parity": parity_reports_to_dict(parity_reports),
        }
        typer.echo(json.dumps(payload, indent=2))
    else:
        for line in structure_lines:
            console.print(line)
        if parity_reports:
            console.print()
            console.print(render_parity_table(parity_reports))
        if parity_failures:
            console.print()
            print_warning("Modules requiring parity fixes:")
            for report in parity_failures:
                console.print(f"  - {report.slug}")

    if structure_exit_code != 0 or parity_failures:
        raise typer.Exit(code=1)


@modules_app.command("validate")
def validate(
    stop_on_error: bool = typer.Option(
        False, "--stop-on-error", help="Exit non-zero on first invalid module"
    )
) -> None:
    """Validate all module manifests against the enterprise schema."""
    if not MODULES_PATH.exists():
        print_error("Modules root not found")
        raise typer.Exit(1)
    total = 0
    invalid = 0
    for module_dir in sorted(MODULES_PATH.iterdir()):
        if not module_dir.is_dir():
            continue
        mf = module_dir / "module.yaml"
        if not mf.exists():
            continue
        total += 1
        errors = validate_spec(mf)
        # Also check module.yaml generation targets for legacy src/core/health paths
        legacy_targets = []
        # Best-effort detection of legacy generation targets; don't fail validation
        # if the helper raises — we treat any failure as no legacy targets.
        with suppress(Exception):
            legacy_targets = _module_generates_legacy_health_targets(module_dir)
        if errors:
            invalid += 1
            print_error(f"❌ {module_dir.name}: invalid")
            for e in errors:
                print_warning(f"   {e}")
            if legacy_targets:
                for t in legacy_targets:
                    print_warning(f"   Legacy generation target found: {t}")
            if stop_on_error:
                raise typer.Exit(2)
        elif legacy_targets:
            invalid += 1
            print_error(f"❌ {module_dir.name}: legacy generation targets detected")
            for t in legacy_targets:
                print_warning(f"   {t}")
            if stop_on_error:
                raise typer.Exit(2)
        else:
            print_success(f"✅ {module_dir.name}: OK")
    if invalid:
        print_error(f"{invalid}/{total} modules invalid")
        raise typer.Exit(2)
    print_success(f"All {total} modules valid ✔")


def _lock_path(base: Optional[Path]) -> Path:
    base_dir = base or Path.cwd()
    return base_dir / ".rapidkit" / "modules.lock.yaml"


@modules_app.command("lock")
def lock(
    path: Optional[Path] = typer.Option(  # noqa: B008
        None, "--path", help="Target project root (defaults to CWD)"
    ),
    overwrite: bool = typer.Option(  # noqa: B008
        False, "--overwrite", help="Overwrite existing lock file"
    ),
) -> None:
    """Generate (or update) modules lock file capturing current module versions."""
    if not MODULES_PATH.exists():
        print_error("Modules root not found")
        raise typer.Exit(1)
    rows = _collect_module_rows(verbose=True)
    lock_file = _lock_path(path)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    if lock_file.exists() and not overwrite:
        print_warning("Lock file exists. Use --overwrite to replace.")
        raise typer.Exit(1)
    data = {
        "core_version": CURRENT_VERSION,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "modules": {r["module"]: {"version": r["version"], "tags": r["tags"]} for r in rows},
    }
    lock_file.write_text(yaml_dump(data), encoding="utf-8")
    print_success(f"Wrote lock file: {lock_file}")


@modules_app.command("outdated")
def outdated(
    path: Optional[Path] = typer.Option(  # noqa: B008
        None, "--path", help="Target project root containing .rapidkit"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),  # noqa: B008
) -> None:
    """Compare current module versions with lock file and list upgrade/diff status."""
    lock_file = _lock_path(path)
    if not lock_file.exists():
        print_error("Lock file not found. Run 'rapidkit modules lock' first.")
        raise typer.Exit(1)
    try:
        lock_data = (yaml.safe_load(lock_file.read_text(encoding="utf-8")) if yaml else {}) or {}
    except (OSError, AttributeError, TypeError, ValueError) as e:
        print_error(f"Failed to read lock file: {e}")
        raise typer.Exit(1) from None
    locked = lock_data.get("modules", {}) or {}
    rows = _collect_module_rows(verbose=False)
    results = []
    # Index current
    current_map = {r["module"]: r for r in rows}
    # Check current modules
    for name, r in current_map.items():
        locked_entry = locked.get(name)
        if not locked_entry:
            status = "new"
        else:
            try:
                cur_v = semver.parse(r["version"])
                lock_v = semver.parse(str(locked_entry.get("version")))
            except (ValueError, TypeError):  # packaging parse errors
                status = "compare_error"
            else:
                if cur_v > lock_v:
                    status = "upgrade_available"
                elif cur_v < lock_v:
                    status = "locked_newer"  # unusual
                else:
                    status = "ok"
        results.append(
            {
                "module": name,
                "current": r["version"],
                "locked": locked.get(name, {}).get("version"),
                "status": status,
            }
        )
    # Detect removed modules
    for name in locked:
        if name not in current_map:
            results.append(
                {
                    "module": name,
                    "current": None,
                    "locked": locked[name].get("version"),
                    "status": "removed_in_current",
                }
            )
    if json_out:
        console.print_json(
            data={
                "schema_version": "modules-outdated-v1",
                "core_version": CURRENT_VERSION,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "results": results,
            }
        )
        return
    # Render table
    table = Table(title="Module Outdated Report")
    table.add_column("Module", style="cyan")
    table.add_column("Locked")
    table.add_column("Current")
    table.add_column("Status", style="magenta")
    for item in results:
        table.add_row(
            item["module"],
            str(item.get("locked") or "-"),
            str(item.get("current") or "-"),
            item.get("status", ""),
        )
    console.print(table)


# Module-level defaults
DEFAULT_MODULE_ARG = typer.Argument(help="Module name")
DEFAULT_FROM_VERSION = typer.Option(..., "--from", help="Previous version")
DEFAULT_TO_VERSION = typer.Option(..., "--to", help="New version")
DEFAULT_OUTPUT = typer.Option(
    None,
    "--output",
    help="Custom output path (.md). Default docs/advanced/MIGRATION_GUIDE_<module>_vFROM_to_vTO.md",
)
DEFAULT_FORCE = typer.Option(False, "--force", help="Overwrite existing file")
DEFAULT_JSON_OUT = typer.Option(False, "--json", help="Emit JSON output")


@modules_app.command("migration-template")
def migration_template(
    module: str = DEFAULT_MODULE_ARG,
    from_version: str = DEFAULT_FROM_VERSION,
    to_version: str = DEFAULT_TO_VERSION,
    output: Optional[Path] = DEFAULT_OUTPUT,
    force: bool = DEFAULT_FORCE,
    json_out: bool = DEFAULT_JSON_OUT,
) -> None:
    """Generate a migration guide file from the template in docs/.

    When --json is provided, emits a machine readable object with schema_version migration-template-v1.
    """
    repo_root = Path(__file__).resolve().parents[3]
    template_path = repo_root / "docs" / "advanced" / "MIGRATION_GUIDE_TEMPLATE.md"
    if not template_path.exists():
        print_error("Template docs/advanced/MIGRATION_GUIDE_TEMPLATE.md not found")
        raise typer.Exit(1)
    raw = template_path.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).date().isoformat()
    content = (
        raw.replace("<module-name>", module)
        .replace("<previous-version>", from_version)
        .replace("<new-major-version>", to_version)
        .replace("<date>", today)
    )
    out_path = (
        output
        if output
        else repo_root / "docs" / f"MIGRATION_GUIDE_{module}_v{from_version}_to_v{to_version}.md"
    )
    if out_path.exists() and not force:
        print_error("File exists. Use --force to overwrite.")
        raise typer.Exit(1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    if json_out:
        console.print_json(
            data={
                "schema_version": "migration-template-v1",
                "module": module,
                "from": from_version,
                "to": to_version,
                "output_file": str(out_path),
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }
        )
    else:
        print_success(f"Wrote migration guide: {out_path}")


@modules_app.command("search")
def modules_search(
    query: str = typer.Argument(..., help="Search query (searches in name, description, tags)"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine readable JSON output."),
) -> None:
    """
    🔍 Search for modules by name, description, or tags.

    Examples:
      rapidkit modules search auth
      rapidkit modules search database --category database
      rapidkit modules search logging --json
    """
    try:
        from modules.free import get_registry
    except ImportError as exc:
        print_error(f"❌ Failed to load module registry: {exc}")
        raise typer.Exit(1) from exc

    try:
        registry = get_registry()
    except (AttributeError, OSError, RuntimeError, ValueError) as exc:
        print_error(f"❌ Failed to read module registry: {exc}")
        raise typer.Exit(1) from exc

    all_modules = list(registry.modules.values())

    if category:
        category_lower = category.lower()
        all_modules = [
            m for m in all_modules if str(m.get("category", "")).lower() == category_lower
        ]

    query_lower = query.lower()
    matching_modules = []

    for module in all_modules:
        name = str(module.get("name", "")).lower()
        description = str(module.get("description", "")).lower()
        tags = [tag.lower() for tag in module.get("tags", []) if isinstance(tag, str)]

        if (
            query_lower in name
            or query_lower in description
            or any(query_lower in tag for tag in tags)
        ):
            matching_modules.append(module)

    if not matching_modules:
        category_hint = f" in category {category}" if category else ""
        print_warning(f"😕 No modules found matching '{query}'{category_hint}.")
        return

    if json_output:
        json_data = [
            {
                "name": m.get("name"),
                "version": m.get("version"),
                "category": m.get("category"),
                "description": m.get("description"),
                "tags": m.get("tags", []),
            }
            for m in matching_modules
        ]
        console.print_json(json.dumps(json_data, indent=2))
        return

    table = Table(title=f"🔍 Search Results for '{query}'")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Category", style="green")
    table.add_column("Description", style="white")

    for module in matching_modules:
        desc = truncate_text(str(module.get("description", "")), DESCRIPTION_TRUNCATE_LIMIT)
        table.add_row(
            module.get("name", ""),
            module.get("version", ""),
            module.get("category", ""),
            desc,
        )

    console.print(table)
    console.print(f"\n📊 Found: {len(matching_modules)} module(s)")


@modules_app.command("install-interactive")
def modules_install_interactive(
    project: Optional[str] = typer.Option(None, help="Project name inside boilerplates"),
) -> None:
    """
    🎯 Interactive module installation wizard.

    This command provides an interactive way to browse and install modules
    with guided selection and dependency resolution.

    Examples:
      rapidkit modules install-interactive
      rapidkit modules install-interactive --project my-api
    """
    try:
        from modules.free import get_registry
    except ImportError as exc:
        print_error(f"❌ Failed to load module registry: {exc}")
        raise typer.Exit(1) from exc

    try:
        from rich.prompt import Confirm, Prompt
    except ImportError as exc:
        print_error(f"❌ Interactive prompts unavailable: {exc}")
        raise typer.Exit(1) from exc

    try:
        registry = get_registry()
    except (AttributeError, OSError, RuntimeError, ValueError) as exc:
        print_error(f"❌ Failed to read module registry: {exc}")
        raise typer.Exit(1) from exc

    all_modules = list(registry.modules.values())

    categories: Dict[str, List[Dict[str, Any]]] = {}
    for module in all_modules:
        cat = str(module.get("category", "other"))
        categories.setdefault(cat, []).append(module)

    if not categories:
        print_warning("😕 No modules available for installation.")
        raise typer.Exit(0)

    print_info("🎯 Welcome to the RapidKit Module Installation Wizard!")
    print_info("This wizard will help you select and install modules for your project.\n")

    category_names = sorted(categories.keys())
    print_info("📂 Available categories:")
    for index, cat in enumerate(category_names, 1):
        module_count = len(categories[cat])
        print_info(f"  [{index}] {cat.title()} ({module_count} modules)")

    while True:
        try:
            selection = Prompt.ask(
                "\nSelect a category (number or name)",
                choices=[str(i) for i in range(1, len(category_names) + 1)] + category_names,
            )

            if selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(category_names):
                    selected_category = category_names[idx]
                    break
            elif selection in category_names:
                selected_category = selection
                break

            print_warning("Invalid choice. Please try again.")

        except KeyboardInterrupt:
            print_info("\n❌ Installation cancelled.")
            raise typer.Exit(0) from None

    selected_modules = categories[selected_category]
    print_info(f"\n📦 Modules in '{selected_category}' category:")
    module_name_pairs: List[tuple[str, Dict[str, Any]]] = []
    for index, module in enumerate(selected_modules, 1):
        name = module.get("name")
        if not isinstance(name, str):
            continue
        module_name_pairs.append((name, module))
        desc = truncate_text(str(module.get("description", "")), SHORT_DESCRIPTION_LIMIT)
        print_info(f"  [{index}] {name} - {desc}")

    if not module_name_pairs:
        print_warning("😕 No modules with valid names found in this category.")
        raise typer.Exit(0)

    module_lookup = {name.lower(): name for name, _ in module_name_pairs}
    selected_module_names: List[str] = []

    while True:
        try:
            raw_choice = Prompt.ask(
                "\nSelect modules to install (comma-separated numbers/names, or 'all', or 'done')",
                default="done",
            ).strip()
            choice_lower = raw_choice.lower()

            if choice_lower == "done":
                break
            if choice_lower == "all":
                selected_module_names = [name for name, _ in module_name_pairs]
                print_info(f"✅ Selected all {len(selected_module_names)} modules")
                break

            selections = [s.strip() for s in raw_choice.split(",") if s.strip()]
            for sel in selections:
                if sel.isdigit():
                    idx = int(sel) - 1
                    if 0 <= idx < len(module_name_pairs):
                        candidate = module_name_pairs[idx][0]
                        if candidate not in selected_module_names:
                            selected_module_names.append(candidate)
                            print_info(f"✅ Added: {candidate}")
                    else:
                        print_warning(f"Invalid number: {sel}")
                    continue

                resolved_name = module_lookup.get(sel.lower())
                if resolved_name:
                    if resolved_name not in selected_module_names:
                        selected_module_names.append(resolved_name)
                        print_info(f"✅ Added: {resolved_name}")
                else:
                    print_warning(f"Module not found: {sel}")

        except KeyboardInterrupt:
            print_info("\n❌ Installation cancelled.")
            raise typer.Exit(0) from None

    if not selected_module_names:
        print_info("ℹ️ No modules selected.")
        raise typer.Exit(0)

    print_info(f"\n🔗 Checking dependencies for {len(selected_module_names)} modules...")
    missing_deps = registry.validate_module_dependencies(selected_module_names)

    if missing_deps:
        print_warning("⚠️ Missing dependencies detected:")
        for dep in missing_deps:
            print_warning(f"  • {dep}")

        if not Confirm.ask("Continue anyway?", default=False):
            print_info("❌ Installation cancelled.")
            raise typer.Exit(0)

    install_order = registry.get_install_order(selected_module_names)
    print_info("📋 Installation order:")
    for index, module_name in enumerate(install_order, 1):
        print_info(f"  {index}. {module_name}")

    if not Confirm.ask(f"\n🚀 Install {len(install_order)} modules?", default=True):
        print_info("❌ Installation cancelled.")
        raise typer.Exit(0)

    print_info("\n🔧 Installing modules...")
    from ..commands.add.module import add_module

    for module_name in install_order:
        print_info(f"📦 Installing {module_name}...")
        try:
            if project:
                add_module(module_name, project=project)
            else:
                add_module(module_name)
            print_success(f"✅ {module_name} installed successfully")
        except (OSError, RuntimeError, ValueError, typer.Exit) as exc:
            print_error(f"❌ Failed to install {module_name}: {exc}")
            if not Confirm.ask("Continue with remaining modules?", default=False):
                print_info("❌ Installation stopped.")
                raise typer.Exit(1) from exc

    print_success(f"\n🎉 Successfully installed {len(selected_module_names)} modules!")
    print_info("You can now run your project with 'rapidkit dev'")


@modules_app.command("configure")
def modules_configure(
    project: Optional[str] = typer.Option(None, help="Project name inside boilerplates"),
) -> None:
    """
    ⚙️ Interactive configuration wizard for project settings.

    This wizard helps you configure common project settings like
    database connections, authentication, logging, and more.

    Examples:
      rapidkit modules configure
      rapidkit modules configure --project my-api
    """
    try:
        from rich.prompt import Confirm, Prompt
    except ImportError as exc:
        print_error(f"❌ Interactive prompts unavailable: {exc}")
        raise typer.Exit(1) from exc

    print_info("⚙️ Welcome to the RapidKit Configuration Wizard!")
    print_info("This wizard will help you configure common project settings.\n")

    # Find project root
    from ..utils.filesystem import find_project_root

    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(1)

    print_info(f"📁 Configuring project: {project_root.name}")

    # Step 1: Database configuration
    print_info("\n🗄️ Database Configuration")
    if Confirm.ask("Configure database settings?", default=True):
        db_type = Prompt.ask(
            "Database type", choices=["postgresql", "sqlite", "mysql"], default="sqlite"
        )

        if db_type == "postgresql":
            db_host = Prompt.ask("Database host", default="localhost")
            db_port = Prompt.ask("Database port", default="5432")
            db_name = Prompt.ask("Database name", default=f"{project_root.name}_db")
            db_user = Prompt.ask("Database user", default="postgres")
            db_password = Prompt.ask("Database password (leave empty for no password)")

            config_lines = [
                (
                    f"DATABASE_URL=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                    if db_password
                    else f"DATABASE_URL=postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
                )
            ]
        elif db_type == "mysql":
            db_host = Prompt.ask("Database host", default="localhost")
            db_port = Prompt.ask("Database port", default="3306")
            db_name = Prompt.ask("Database name", default=f"{project_root.name}_db")
            db_user = Prompt.ask("Database user", default="root")
            db_password = Prompt.ask("Database password")

            config_lines = [
                f"DATABASE_URL=mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            ]
        else:  # sqlite
            db_file = Prompt.ask("Database file path", default=f"{project_root.name}.db")
            config_lines = [f"DATABASE_URL=sqlite:///{db_file}"]

        env_file = project_root / ".env"
        if env_file.exists() and not Confirm.ask(
            ".env file already exists. Overwrite?", default=False
        ):
            config_lines = []

        if config_lines:
            try:
                with open(env_file, "a" if env_file.exists() else "w") as f:
                    if not env_file.exists():
                        f.write("# RapidKit Configuration\n")
                    f.write("\n# Database Configuration\n")
                    for line in config_lines:
                        f.write(f"{line}\n")
            except OSError as exc:
                print_error(f"❌ Failed to update .env: {exc}")
                raise typer.Exit(1) from exc
            print_success("✅ Database configuration saved to .env")

    # Step 2: Authentication configuration
    print_info("\n🔐 Authentication Configuration")
    if Confirm.ask("Configure authentication settings?", default=True):
        auth_provider = Prompt.ask(
            "Authentication provider", choices=["local", "oauth", "ldap"], default="local"
        )

        if auth_provider == "oauth":
            oauth_provider = Prompt.ask(
                "OAuth provider", choices=["google", "github", "facebook"], default="google"
            )
            client_id = Prompt.ask(f"{oauth_provider.title()} Client ID")
            client_secret = Prompt.ask(f"{oauth_provider.title()} Client Secret")

            config_lines = [
                f"OAUTH_PROVIDER={oauth_provider}",
                f"OAUTH_CLIENT_ID={client_id}",
                f"OAUTH_CLIENT_SECRET={client_secret}",
            ]
        else:
            config_lines = [f"AUTH_PROVIDER={auth_provider}"]

        env_file = project_root / ".env"
        try:
            with open(env_file, "a") as f:
                f.write("\n# Authentication Configuration\n")
                for line in config_lines:
                    f.write(f"{line}\n")
        except OSError as exc:
            print_error(f"❌ Failed to update .env: {exc}")
            raise typer.Exit(1) from exc
        print_success("✅ Authentication configuration saved to .env")

    # Step 3: Logging configuration
    print_info("\n📝 Logging Configuration")
    if Confirm.ask("Configure logging settings?", default=True):
        log_level = Prompt.ask(
            "Log level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
        )
        log_file = Prompt.ask("Log file path (leave empty for console only)", default="")

        config_lines = [f"LOG_LEVEL={log_level}"]
        if log_file:
            config_lines.append(f"LOG_FILE={log_file}")

        env_file = project_root / ".env"
        try:
            with open(env_file, "a") as f:
                f.write("\n# Logging Configuration\n")
                for line in config_lines:
                    f.write(f"{line}\n")
        except OSError as exc:
            print_error(f"❌ Failed to update .env: {exc}")
            raise typer.Exit(1) from exc
        print_success("✅ Logging configuration saved to .env")

    # Step 4: Environment configuration
    print_info("\n🌍 Environment Configuration")
    environment = Prompt.ask(
        "Environment", choices=["development", "staging", "production"], default="development"
    )

    debug_mode = Confirm.ask("Enable debug mode?", default=environment == "development")
    secret_key = Prompt.ask("Application secret key", default="your-secret-key-change-this")

    config_lines = [
        f"ENVIRONMENT={environment}",
        f"DEBUG={str(debug_mode).lower()}",
        f"SECRET_KEY={secret_key}",
    ]

    env_file = project_root / ".env"
    try:
        with open(env_file, "a") as f:
            f.write("\n# Environment Configuration\n")
            for line in config_lines:
                f.write(f"{line}\n")
    except OSError as exc:
        print_error(f"❌ Failed to update .env: {exc}")
        raise typer.Exit(1) from exc
    print_success("✅ Environment configuration saved to .env")

    print_success("\n🎉 Configuration completed!")
    print_info("Your settings have been saved to .env file.")
    print_info("You can now run your project with 'rapidkit dev'")
