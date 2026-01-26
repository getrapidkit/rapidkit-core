import difflib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import typer

from core.rendering.template_renderer import render_template
from core.services.config_loader import load_module_config
from core.services.file_hash_registry import _sha256, load_hashes, load_snapshot
from core.services.module_manifest import load_manifest_or_none
from core.services.profile_utils import resolve_profile_chain

from ..ui.printer import print_error, print_info, print_success, print_warning
from ..utils.classifier import classify_file_status
from ..utils.filesystem import find_project_root
from ..utils.variables_prompt import prompt_for_variables

diff_app = typer.Typer(
    help="Diff generated module files against current templates & registry state"
)


def _resolve_repo_root() -> Path:
    here = Path(__file__).resolve()
    # Prefer nearest ancestor containing src/modules
    for p in [here] + list(here.parents):
        candidate = p / "src" / "modules"
        if candidate.exists():
            return p
    # Fallback to original heuristic (4 levels up)
    return here.parents[4]


REPO_ROOT = _resolve_repo_root()
MODULES_PATH = REPO_ROOT / "src" / "modules"


def _collect_module_files(
    _module_name: str, profile: str, config: Dict[str, Any]
) -> List[Tuple[str, Dict[str, Any]]]:  # module name unused
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
    # Defensive: features must be dict of name -> meta(dict)
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
    return all_files


@diff_app.command("module")
def diff_module(
    name: str,
    profile: str = typer.Option("fastapi/minimal", help="Profile used when generating files"),
    project: str = typer.Option(None, help="Project name inside boilerplates"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
    show_patch: bool = typer.Option(
        False, "--patch", help="Show unified diff for changed / diverged files"
    ),
    merge_json: bool = typer.Option(
        False,
        "--merge-json",
        help="Emit JSON with three-way contents (base/current/template) for merge tooling",
    ),
) -> None:
    """Show file-level status for a module.

    Status legend:
      clean              -> current == registry hash == regenerated
      template_updated   -> current == registry hash != regenerated
      locally_modified   -> current != registry hash == regenerated
      manually_updated   -> current == regenerated != registry hash
      diverged           -> all three differ (conflict)
      untracked_existing -> file exists but no registry record
      new_template       -> template now produces file not present & untracked
      missing            -> tracked hash but file removed locally
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
        print_warning("⚠️ No module.yaml manifest found (legacy)")

    try:
        config = load_module_config(name, profile)
    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(code=1) from None

    variables = prompt_for_variables(config.get("variables", {}))
    all_files = _collect_module_files(name, profile, config)
    template_cache: Dict[Path, Optional[str]] = {}

    hash_registry = load_hashes(project_root)
    root_path = config.get("root_path", "")

    report = []
    counts: Dict[str, int] = {}

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
            # Primary expected location
            template_path = (
                MODULES_PATH
                / name
                / "templates"
                / ("base" if context == "base" else f"overrides/{context}")
                / f"{rel}.j2"
            )
            # Fallback: if the exact override folder doesn't exist for this profile,
            # search the overrides tree for any matching rel path (useful when
            # templates are provided under a different profile like "enterprise").
            if not template_path.exists():
                overrides_dir = MODULES_PATH / name / "templates" / "overrides"
                if overrides_dir.exists():
                    # look for any .j2 file that ends with the expected relative path
                    target_suffix = f"{rel}.j2"
                    for cand in overrides_dir.glob("**/*.j2"):
                        try:
                            path_str = (
                                cand.as_posix()
                            )  # could raise only AttributeError if cand is None or invalid
                        except AttributeError:
                            continue
                        if path_str.endswith(target_suffix):
                            template_path = cand
                            break

        dst = project_root / root_path / rel
        regen_hash = None
        regen_content = None
        if template_path.exists():
            cached = template_cache.get(template_path)
            if cached is None and template_path not in template_cache:
                try:
                    cached = render_template(template_path, variables)
                except (OSError, ValueError) as e:
                    print_warning(f"⚠️ Render failed {template_path}: {e}")
                    cached = None
                template_cache[template_path] = cached
            regen_content = cached
            if regen_content is not None:
                try:
                    regen_hash = _sha256(regen_content.encode("utf-8"))
                except (OSError, ValueError):
                    regen_hash = None
        rel_record = str(dst.relative_to(project_root))
        entry = hash_registry.get("files", {}).get(rel_record)
        registry_hash = entry.get("hash") if entry else None
        previous_hash = entry.get("previous_hash") if entry else None
        if dst.exists():
            try:
                cur_bytes = dst.read_bytes()
            except OSError:
                cur_bytes = b""
            current_hash = _sha256(cur_bytes)
        else:
            current_hash = None

        status = classify_file_status(dst.exists(), registry_hash, current_hash, regen_hash)

        counts[status] = counts.get(status, 0) + 1
        item = {
            "file": rel_record,
            "status": status,
            "registry_hash": registry_hash,
            "current_hash": current_hash,
            "regenerated_hash": regen_hash,
        }
        if previous_hash:
            item["previous_hash"] = previous_hash
            item["rollback_available"] = True
        if (
            show_patch
            and regen_content
            and dst.exists()
            and status in {"template_updated", "locally_modified", "diverged", "manually_updated"}
        ):
            try:
                cur_lines = dst.read_text(encoding="utf-8", errors="ignore").splitlines()
                regen_lines = regen_content.splitlines()
                diff_lines = list(
                    difflib.unified_diff(
                        cur_lines,
                        regen_lines,
                        fromfile=rel_record + " (current)",
                        tofile=rel_record + " (template)",
                        lineterm="",
                        n=3,
                    )
                )
                item["diff"] = "\n".join(diff_lines)
            except OSError:
                pass
        report.append(item)

    if json_output or merge_json:
        merge_files = []
        if merge_json:
            project_root = find_project_root(project)
            for item in report:
                if item["status"] in {
                    "template_updated",
                    "locally_modified",
                    "diverged",
                    "manually_updated",
                }:
                    rel_path = item["file"]
                    dst_path = (
                        (project_root / rel_path)
                        if (project_root and isinstance(rel_path, str))
                        else None
                    )
                    base_hash = item.get("registry_hash")
                    base_content = None
                    if base_hash and project_root:
                        try:
                            snap_bytes = load_snapshot(project_root, base_hash)
                            if snap_bytes is not None:
                                try:
                                    base_content = snap_bytes.decode("utf-8")
                                except UnicodeDecodeError:
                                    base_content = None
                        except OSError:
                            base_content = None
                    current_content = None
                    if dst_path and dst_path.exists():
                        try:
                            current_content = dst_path.read_text(encoding="utf-8", errors="ignore")
                        except OSError:
                            current_content = None
                    # Re-render template content
                    template_content = None
                    try:
                        base_candidate = (
                            MODULES_PATH / name / "templates" / "base" / f"{rel_path}.j2"
                        )
                        if base_candidate.exists():
                            template_content = render_template(base_candidate, variables)
                        else:
                            overrides_dir = MODULES_PATH / name / "templates" / "overrides"
                            if overrides_dir.exists():
                                for prof_dir in overrides_dir.glob("**/*"):
                                    if prof_dir.is_dir():
                                        cand = prof_dir / f"{rel_path}.j2"
                                        if cand.exists():
                                            template_content = render_template(cand, variables)
                                            break
                    except (OSError, ValueError):
                        template_content = None
                    merge_files.append(
                        {
                            "file": rel_path,
                            "status": item["status"],
                            "merge": {
                                "base": base_content,
                                "current": current_content,
                                "template": template_content,
                            },
                        }
                    )
        payload = {
            "schema_version": "diff-merge-v1" if merge_json else "diff-v2",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "module": name,
            "profile": profile,
            "summary": counts,
            "files": report,
        }
        if merge_json:
            payload["merge_files"] = merge_files
        print(json.dumps(payload, indent=2))
        return

    print_info("\n[bold magenta]=== Diff Summary ===[/bold magenta]")
    for k, v in sorted(counts.items()):
        print_info(f"  • {k}: {v}")

    priority = {"diverged", "template_updated", "locally_modified", "manually_updated"}
    print_info("\n[bold cyan]Details:[/bold cyan]")
    for item in report:
        if item["status"] in priority:
            file_val = item.get("file") or "<unknown>"
            line = f"[yellow]{item['status']:<18}[/yellow] {file_val}"
            if item.get("previous_hash"):
                line += " [dim](has previous_hash)[/dim]"
            print_info(line)
            if show_patch:
                diff_text = item.get("diff")
                if isinstance(diff_text, str) and diff_text:
                    print_info("[dim]--- diff ---[/dim]\n" + diff_text)
    for item in report:
        if item["status"] not in priority:
            color = "green" if item["status"] == "clean" else "cyan"
            if item["status"] in {"untracked_existing", "missing", "new_template"}:
                color = "magenta"
            print_info(f"[{color}]{item['status']:<18}[/{color}] {item['file']}")

    print_success("Done.")


@diff_app.command("all")
def diff_all(
    profile: str = typer.Option("fastapi/minimal", help="Profile context"),
    project: str = typer.Option(None, help="Project name inside boilerplates"),
) -> None:
    """Run diff across all modules (aggregated JSON by default)."""
    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)
    results: List[Dict[str, Any]] = []
    if not MODULES_PATH.exists():
        # Always emit JSON (even if user didn't specify) to keep interface consistent
        payload = {
            "schema_version": "diff-all-v1",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "profile": profile,
            "modules": results,
            "note": "modules directory missing",
        }
        print(json.dumps(payload, indent=2))
        return
    # Load hash registry once outside the module loop
    hash_registry = load_hashes(project_root)

    for mod_dir in sorted(MODULES_PATH.iterdir()):
        if not (mod_dir / "module.yaml").exists():
            continue
        mod_name = mod_dir.name
        try:
            config = load_module_config(mod_name, profile)
        except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
            print_warning(f"Skipping {mod_name}: {e}")
            continue

        variables = {
            k: (v.get("default") if isinstance(v, dict) else None)
            for k, v in (config.get("variables", {}) or {}).items()
        }
        all_files = _collect_module_files(mod_name, profile, config)
        root_path = config.get("root_path", "")
        report: List[Dict[str, Any]] = []
        counts: Dict[str, int] = {}
        template_cache: Dict[Path, Optional[str]] = {}

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
                template_path = MODULES_PATH / mod_name / template_file
            else:
                template_path = (
                    MODULES_PATH
                    / mod_name
                    / "templates"
                    / ("base" if context == "base" else f"overrides/{context}")
                    / f"{rel}.j2"
                )
            dst = project_root / root_path / rel
            regen_hash = None
            if template_path.exists():
                cached = template_cache.get(template_path)
                if cached is None and template_path not in template_cache:
                    try:
                        cached = render_template(template_path, variables)
                    except (OSError, ValueError):
                        cached = None
                    template_cache[template_path] = cached
                regen_content = cached
                if regen_content is not None:
                    try:
                        regen_hash = _sha256(regen_content.encode("utf-8"))
                    except (OSError, ValueError):
                        regen_hash = None
            rel_record = str(dst.relative_to(project_root))
            entry = hash_registry.get("files", {}).get(rel_record)
            registry_hash = entry.get("hash") if entry else None
            if dst.exists():
                try:
                    cur_bytes = dst.read_bytes()
                except OSError:
                    cur_bytes = b""
                current_hash = _sha256(cur_bytes)
            else:
                current_hash = None
            status = classify_file_status(dst.exists(), registry_hash, current_hash, regen_hash)
            counts[status] = counts.get(status, 0) + 1
            report.append({"file": rel_record, "status": status})

        results.append({"module": mod_name, "summary": counts, "files": report})
    print(
        json.dumps(
            {
                "schema_version": "diff-all-v1",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "profile": profile,
                "modules": results,
            },
            indent=2,
        )
    )
