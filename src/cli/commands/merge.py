import difflib
import json
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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

from ..ui.printer import print_error, print_info, print_success, print_warning
from ..utils.classifier import classify_file_status
from ..utils.filesystem import find_project_root
from ..utils.variables_prompt import prompt_for_variables
from .diff import MODULES_PATH, _collect_module_files

merge_app = typer.Typer(help="Merge helper: reconcile local vs template changes")


@merge_app.command("module")
def merge_module(
    name: str = typer.Argument(help="Module name"),
    profile: str = typer.Option("fastapi/minimal", help="Profile chain for template resolution"),
    project: Optional[str] = typer.Option(None, help="Project name inside boilerplates"),
    strategy: str = typer.Option(
        "prompt",
        help="Conflict strategy: prompt | prefer-current | prefer-template",
    ),
    auto_apply_template_updated: bool = typer.Option(
        False,
        help="When strategy=prompt: automatically apply template for template_updated files without prompting",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry-run (no writes)"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON result"),
) -> None:
    """
    Interactive / automated merge of modified module files.

    Targets statuses: template_updated, locally_modified, manually_updated, diverged.

    Strategy rules:
    - prefer-current: keep current file (no overwrite)
    - prefer-template: overwrite with freshly rendered template (if available)
    - prompt: interactive per-file menu (show diff / apply / keep / skip)
        with --auto-apply-template-updated it auto-applies those statuses.
    """
    project_root = find_project_root(project)
    if not project_root:
        print_error("❌ Not a valid RapidKit project.")
        raise typer.Exit(code=1)

    manifest = load_manifest_or_none(MODULES_PATH, name)
    module_version = getattr(manifest, "version", "unknown") if manifest else "unknown"

    try:
        config = load_module_config(name, profile)
    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(code=1) from None

    variables = prompt_for_variables(config.get("variables", {}))
    root_path = config.get("root_path", "") or ""
    registry: Dict[str, Any] = load_hashes(project_root)
    target_statuses = {
        "template_updated",
        "locally_modified",
        "manually_updated",
        "diverged",
    }

    all_files = _collect_module_files(name, profile, config)

    actions: List[Dict[str, Any]] = []
    updates_performed = 0

    def decide_action(
        rel_file: str,
        status: str,
        has_template: bool,
        has_current: bool,
        template_preview: Optional[str],
        current_preview: Optional[str],
        interactive_allowed: bool,
    ) -> str:
        nonlocal actions
        if strategy == "prefer-current":
            return "keep-current"
        if strategy == "prefer-template":
            return "apply-template" if has_template else "skip"
        # prompt strategy
        if auto_apply_template_updated and status == "template_updated" and has_template:
            return "apply-template"

        if not interactive_allowed:
            return "apply-template" if has_template else "keep-current"

        choices = {
            "k": "keep-current",
            "c": "keep-current",
            "a": "apply-template",
            "t": "apply-template",
            "s": "skip",
        }
        default_choice = "a" if has_template else "k"
        while True:
            prompt_text = (
                f"File: {rel_file} [{status}] -> (k)eep current"
                + ("/(a)pply template" if has_template else "")
                + "/(s)kip"
                + (
                    "/(d)iff"
                    if has_template and has_current and template_preview is not None
                    else ""
                )
            )
            answer = typer.prompt(prompt_text, default=default_choice).strip().lower()
            if answer in {"d", "diff"} and has_template and has_current:
                current_lines = (current_preview or "").splitlines()
                template_lines = (template_preview or "").splitlines()
                diff_lines = difflib.unified_diff(
                    current_lines,
                    template_lines,
                    fromfile=f"{rel_file} (current)",
                    tofile=f"{rel_file} (template)",
                    lineterm="",
                    n=3,
                )
                print_info("\n".join(diff_lines) or "(no diff)")
                continue
            decision = choices.get(answer)
            if decision:
                return decision
            print_warning("Please choose one of: k, a, s" + (", d" if has_template else ""))

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
            if not template_path.exists():
                overrides_dir = MODULES_PATH / name / "templates" / "overrides"
                if overrides_dir.exists():
                    target_suffix = f"{rel}.j2"
                    for cand in overrides_dir.glob("**/*.j2"):
                        try:
                            if cand.as_posix().endswith(target_suffix):
                                template_path = cand
                                break
                        except AttributeError:
                            continue

        destination = Path(project_root / root_path / rel).resolve()
        try:
            rel_record = destination.relative_to(project_root).as_posix()
        except ValueError:
            # Destination outside project root; skip for safety
            print_warning(f"Skipping {rel}: resolves outside project root")
            continue

        entry = registry.get("files", {}).get(rel_record, {})
        registry_hash = entry.get("hash") if isinstance(entry, dict) else None

        current_bytes: Optional[bytes]
        current_hash: Optional[str]
        if destination.exists():
            try:
                current_bytes = destination.read_bytes()
            except OSError as err:
                print_warning(f"Cannot read {rel_record}: {err}")
                current_bytes = None
            current_hash = _sha256(current_bytes) if current_bytes is not None else None
        else:
            current_bytes = None
            current_hash = None

        template_content: Optional[str] = None
        template_hash: Optional[str] = None
        if template_path.exists():
            try:
                template_content = render_template(template_path, variables)
                template_hash = _sha256(template_content.encode("utf-8"))
            except (OSError, ValueError) as err:
                print_warning(f"Failed to render template for {rel_record}: {err}")

        status = classify_file_status(
            destination.exists(),
            registry_hash,
            current_hash,
            template_hash,
        )

        if status not in target_statuses:
            continue

        has_template = template_content is not None
        has_current = current_bytes is not None
        decision = decide_action(
            rel_record,
            status,
            has_template,
            has_current,
            template_content,
            current_bytes.decode("utf-8", errors="ignore") if current_bytes else None,
            strategy == "prompt" and not json_output,
        )
        actions.append(
            {
                "file": rel_record,
                "status": status,
                "decision": decision,
            }
        )

        if dry_run or decision == "skip":
            actions[-1]["applied"] = False
            continue

        if decision == "apply-template":
            if not has_template:
                actions[-1]["applied"] = False
                actions[-1]["reason"] = "template-missing"
                continue
            previous_content = current_bytes
            if previous_content is not None:
                with suppress(OSError):
                    store_snapshot(project_root, previous_content)
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                destination.write_text(template_content or "", encoding="utf-8")
            except OSError as err:
                print_error(f"Failed writing {rel_record}: {err}")
                actions[-1]["applied"] = False
                actions[-1]["reason"] = "write-error"
                continue
            record_file_hash(
                registry,
                rel_record,
                name,
                module_version,
                (template_content or "").encode("utf-8"),
                previous_hash=registry_hash,
                snapshot=True,
                project_root=project_root,
            )
            updates_performed += 1
            actions[-1]["applied"] = True
            actions[-1]["result_hash"] = template_hash
            continue

        if decision == "keep-current":
            if current_bytes is None:
                actions[-1]["applied"] = False
                actions[-1]["reason"] = "current-missing"
                continue
            record_file_hash(
                registry,
                rel_record,
                name,
                module_version,
                current_bytes,
                previous_hash=registry_hash,
                snapshot=True,
                project_root=project_root,
            )
            updates_performed += 1
            actions[-1]["applied"] = True
            actions[-1]["result_hash"] = current_hash
            continue

        actions[-1]["applied"] = False

    if not dry_run and updates_performed:
        save_hashes(project_root, registry)

    summary = {
        "schema_version": "merge-module-v1",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "module": name,
        "profile": profile,
        "dry_run": bool(dry_run),
        "actions": actions,
    }

    if json_output:
        print(json.dumps(summary, indent=2))
        return

    applied = len([a for a in actions if a.get("applied")])
    skipped = len(actions) - applied
    print_info(f"Merge candidates processed: {len(actions)}")
    print_info(f"Applied updates: {applied} | Skipped: {skipped}")
    if updates_performed:
        print_success("Registry updated.")
    else:
        print_warning("No changes applied; registry unchanged.")
