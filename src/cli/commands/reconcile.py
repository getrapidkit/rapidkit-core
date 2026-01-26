from __future__ import annotations

import contextlib
import difflib
import tempfile
from pathlib import Path
from typing import Any, Optional, cast

import typer

from cli.ui.printer import print_error, print_info, print_success, print_warning
from cli.utils.filesystem import find_project_root
from cli.utils.pathing import resolve_modules_path
from core.services.module_path_resolver import resolve_module_directory
from core.services.snippet_injector import (
    infer_owner_module_slug,
    inject_snippet_enterprise,
    load_installed_module_slugs,
    load_snippet_registry,
    reconcile_pending_snippets,
    resolve_conflicted_snippet,
)


def reconcile(
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Target project root (defaults to auto-detect).",
    ),
    lenient: bool = typer.Option(
        False,
        "--lenient",
        help="Lenient validation for env snippets during reconcile.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Print detailed lists of applied/skipped/failed snippet keys.",
    ),
    plan: bool = typer.Option(
        False,
        "--plan",
        help="Show diffs for pending injections without writing anything.",
    ),
    resolve_key: Optional[str] = typer.Option(
        None,
        "--resolve-key",
        help="Resolve a conflicted snippet by key (updates snippet_registry.json only).",
    ),
    resolve_to: str = typer.Option(
        "pending",
        "--resolve-to",
        help="Target status when resolving conflicts: pending|failed",
    ),
) -> None:
    """Reconcile pending snippet injections for the current project."""

    root = find_project_root(project)
    if root is None:
        print_error("❌ Could not detect project root. Pass --project PATH.")
        raise typer.Exit(code=1)

    print_info(f"🔁 Reconciling pending snippet injections in: {root}")

    if resolve_key:
        result = resolve_conflicted_snippet(root, key=resolve_key, to_status=resolve_to)
        status = result.get("status")
        if status == "updated":
            print_success(
                f"✅ Updated {resolve_key}: {result.get('from_status')} -> {result.get('to_status')}"
            )
            return
        if status == "missing_entry":
            print_error("❌ Snippet key not found in snippet_registry.json")
            raise typer.Exit(code=1)
        print_error(f"❌ Resolve failed: {result.get('error') or status}")
        raise typer.Exit(code=1)

    if plan:
        registry = load_snippet_registry(root)
        snippets = registry.get("snippets", {}) if isinstance(registry, dict) else {}
        if not isinstance(snippets, dict):
            print_error("❌ snippet_registry.json is invalid.")
            raise typer.Exit(code=1)

        pending = [
            (k, v)
            for k, v in snippets.items()
            if isinstance(v, dict) and v.get("status") == "pending"
        ]
        if not pending:
            print_success("✅ No pending snippets found.")
            return

        installed = load_installed_module_slugs(root)
        shown = 0
        for key, entry in pending:
            rel_file = entry.get("file")
            anchor = entry.get("anchor")
            module_slug = entry.get("module_slug")
            template = entry.get("template")
            if not all(
                isinstance(v, str) and v.strip() for v in (rel_file, anchor, module_slug, template)
            ):
                print_warning(f"❌ {key}: missing metadata (file/anchor/module_slug/template)")
                continue

            rel_file = cast(str, rel_file)
            anchor = cast(str, anchor)
            module_slug = cast(str, module_slug)
            template = cast(str, template)

            dest = root / rel_file
            owner = infer_owner_module_slug(root, dest)

            if installed and module_slug not in installed:
                print_warning(f"⏭️ {key}: producer '{module_slug}' not installed")
                continue
            if installed and owner and owner not in installed:
                print_warning(f"⏭️ {key}: owner '{owner}' not installed")
                continue

            module_dir = resolve_module_directory(resolve_modules_path(), module_slug)
            template_path = module_dir / "templates" / "snippets" / template
            if not template_path.exists():
                print_warning(f"❌ {key}: template not found: {template_path}")
                continue

            before = ""
            if dest.exists():
                try:
                    before = dest.read_text(encoding="utf-8")
                except OSError:
                    before = ""

            # Run injection against a temp project root to avoid writing registries/audit.
            with tempfile.TemporaryDirectory() as tmp:
                tmp_root = Path(tmp)
                tmp_dest = tmp_root / rel_file
                tmp_dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    with contextlib.suppress(OSError):
                        tmp_dest.write_text(before, encoding="utf-8")

                snippet_id = key.split("::", 1)[0] if "::" in key else key
                snippet_meta: dict[str, Any] = {
                    "id": snippet_id,
                    "version": entry.get("version", "0.0.0"),
                    "priority": entry.get("priority", 0),
                    "context": entry.get("context") or {},
                    "schema": entry.get("schema") or {},
                    "conflict_resolution": entry.get("conflict_resolution", "override"),
                    "patch_mode": entry.get("patch_mode"),
                    "template": template,
                    "module_slug": module_slug,
                    "profile": entry.get("profile"),
                    "target": entry.get("target"),
                }
                res = inject_snippet_enterprise(
                    destination_path=tmp_dest,
                    template_path=template_path,
                    anchor=anchor,
                    variables={},
                    snippet_metadata=snippet_meta,
                    project_root=tmp_root,
                    lenient=lenient,
                )

                if not isinstance(res, dict) or not res.get("injected"):
                    errs = res.get("errors") if isinstance(res, dict) else None
                    print_warning(f"❌ {key}: would not inject ({errs})")
                    continue

                after = tmp_dest.read_text(encoding="utf-8") if tmp_dest.exists() else ""

            diff = list(
                difflib.unified_diff(
                    before.splitlines(True),
                    after.splitlines(True),
                    fromfile=str(rel_file),
                    tofile=str(rel_file),
                )
            )
            print_info(f"\n[bold]DIFF {key}[/bold]")
            if diff:
                for line in diff:
                    print_info(line.rstrip("\n"))
            else:
                print_info("(no changes)")
            shown += 1

        print_success(f"✅ Plan complete. Diffs shown: {shown}.")
        return

    stats = reconcile_pending_snippets(root, lenient=lenient, return_details=verbose)

    # Surface conflicts even though reconcile doesn't auto-apply them.
    reg = load_snippet_registry(root)
    snips = reg.get("snippets", {}) if isinstance(reg, dict) else {}
    conflicted_keys: list[str] = []
    if isinstance(snips, dict):
        conflicted_keys = [
            str(k)
            for k, v in snips.items()
            if isinstance(v, dict) and v.get("status") == "conflicted"
        ]

    if stats.get("pending_before", 0) == 0:
        print_success("✅ No pending snippets found.")
        return

    applied = stats.get("applied", 0)
    pending_after = stats.get("pending_after", 0)
    failed = stats.get("failed", 0)
    skipped = stats.get("skipped", 0)

    if applied:
        print_success(f"✅ Applied {applied} pending snippet(s).")
    if pending_after:
        print_warning(f"⚠️ {pending_after} snippet(s) still pending.")
    if skipped:
        print_warning(f"⏭️ {skipped} snippet(s) skipped (missing prerequisites).")
    if failed:
        print_warning(f"❌ {failed} snippet(s) failed during reconcile.")

    if conflicted_keys:
        print_warning(
            f"⚠️ {len(conflicted_keys)} snippet(s) are conflicted. Use --resolve-key <key> --resolve-to pending to re-queue."
        )

    if verbose:
        applied_keys = stats.get("applied_keys") or []
        skipped_keys = stats.get("skipped_keys") or []
        failed_keys = stats.get("failed_keys") or []
        pending_keys = stats.get("pending_keys") or []

        def _print_list(title: str, keys: object) -> None:
            if not isinstance(keys, list) or not keys:
                return
            print_info(f"\n[bold]{title}[/bold]")
            for k in keys:
                if isinstance(k, str) and k.strip():
                    print_info(f"- {k}")

        _print_list("Applied", applied_keys)
        _print_list("Skipped", skipped_keys)
        _print_list("Failed", failed_keys)
        _print_list("Still pending", pending_keys)
        _print_list("Conflicted", conflicted_keys)
