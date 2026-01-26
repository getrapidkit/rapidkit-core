# src / core / services / snippet_injector.py
import importlib
import json
import re
from datetime import datetime, timezone
from importlib import util
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, cast

from jsonschema import ValidationError, validate

from cli.ui.printer import print_info, print_success, print_warning
from core.rendering.template_renderer import render_template
from core.services.env_validator import validate_env


def _infer_inject_group_from_anchor(anchor_stripped: str) -> str:
    """Infer the inject group from an anchor like '# <<<inject:module-env>>>'.

    Falls back to 'settings-fields' for backward compatibility.
    """

    match = re.search(r"<<<inject:(?P<group>[^>]+?)>>>", anchor_stripped)
    if match:
        group = match.group("group").strip()
        if group:
            return group
    return "settings-fields"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit_log_path(project_root: Path) -> Path:
    return project_root / ".rapidkit" / "audit" / "snippet_injections.jsonl"


def _append_audit_event(project_root: Path, event: Dict[str, Any]) -> None:
    path = _audit_log_path(project_root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    except (OSError, TypeError, ValueError):
        # Audit is best-effort; never block install/reconcile.
        return


def load_installed_module_slugs(project_root: Path) -> set[str]:
    """Load installed module slugs from registry.json.

    This is treated as the source of truth for which modules are installed.
    """

    registry_path = project_root / "registry.json"
    if not registry_path.exists():
        return set()
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    installed_raw = payload.get("installed_modules", []) if isinstance(payload, dict) else []
    if not isinstance(installed_raw, list):
        return set()
    slugs: set[str] = set()
    for entry in installed_raw:
        if isinstance(entry, str) and entry.strip():
            slugs.add(entry.strip())
        elif isinstance(entry, dict):
            slug = entry.get("slug") or entry.get("module") or entry.get("name")
            if isinstance(slug, str) and slug.strip():
                slugs.add(slug.strip())
    return slugs


def infer_owner_module_slug(project_root: Path, destination_path: Path) -> Optional[str]:
    """Infer which RapidKit module "owns" a file path.

    Convention: module-owned code lives under:
      src/modules/<tier>/<category>/<module>/...

    If the destination is outside that convention, returns None.
    """

    try:
        rel = destination_path.relative_to(project_root).as_posix()
    except ValueError:
        return None

    parts = [p for p in rel.split("/") if p]
    _MIN_MODULE_PARTS = 5
    if len(parts) < _MIN_MODULE_PARTS:
        return None
    if parts[0] != "src" or parts[1] != "modules":
        return None
    tier, category, module = parts[2], parts[3], parts[4]
    if not (tier and category and module):
        return None
    return f"{tier}/{category}/{module}"


def _stringify_errors(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value)


def _record_snippet_registry_entry(
    *,
    registry_root: Path,
    registry: Dict[str, Any],
    registry_key: str,
    destination_path: Path,
    anchor: str,
    snippet_metadata: Dict[str, Any],
    status: str,
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> None:
    # Backward compatible: keep original keys + add new optional metadata.
    entry: Dict[str, Any] = dict(registry.get("snippets", {}).get(registry_key, {}) or {})

    snippet_version = snippet_metadata.get("version", "0.0.0")
    snippet_priority = snippet_metadata.get("priority", 0)
    template_name = snippet_metadata.get("template")
    module_slug = snippet_metadata.get("module_slug")
    profile = snippet_metadata.get("profile")
    target = snippet_metadata.get("target")
    patch_mode = snippet_metadata.get("patch_mode")

    now = _utc_now_iso()
    try:
        rel_path = destination_path.relative_to(registry_root).as_posix()
    except ValueError:
        rel_path = destination_path.as_posix()

    entry.update(
        {
            "anchor": anchor,
            "version": snippet_version,
            "priority": snippet_priority,
            "file": rel_path,
            "status": status,
            "last_attempt_at": now,
        }
    )
    if template_name:
        entry["template"] = str(template_name)
    if module_slug:
        entry["module_slug"] = str(module_slug)
    if profile:
        entry["profile"] = str(profile)
    if target:
        entry["target"] = target
    if isinstance(patch_mode, str) and patch_mode.strip():
        entry["patch_mode"] = patch_mode.strip()

    # Persist behavior-critical metadata to enable later reconcile without
    # re-loading module configs.
    if "context" in snippet_metadata and isinstance(snippet_metadata.get("context"), dict):
        entry["context"] = snippet_metadata.get("context")
    if "schema" in snippet_metadata and isinstance(snippet_metadata.get("schema"), dict):
        entry["schema"] = snippet_metadata.get("schema")
    if "conflict_resolution" in snippet_metadata:
        entry["conflict_resolution"] = snippet_metadata.get("conflict_resolution")

    if status == "applied":
        entry.setdefault("applied_at", now)
        entry["applied_at"] = now
        entry.pop("last_error", None)
    elif errors:
        entry["last_error"] = _stringify_errors(errors)
    elif warnings:
        entry["last_error"] = _stringify_errors(warnings)

    registry.setdefault("snippets", {})
    registry["snippets"][registry_key] = entry
    save_snippet_registry(registry_root, registry)

    # Audit event (best-effort)
    owner_slug = infer_owner_module_slug(registry_root, destination_path)
    event: Dict[str, Any] = {
        "ts": _utc_now_iso(),
        "event": "snippet_injection_state",
        "key": registry_key,
        "status": status,
        "file": entry.get("file"),
        "anchor": anchor,
        "module_slug": entry.get("module_slug"),
        "owner_module_slug": owner_slug,
        "template": entry.get("template"),
        "version": entry.get("version"),
        "priority": entry.get("priority"),
    }
    if entry.get("last_error"):
        event["error"] = entry.get("last_error")
    _append_audit_event(registry_root, event)


def reconcile_pending_snippets(
    project_root: Path,
    *,
    modules_root: Optional[Path] = None,
    lenient: bool = False,
    include_keys: Optional[set[str]] = None,
    return_details: bool = False,
) -> Dict[str, Any]:
    """Retry pending snippet injections recorded in snippet_registry.json.

    This is intentionally conservative:
    - Only entries with status == 'pending' are retried.
    - On success we mark them 'applied'.
    - On failure we keep them 'pending' (if target missing) or mark 'failed' (if anchor/template missing).

    Returns counts: {pending_before, applied, pending_after, failed}.
    """

    registry = load_snippet_registry(project_root)
    snippets = registry.get("snippets", {}) if isinstance(registry, dict) else {}
    if not isinstance(snippets, dict):
        snippets = {}

    pending_items_all = [
        (k, v) for k, v in snippets.items() if isinstance(v, dict) and v.get("status") == "pending"
    ]

    if include_keys is not None:
        include = {k for k in include_keys if isinstance(k, str) and k}
        pending_items = [(k, v) for k, v in pending_items_all if k in include]
    else:
        pending_items = pending_items_all

    pending_before = len(pending_items)
    applied = 0
    failed = 0
    skipped = 0

    applied_keys: list[str] = []
    failed_keys: list[str] = []
    skipped_keys: list[str] = []

    if pending_before == 0:
        return {"pending_before": 0, "applied": 0, "pending_after": 0, "failed": 0, "skipped": 0}

    modules_root_resolved = (
        modules_root
        if modules_root is not None
        else (Path(__file__).resolve().parents[2] / "modules")
    )

    installed_slugs = load_installed_module_slugs(project_root)

    # Lazy import to avoid circular imports during module import graph.
    from core.services.module_path_resolver import resolve_module_directory

    for registry_key, entry in pending_items:
        snippet_id = registry_key.split("::", 1)[0] if "::" in registry_key else registry_key
        module_slug = entry.get("module_slug")
        template_name = entry.get("template")
        anchor = entry.get("anchor")
        rel_file = entry.get("file")

        if not all(
            isinstance(v, str) and v.strip() for v in (module_slug, template_name, anchor, rel_file)
        ):
            failed += 1
            failed_keys.append(str(registry_key))
            _record_snippet_registry_entry(
                registry_root=project_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=project_root / (rel_file or ""),
                anchor=str(anchor or ""),
                snippet_metadata={"id": snippet_id, **entry},
                status="failed",
                errors=[
                    "pending snippet missing required metadata (module_slug/template/anchor/file)"
                ],
            )
            continue

        # Gate by producer module presence (if registry.json exists and has entries).
        if installed_slugs and str(module_slug) not in installed_slugs:
            skipped += 1
            skipped_keys.append(str(registry_key))
            destination_path = project_root / str(rel_file)
            _record_snippet_registry_entry(
                registry_root=project_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=destination_path,
                anchor=str(anchor),
                snippet_metadata={"id": snippet_id, **entry},
                status="pending",
                errors=[
                    f"producer module '{module_slug}' is not installed (registry.json); skipping reconcile"
                ],
            )
            continue

        # Gate by target owner module presence (dynamic cross-module injections).
        destination_path = project_root / str(rel_file)
        owner_slug = infer_owner_module_slug(project_root, destination_path)
        if installed_slugs and owner_slug and owner_slug not in installed_slugs:
            skipped += 1
            skipped_keys.append(str(registry_key))
            _record_snippet_registry_entry(
                registry_root=project_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=destination_path,
                anchor=str(anchor),
                snippet_metadata={"id": snippet_id, **entry},
                status="pending",
                errors=[
                    f"target owner module '{owner_slug}' is not installed (registry.json); keeping injection pending"
                ],
            )
            continue

        module_dir = resolve_module_directory(modules_root_resolved, str(module_slug))
        template_path = module_dir / "templates" / "snippets" / str(template_name)
        destination_path = project_root / str(rel_file)

        snippet_metadata = {
            "id": snippet_id,
            "version": entry.get("version", "0.0.0"),
            "priority": entry.get("priority", 0),
            "context": entry.get("context") or {},
            "schema": entry.get("schema") or {},
            "conflict_resolution": entry.get("conflict_resolution", "override"),
            "patch_mode": entry.get("patch_mode"),
            "template": str(template_name),
            "module_slug": str(module_slug),
            "profile": entry.get("profile"),
            "target": entry.get("target"),
        }

        result = inject_snippet_enterprise(
            destination_path=destination_path,
            template_path=template_path,
            anchor=str(anchor),
            variables={},
            snippet_metadata=snippet_metadata,
            project_root=project_root,
            lenient=lenient,
        )

        if isinstance(result, dict) and bool(result.get("injected")):
            applied += 1
            applied_keys.append(str(registry_key))
            continue

        # If it didn't inject, decide whether to keep pending or mark failed
        errors = result.get("errors") if isinstance(result, dict) else None
        err_text = _stringify_errors(errors)
        err_lower = err_text.lower()

        # The injector can mark a snippet as conflicted (e.g. malformed marker blocks).
        # Do not overwrite that status back to pending.
        if "mark as conflicted" in err_lower or "malformed snippet block" in err_lower:
            _record_snippet_registry_entry(
                registry_root=project_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=destination_path,
                anchor=str(anchor),
                snippet_metadata=snippet_metadata,
                status="conflicted",
                errors=errors if isinstance(errors, list) else [err_text] if err_text else None,
            )
            continue
        if "anchor" in err_text or "Template path invalid" in err_text:
            failed += 1
            failed_keys.append(str(registry_key))
            _record_snippet_registry_entry(
                registry_root=project_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=destination_path,
                anchor=str(anchor),
                snippet_metadata=snippet_metadata,
                status="failed",
                errors=errors if isinstance(errors, list) else [err_text] if err_text else None,
            )
        else:
            _record_snippet_registry_entry(
                registry_root=project_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=destination_path,
                anchor=str(anchor),
                snippet_metadata=snippet_metadata,
                status="pending",
                errors=errors if isinstance(errors, list) else [err_text] if err_text else None,
            )

    # reload registry to compute pending_after (it may be modified by injection calls)
    final_registry = load_snippet_registry(project_root)
    final_snips = final_registry.get("snippets", {}) if isinstance(final_registry, dict) else {}
    if isinstance(final_snips, dict):
        if include_keys is None:
            pending_after = sum(
                1
                for v in final_snips.values()
                if isinstance(v, dict) and v.get("status") == "pending"
            )
        else:
            include = {k for k in include_keys if isinstance(k, str) and k}
            pending_after = sum(
                1
                for k, v in final_snips.items()
                if k in include and isinstance(v, dict) and v.get("status") == "pending"
            )
    else:
        pending_after = 0
    result_out: Dict[str, Any] = {
        "pending_before": pending_before,
        "applied": applied,
        "pending_after": pending_after,
        "failed": failed,
        "skipped": skipped,
    }

    if return_details:
        include_filter: set[str] | None = (
            {k for k in include_keys if isinstance(k, str) and k}
            if include_keys is not None
            else None
        )
        pending_keys: list[str] = []
        if isinstance(final_snips, dict):
            for k, v in final_snips.items():
                if include_filter is not None and k not in include_filter:
                    continue
                if isinstance(v, dict) and v.get("status") == "pending":
                    pending_keys.append(str(k))

        result_out["applied_keys"] = applied_keys
        result_out["failed_keys"] = failed_keys
        result_out["skipped_keys"] = skipped_keys
        result_out["pending_keys"] = pending_keys

    return result_out


def reconcile_pending_snippets_scoped(
    project_root: Path,
    *,
    scope_slugs: set[str],
    modules_root: Optional[Path] = None,
    lenient: bool = False,
    return_details: bool = False,
) -> Dict[str, Any]:
    """Reconcile pending snippets, but only those related to `scope_slugs`.

    A pending snippet is considered "related" if:
    - its producer module_slug is in scope, OR
    - its inferred owner module (based on target file path) is in scope.

    This keeps post-install reconcile deterministic and fast.
    """

    cleaned_scope = {s.strip().strip("/") for s in scope_slugs if isinstance(s, str) and s.strip()}
    if not cleaned_scope:
        return {"pending_before": 0, "applied": 0, "pending_after": 0, "failed": 0, "skipped": 0}

    registry = load_snippet_registry(project_root)
    snippets = registry.get("snippets", {}) if isinstance(registry, dict) else {}
    if not isinstance(snippets, dict):
        return {"pending_before": 0, "applied": 0, "pending_after": 0, "failed": 0, "skipped": 0}

    # Identify scoped pending keys.
    scoped_keys: set[str] = set()
    for key, entry in snippets.items():
        if not isinstance(entry, dict) or entry.get("status") != "pending":
            continue
        producer = entry.get("module_slug")
        rel_file = entry.get("file")
        producer_ok = isinstance(producer, str) and producer.strip("/") in cleaned_scope
        owner_ok = False
        if isinstance(rel_file, str) and rel_file.strip():
            owner = infer_owner_module_slug(project_root, project_root / rel_file)
            owner_ok = bool(owner and owner.strip("/") in cleaned_scope)
        if producer_ok or owner_ok:
            scoped_keys.add(str(key))

    if not scoped_keys:
        return {"pending_before": 0, "applied": 0, "pending_after": 0, "failed": 0, "skipped": 0}

    return reconcile_pending_snippets(
        project_root,
        modules_root=modules_root,
        lenient=lenient,
        include_keys=scoped_keys,
        return_details=return_details,
    )


def rollback_snippet_injection(  # noqa: PLR0911
    project_root: Path,
    *,
    key: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Rollback a previously applied snippet injection by removing its marker-delimited block.

    This is marker-based (start/end markers) and intentionally conservative.

    Status values:
      - rolled_back: markers found and removed (or would be in dry-run)
      - missing_entry: key not in snippet_registry.json
      - not_applied: registry entry exists but status is not 'applied'
      - missing_file: target file is missing
      - markers_not_found: no matching marker pair found in file
      - error: unexpected I/O or malformed entry
    """

    if not isinstance(key, str) or not key.strip():
        return {"status": "error", "error": "key is required", "dry_run": dry_run}

    registry = load_snippet_registry(project_root)
    snippets = registry.get("snippets", {}) if isinstance(registry, dict) else {}
    if not isinstance(snippets, dict):
        snippets = {}

    entry = snippets.get(key)
    if not isinstance(entry, dict):
        return {"status": "missing_entry", "key": key, "dry_run": dry_run}

    rel_file = entry.get("file")
    if not isinstance(rel_file, str) or not rel_file.strip():
        return {
            "status": "error",
            "key": key,
            "error": "entry.file missing",
            "dry_run": dry_run,
        }

    current_status = entry.get("status")
    if current_status != "applied":
        return {
            "status": "not_applied",
            "key": key,
            "file": rel_file,
            "current_status": current_status,
            "dry_run": dry_run,
        }

    dest = project_root / rel_file
    if not dest.exists():
        return {"status": "missing_file", "key": key, "file": rel_file, "dry_run": dry_run}

    try:
        before = dest.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "status": "error",
            "key": key,
            "file": rel_file,
            "error": f"unable to read file: {exc}",
            "dry_run": dry_run,
        }

    snippet_id = key.split("::", 1)[0] if "::" in key else key
    start_re = re.compile(rf"^\s*.*<<<inject:[^:>]+:{re.escape(snippet_id)}:start>>>\s*$")
    end_re = re.compile(rf"^\s*.*<<<inject:[^:>]+:{re.escape(snippet_id)}:end>>>\s*$")

    lines = before.splitlines(True)
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None
    for idx, line in enumerate(lines):
        if start_idx is None and start_re.match(line):
            start_idx = idx
            continue
        if start_idx is not None and end_re.match(line):
            end_idx = idx
            break

    if start_idx is None or end_idx is None or end_idx < start_idx:
        return {
            "status": "markers_not_found",
            "key": key,
            "file": rel_file,
            "dry_run": dry_run,
        }

    after = "".join(lines[:start_idx] + lines[end_idx + 1 :])

    if not dry_run:
        try:
            dest.write_text(after, encoding="utf-8")
        except OSError as exc:
            return {
                "status": "error",
                "key": key,
                "file": rel_file,
                "error": f"unable to write file: {exc}",
                "dry_run": dry_run,
            }

        now = _utc_now_iso()
        entry["status"] = "pending"
        entry["rolled_back_at"] = now
        entry["updated_at"] = now
        entry.pop("applied_at", None)
        snippets[key] = entry
        registry["snippets"] = snippets
        save_snippet_registry(project_root, registry)

        owner_slug = infer_owner_module_slug(project_root, dest)
        _append_audit_event(
            project_root,
            {
                "ts": now,
                "event": "snippet_rollback",
                "key": key,
                "file": rel_file,
                "from_status": "applied",
                "to_status": "pending",
                "module_slug": entry.get("module_slug"),
                "owner_module_slug": owner_slug,
            },
        )

    return {"status": "rolled_back", "key": key, "file": rel_file, "dry_run": dry_run}


def resolve_conflicted_snippet(
    project_root: Path,
    *,
    key: str,
    to_status: str = "pending",
) -> Dict[str, Any]:
    """Resolve a conflicted snippet by changing its registry status.

    This does not edit any project files; it only updates snippet_registry.json.
    The status change is recorded via the normal snippet registry writer (and thus audited).
    """

    if not isinstance(key, str) or not key.strip():
        return {"status": "error", "error": "key is required"}
    if to_status not in {"pending", "failed"}:
        return {"status": "error", "error": "to_status must be 'pending' or 'failed'"}

    registry = load_snippet_registry(project_root)
    snippets = registry.get("snippets", {}) if isinstance(registry, dict) else {}
    if not isinstance(snippets, dict):
        return {"status": "error", "error": "snippet_registry.json is invalid"}

    entry = snippets.get(key)
    if not isinstance(entry, dict):
        return {"status": "missing_entry", "key": key}

    rel_file = entry.get("file")
    anchor = entry.get("anchor") or ""
    if not isinstance(rel_file, str) or not rel_file.strip():
        return {"status": "error", "key": key, "error": "entry.file missing"}
    if not isinstance(anchor, str):
        anchor = ""

    dest = project_root / rel_file
    snippet_id = key.split("::", 1)[0] if "::" in key else key
    _record_snippet_registry_entry(
        registry_root=project_root,
        registry=registry,
        registry_key=key,
        destination_path=dest,
        anchor=anchor,
        snippet_metadata={"id": snippet_id, **entry},
        status=to_status,
        errors=[f"manually resolved conflict; set status -> {to_status}"],
    )
    return {
        "status": "updated",
        "key": key,
        "file": rel_file,
        "from_status": entry.get("status"),
        "to_status": to_status,
    }


def _format_with_black(text: str) -> tuple[str, Optional[str]]:
    """Format text with Black if available; otherwise return original text.

    Returns (formatted_text, warning_message_if_any).
    """
    # If Black isn't installed, skip formatting silently
    if util.find_spec("black") is None:
        return text, None
    try:
        black = importlib.import_module("black")
    except ImportError as e:  # pragma: no cover - module not available at runtime
        return text, f"⚠️ Black unavailable: {e}. Writing unformatted output."

    Mode = getattr(black, "Mode", None) or getattr(black, "FileMode", None)
    fmt = getattr(black, "format_str", None)
    # Try to get InvalidInput for precise exception handling (newer or older Black)
    invalid_input_exc = getattr(black, "InvalidInput", None)
    if invalid_input_exc is None:
        parsing = getattr(black, "parsing", None)
        if parsing is not None:
            invalid_input_exc = getattr(parsing, "InvalidInput", None)

    if Mode is None or fmt is None:
        return text, None

    exceptions_to_catch: tuple[type[Exception], ...] = (OSError, ValueError, TypeError)
    if isinstance(invalid_input_exc, type) and issubclass(invalid_input_exc, Exception):
        exceptions_to_catch = exceptions_to_catch + (invalid_input_exc,)

    try:
        return fmt(text, mode=Mode()), None
    except exceptions_to_catch as e:
        return text, f"⚠️ Black formatting failed: {e}. Writing unformatted output."


def _try_parse_python_with_libcst(source: str) -> Optional[str]:
    """Best-effort Python syntax validation using libcst.

    Returns None on success, or an error string if parsing fails or libcst is unavailable.
    """

    try:
        libcst = cast(Any, importlib.import_module("libcst"))
    except ImportError:
        return None
    try:
        libcst.parse_module(source)
    except Exception as exc:  # noqa: BLE001
        return str(exc)
    return None


def _find_python_anchor_line_with_libcst(source: str, anchor_stripped: str) -> Optional[int]:
    """Return 0-based line index after which to insert, using libcst to find comment anchors.

    This finds an `EmptyLine` comment matching `anchor_stripped` and returns its end line.
    Returns None if anchor is not found or libcst is unavailable.
    """

    try:
        cst = cast(Any, importlib.import_module("libcst"))
        metadata = cast(Any, importlib.import_module("libcst.metadata"))
        MetadataWrapper = metadata.MetadataWrapper
        PositionProvider = metadata.PositionProvider
    except (ImportError, AttributeError):
        return None

    try:
        module = cst.parse_module(source)
        wrapper = MetadataWrapper(module)
    except Exception:  # noqa: BLE001
        return None

    matches: list[int] = []

    class _Finder(cst.CSTVisitor):  # type: ignore[name-defined]
        METADATA_DEPENDENCIES = (PositionProvider,)

        def visit_EmptyLine(self, node: Any) -> None:
            comment = getattr(node, "comment", None)
            if comment is None:
                return
            value = getattr(comment, "value", None)
            if not isinstance(value, str):
                return
            if value.strip() != anchor_stripped:
                return
            pos = self.get_metadata(PositionProvider, node)
            # libcst lines are 1-based
            matches.append(int(pos.end.line) - 1)

    wrapper.visit(_Finder())
    if not matches:
        return None
    return matches[0]


def _inject_python_snippet_ast(
    *,
    source: str,
    anchor_stripped: str,
    snippet_id: str,
    snippet_lines: list[str],
    indent: str,
    prefix: str,
) -> tuple[Optional[str], Optional[str]]:
    """Return (new_source, error_message)."""

    inject_group = _infer_inject_group_from_anchor(anchor_stripped)
    start_marker = f"{prefix}<<<inject:{inject_group}:{snippet_id}:start>>>"
    end_marker = f"{prefix}<<<inject:{inject_group}:{snippet_id}:end>>>"
    any_start_re = re.compile(rf"^.*<<<inject:[^:>]+:{re.escape(snippet_id)}:start>>>$")
    any_end_re = re.compile(rf"^.*<<<inject:[^:>]+:{re.escape(snippet_id)}:end>>>$")

    lines = source.splitlines(True)

    def _strip_nl(text: str) -> str:
        return text.rstrip("\n").rstrip("\r")

    def _maybe_undouble_newlines(text: str) -> str:
        """Best-effort fix for pathological double-spacing.

        In some environments we have observed snippet bodies ending up with a blank
        line between nearly every statement (i.e. most line breaks become '\n\n').
        When that happens, the injected body contains a very high ratio of blank
        lines. If detected, halve runs of consecutive newlines:
          - '\n\n' -> '\n'
          - '\n\n\n\n' -> '\n\n'
        This preserves intended blank lines while removing the accidental doubling.
        """

        # Detect pathological spacing by looking for pervasive "double breaks"
        # between non-empty lines.
        # - Normal snippets: occasional "\n\n" between blocks.
        # - Doubled spacing: most line breaks become "\n\n".
        single_breaks = len(re.findall(r"\n[\t ]*\S", text))
        double_breaks = len(re.findall(r"\n\n[\t ]*\S", text))
        if single_breaks == 0:
            return text
        _MIN_DOUBLE_BREAKS = 10
        _MIN_DOUBLE_BREAK_RATIO = 0.50
        if double_breaks < _MIN_DOUBLE_BREAKS:
            return text
        if (double_breaks / single_breaks) < _MIN_DOUBLE_BREAK_RATIO:
            return text

        def _halve_newlines(match: re.Match[str]) -> str:
            count = len(match.group(0))
            return "\n" * max(1, count // 2)

        return re.sub(r"\n{2,}", _halve_newlines, text)

    # If block exists, replace it.
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None
    for idx, line in enumerate(lines):
        if any_start_re.match(_strip_nl(line).strip()):
            start_idx = idx
            break
    if start_idx is not None:
        for j in range(start_idx + 1, len(lines)):
            if any_end_re.match(_strip_nl(lines[j]).strip()):
                end_idx = j
                break
        if end_idx is None:
            return None, "start marker found but end marker missing"

        new_block: list[str] = []
        new_block.append(lines[start_idx])
        body_lines: list[str] = []
        for ln in snippet_lines:
            ln_clean = ln.rstrip("\r\n")
            if ln_clean.strip():
                body_lines.append(f"{indent}{ln_clean}\n")
            else:
                body_lines.append("\n")
        body_text = _maybe_undouble_newlines("".join(body_lines))
        new_block.extend(body_text.splitlines(True))
        new_block.append(lines[end_idx])
        return "".join(lines[:start_idx] + new_block + lines[end_idx + 1 :]), None

    # Otherwise, insert after the anchor line.
    anchor_line_idx = _find_python_anchor_line_with_libcst(source, anchor_stripped)
    if anchor_line_idx is None:
        # Fallback to a strict text match for the anchor line.
        for idx, line in enumerate(lines):
            if _strip_nl(line).strip() == anchor_stripped:
                anchor_line_idx = idx
                break
    if anchor_line_idx is None:
        return None, "anchor not found"

    insert_at = anchor_line_idx + 1
    block_lines: list[str] = [f"{indent}{start_marker}\n"]
    body_lines = []
    for ln in snippet_lines:
        ln_clean = ln.rstrip("\r\n")
        if ln_clean.strip():
            body_lines.append(f"{indent}{ln_clean}\n")
        else:
            body_lines.append("\n")
    body_text = _maybe_undouble_newlines("".join(body_lines))
    block_lines.extend(body_text.splitlines(True))
    block_lines.append(f"{indent}{end_marker}\n")

    return "".join(lines[:insert_at] + block_lines + lines[insert_at:]), None


def parse_poetry_dependency_line(line: str) -> tuple[Optional[str], Optional[str]]:
    """Parse a dependency assignment line from [tool.poetry.dependencies].

    Supports inline comments and dict-style specs. Returns (name, raw_value)
    where raw_value keeps surrounding quotes or braces. None, None if not a dep line.
    """
    raw = line.rstrip()
    if not raw or raw.lstrip().startswith("#"):
        return None, None
    in_s = False
    in_d = False
    buf = []
    for ch in raw:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        if ch == "#" and not in_s and not in_d:
            break
        buf.append(ch)
    cleaned = "".join(buf).strip()
    if "=" not in cleaned:
        return None, None
    key, value = cleaned.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not re.match(r"^[A-Za-z0-9_\-]+$", key):
        return None, None
    return key, value


def filter_and_update_poetry_dependencies_snippet(destination_path: Path, snippet: str) -> str:
    """Idempotently inject dependency snippet into [tool.poetry.dependencies] section.

    Design goals ("pro mode"):
    - Preserve original ordering, spacing and inline comments of all lines BEFORE the anchor.
    - Preserve the anchor line exactly; create it if missing.
    - Maintain a clean, alphabetically sorted block of injected module dependencies AFTER the anchor.
    - Avoid duplicating packages that already exist either before or after the anchor.
    - If a dependency already exists in the injected block, update its version/value in place logically
      (effectively by rebuilding the injected block) while keeping base lines untouched.
    - Never pull injected deps up into the base region or reorder base deps.
    - Produce minimal diffs when adding new modules.
    """
    if not destination_path.exists():
        return snippet

    anchor = "# <<<inject:module-dependencies>>>"
    content = destination_path.read_text(encoding="utf-8")

    # Locate dependency section boundaries
    start_match = re.search(r"^\[tool\.poetry\.dependencies\]", content, re.MULTILINE)
    if not start_match:
        # Append a fresh section if somehow missing
        injected_block = ["[tool.poetry.dependencies]", anchor]
        # Normalize snippet lines to simple dependency lines (strip blank)
        for line in snippet.splitlines():
            pkg, ver = parse_poetry_dependency_line(line)
            if pkg and ver:
                injected_block.append(f"{pkg} = {ver}")
        return content.rstrip() + "\n\n" + "\n".join(injected_block) + "\n"

    start_pos = start_match.start()
    next_section_match = re.search(r"^\[.+\]", content[start_pos + 1 :], re.MULTILINE)
    end_pos = next_section_match.start() + start_pos + 1 if next_section_match else len(content)
    section_text = content[start_pos:end_pos]
    section_lines = section_text.splitlines()

    # Ensure anchor exists (if not, append it at end of section, preserving existing trailing newline policy)
    if not any(anchor in line for line in section_lines):
        # preserve potential final blank line inside section
        if section_lines and section_lines[-1].strip() == "":
            section_lines.insert(len(section_lines) - 1, anchor)
        else:
            section_lines.append(anchor)

    # Re-scan for anchor index (first occurrence dominates)
    for idx, line in enumerate(section_lines):
        if anchor in line:
            anchor_idx = idx
            break
    else:  # pragma: no cover (defensive)
        return content

    header_line = section_lines[0]
    base_lines = section_lines[1:anchor_idx]  # keep EXACT
    injected_existing_lines = section_lines[anchor_idx + 1 :]

    # Collect package names already defined in base part (so we don't duplicate them)
    base_packages = set()
    for ln in base_lines:
        pkg, ver = parse_poetry_dependency_line(ln)
        if pkg and ver:
            base_packages.add(pkg)

    # Parse existing injected block
    injected_existing: Dict[str, str] = {}
    for ln in injected_existing_lines:
        pkg, ver = parse_poetry_dependency_line(ln)
        if pkg and ver:
            injected_existing[pkg] = ver

    # Parse new snippet deps
    snippet_deps: Dict[str, str] = {}
    for ln in snippet.splitlines():
        pkg, ver = parse_poetry_dependency_line(ln)
        if pkg and ver:
            snippet_deps[pkg] = ver

    # Merge: existing injected first then update with snippet (snippet wins)
    merged_injected: Dict[str, str] = dict(injected_existing)
    for pkg, ver in snippet_deps.items():
        if pkg in base_packages:
            # core/base dependency: do NOT duplicate or overwrite formatting of base line
            continue
        merged_injected[pkg] = ver

    # Optional full alignment (user preference): align '=' for base + injected without losing comments.
    # We only touch lines that are dependency assignments; comments/blank lines stay verbatim.
    align_all = True

    # Helper to safely split out an inline comment while respecting quotes
    def _split_inline_comment(raw_line: str) -> tuple[str, str]:
        in_s = in_d = False
        for i, ch in enumerate(raw_line):
            if ch == "'" and not in_d:
                in_s = not in_s
            elif ch == '"' and not in_s:
                in_d = not in_d
            elif ch == "#" and not in_s and not in_d:
                # Ensure single leading space before '#'
                left = raw_line[:i].rstrip()
                comment = raw_line[i:].lstrip()  # drop excess spaces before '#'
                return left, (
                    "# " + comment[1:].lstrip() if not comment.startswith("# ") else comment
                )
        return raw_line.rstrip(), ""

    # Collect dependency metadata from base lines
    base_meta = []  # (original_index, pkg, value, comment, original_line or None if reconstructed)
    if align_all:
        for idx, ln in enumerate(base_lines):
            left, comment = _split_inline_comment(ln)
            pkg, val = parse_poetry_dependency_line(left)
            if pkg and val:
                base_meta.append((idx, pkg, val, comment, ln))

    # Determine max key length across base deps + injected deps (for alignment column)
    if align_all and base_meta:
        max_key_len = (
            max([len(m[1]) for m in base_meta] + [len(k) for k in merged_injected])
            if merged_injected
            else max(len(m[1]) for m in base_meta)
        )
    else:
        max_key_len = max((len(k) for k in merged_injected), default=0)

    def _format_dep(pkg: str, val: str, comment: str) -> str:
        padding = " " * (max_key_len - len(pkg)) if max_key_len > len(pkg) else ""
        line = f"{pkg}{padding} = {val}"
        if comment:
            # Ensure single space before comment
            if not comment.startswith("#"):
                comment = "# " + comment
            line += "  " + comment if not line.endswith(" ") else comment
        return line

    # Rebuild base lines with alignment
    if align_all and base_meta:
        base_lines_aligned = base_lines[:]  # copy
        for idx, pkg, val, comment, _orig in base_meta:
            base_lines_aligned[idx] = _format_dep(pkg, val, comment)
    else:
        base_lines_aligned = base_lines

    # Build new injected block lines (alphabetical) with alignment based on combined key width
    new_injected_lines = [_format_dep(pkg, ver, "") for pkg, ver in sorted(merged_injected.items())]

    # Reassemble section: header + aligned base lines + anchor + aligned injected lines + trailing blank
    rebuilt_section_lines = [header_line] + base_lines_aligned + [anchor] + new_injected_lines

    # Preserve a single blank line termination inside section for readability
    if not (rebuilt_section_lines and rebuilt_section_lines[-1].strip() == ""):
        rebuilt_section_lines.append("")

    new_section_text = "\n".join(rebuilt_section_lines)
    new_content = content[:start_pos] + new_section_text + content[end_pos:]
    return new_content


def inject_dependencies(
    destination_path: Path, snippet: str, file_type: str = "requirements"
) -> str:
    """
    Inject dependencies into a file, handling both requirements.txt and pyproject.toml (Poetry).

    Args:
        destination_path (Path): Path to the target file.
        snippet (str): Dependency snippet to inject.
        file_type (str): 'requirements' or 'poetry'.

    Returns:
        str: Updated file content.
    """
    if not destination_path.exists():
        return snippet

    content = destination_path.read_text(encoding="utf-8")
    anchor = "# <<<inject:module-dependencies>>>"

    if file_type == "poetry":
        # -------------------
        # Poetry: TOML style
        # -------------------
        snippet_deps: Dict[str, str] = {}
        for line in snippet.splitlines():
            if "=" not in line:
                continue
            pkg, ver = [x.strip() for x in line.split("=", 1)]
            snippet_deps[pkg] = ver

        start_match = re.search(r"^\[tool\.poetry\.dependencies\]", content, re.MULTILINE)
        if not start_match:
            return content + "\n" + snippet

        start_pos = start_match.start()
        next_section_match = re.search(r"^\[.+\]", content[start_pos + 1 :], re.MULTILINE)
        end_pos = next_section_match.start() + start_pos + 1 if next_section_match else len(content)
        deps_section = content[start_pos:end_pos]

        if anchor in deps_section:
            before_anchor, after_anchor = deps_section.split(anchor, 1)
        else:
            before_anchor, after_anchor = deps_section, ""

        existing_deps: Dict[str, str] = {}
        for line in before_anchor.splitlines()[1:]:  # skip header
            if "=" in line:
                pkg, ver = [x.strip() for x in line.split("=", 1)]
                if pkg not in snippet_deps:
                    existing_deps[pkg] = ver

        injected_deps: Dict[str, str] = {}
        for line in after_anchor.splitlines():
            if "=" in line:
                pkg, ver = [x.strip() for x in line.split("=", 1)]
                injected_deps[pkg] = ver

        existing_deps.update(snippet_deps)
        injected_deps.update(snippet_deps)

        max_len = max((len(pkg) for pkg in existing_deps | injected_deps), default=0)
        new_lines = [before_anchor.splitlines()[0]]  # header
        for pkg, ver in sorted(existing_deps.items()):
            if pkg in snippet_deps:
                continue
            spaces = " " * (max_len - len(pkg))
            new_lines.append(f"{pkg}{spaces} = {ver}")

        new_lines.append(anchor)
        for pkg, ver in sorted(injected_deps.items()):
            spaces = " " * (max_len - len(pkg))
            new_lines.append(f"{pkg}{spaces} = {ver}")

        new_lines.append("")
        new_deps_section = "\n".join(new_lines)
        return content[:start_pos] + new_deps_section + content[end_pos:]

    elif file_type == "requirements":
        # -------------------------
        # requirements.txt style
        # -------------------------
        if anchor not in content:
            return content + "\n" + snippet
        before, after = content.split(anchor, 1)
        req_existing_deps: Set[str] = {ln.strip() for ln in after.splitlines() if ln.strip()}
        new_lines = [line for line in snippet.splitlines() if line.strip() not in req_existing_deps]
        updated_content = "\n".join([before.rstrip(), anchor] + new_lines + [""])
        return updated_content
    else:  # pragma: no cover - defensive
        raise ValueError("file_type must be 'requirements' or 'poetry'")


def remove_inject_anchors(filepath: Path) -> None:
    """
    Removes all snippet anchor comments (e.g. # <<<inject:auth-login>>>) from the file,
    even if anchor is followed by code on the same line.
    """
    content = filepath.read_text(encoding="utf-8")
    # Remove anchor comments anywhere in the line
    cleaned = re.sub(r"#\s*<<<inject:[^>]+>>>", "", content)
    # Remove resulting empty lines
    cleaned = re.sub(r"^\s*\n", "", cleaned, flags=re.MULTILINE)
    filepath.write_text(cleaned, encoding="utf-8")


def inject_snippet_from_template(
    destination_path: Path,
    snippet_template_path: Path,
    anchor: str,
    variables: Optional[Dict[str, Any]] = None,
) -> None:
    if not destination_path.exists():
        print_warning(f"⚠️ File not found: {destination_path}")
        return

    content = destination_path.read_text(encoding="utf-8")
    anchor_pattern = re.compile(rf"^(?:[ \t]*){re.escape(anchor)}\s*$", re.MULTILINE)
    match = anchor_pattern.search(content)
    if not match:
        print_warning(
            f"⚠️ Anchor '{anchor}' not found in {destination_path.name}, skipping snippet injection"
        )
        return

    # Render snippet
    snippet = render_template(snippet_template_path, variables or {})

    # Smart filter/update for pyproject.toml dependencies
    if destination_path.name == "pyproject.toml":
        snippet = filter_and_update_poetry_dependencies_snippet(destination_path, snippet)

    # Check for duplicate injection
    snippet_marker = snippet.splitlines()[0].strip() if snippet else ""
    if snippet_marker and snippet_marker in content:
        print_info(f"🔁 Snippet already injected in {destination_path.name}")
        return

    # Preserve exact indentation of the anchor
    indent = match.group(0).split(anchor)[0].replace("\t", "    ")
    indented_snippet = "\n".join(
        indent + line if line.strip() else indent for line in snippet.splitlines()
    ).rstrip()

    # Replace anchor with anchor + indented snippet
    new_content = anchor_pattern.sub(f"{match.group(0)}\n{indented_snippet}", content)
    destination_path.write_text(new_content, encoding="utf-8")
    print_success(f"✅ Injected snippet into {destination_path.name}")


def load_snippet_registry(project_root: Path) -> Dict[str, Any]:
    canonical_registry_path = project_root / ".rapidkit" / "snippet_registry.json"
    legacy_registry_path = project_root / "snippet_registry.json"
    registry_path = (
        canonical_registry_path if canonical_registry_path.exists() else legacy_registry_path
    )
    try:
        return (
            json.loads(registry_path.read_text(encoding="utf-8"))
            if registry_path.exists()
            else {"snippets": {}}
        )
    except json.JSONDecodeError:
        print_warning(
            "⚠️ Corrupted snippet_registry.json, initializing empty "
            "(expected at .rapidkit/snippet_registry.json)"
        )
        return {"snippets": {}}


def save_snippet_registry(project_root: Path, registry: Dict[str, Any]) -> None:
    registry_dir = project_root / ".rapidkit"
    registry_path = registry_dir / "snippet_registry.json"
    try:
        registry_dir.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    except (OSError, TypeError, ValueError) as e:
        print_warning(f"⚠️ Failed to save .rapidkit/snippet_registry.json: {e}")


def validate_snippet_schema(snippet: str, schema: Dict[str, Any]) -> bool:
    """Validate snippet against schema."""

    # --- Professional: auto-detect env format and bypass schema validation for env files ---
    def is_env_snippet(snippet: str) -> bool:
        env_lines = [
            line
            for line in snippet.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        # Heuristic: at least 2 lines, all match KEY=VALUE, no colons
        if not env_lines:
            return False
        env_pattern = re.compile(r"^[A-Z0-9_]+\s*=")
        env_like = sum(1 for line in env_lines if env_pattern.match(line) and ":" not in line)
        return env_like >= max(1, len(env_lines) // 2)

    if is_env_snippet(snippet):
        # For env files, skip schema validation (they are just key=value pairs)
        return True

    # If the snippet has no schema properties defined, skip validation (useful for
    # settings-fields snippets that contain Pydantic Field declarations which are
    # difficult to parse reliably here).
    if not schema or not schema.get("properties"):
        return True

    try:
        snippet_dict = {}
        for raw_line in snippet.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                print_warning(f"⚠️ Skipping malformed line in snippet: {line}")
                continue
            key, value_part = line.split(":", 1)
            key = key.strip()
            if "Field(" in value_part:
                default_match = re.search(r"Field\\(default=([^,)]+)", value_part)
                if not default_match:
                    print_warning(f"⚠️ Unrecognized Field format in line: {line}")
                    continue
                value = default_match.group(1).strip()
            else:
                value_match = re.search(r"=\\s*(\\S+)", value_part)
                if not value_match:
                    print_warning(f"⚠️ Unrecognized assignment format in line: {line}")
                    continue
                value = value_match.group(1).strip()

            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            else:
                print_warning(f"⚠️ Unrecognized value format in line: {line}")
                continue
            snippet_dict[key] = value

        if not snippet_dict:
            print_warning("⚠️ No valid settings found in snippet for schema validation")
            return False

        validate(instance=snippet_dict, schema=schema)
        return True
    except ValidationError as e:
        print_warning(f"⚠️ Schema validation failed: {e}")
        return False
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        print_warning(f"⚠️ Error parsing snippet for schema validation: {e}")
        return False


def merge_snippets(
    existing_snippet: List[str],
    new_snippet: List[str],
    indent: str,
    snippet_metadata: Dict[str, Any],
) -> List[str]:
    """Merge two snippets, keeping valid existing fields, new fields, and preserving comments."""
    schema_properties = snippet_metadata.get("schema", {}).get("properties", {})
    existing_fields = {}
    for line in existing_snippet:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            field_name = stripped.split(":", 1)[0].strip()
            existing_fields[field_name] = line

    new_lines = []
    new_field_names = set()
    for line in new_snippet:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            new_lines.append(f"{indent}{line}" if line.strip() else indent)
        else:
            field_name = stripped.split(":", 1)[0].strip()
            new_field_names.add(field_name)
            if field_name in schema_properties:
                new_lines.append(f"{indent}{line}")

    # Only keep existing fields that are in the new schema and not in the new snippet
    for field_name, line in existing_fields.items():
        if field_name in schema_properties and field_name not in new_field_names:
            new_lines.append(f"{indent}{line}")

    return new_lines


def inject_snippet_enterprise(  # noqa: PLR0911
    destination_path: Path,
    template_path: Optional[Path],
    anchor: str,
    variables: Dict[str, Any],
    snippet_metadata: Dict[str, Any],
    project_root: Optional[Path] = None,
    *,
    lenient: bool = False,
) -> Dict[str, object]:
    snippet_id = snippet_metadata.get("id", "unknown")
    snippet_version = snippet_metadata.get("version", "0.0.0")
    schema = snippet_metadata.get("schema", {})
    conflict_resolution = snippet_metadata.get("conflict_resolution", "override")
    print_info(
        f"🔍 Checking injection for {destination_path} with anchor '{anchor}' (ID: {snippet_id}, Version: {snippet_version})"
    )

    def _result(
        injected: bool = False,
        blocked: bool = False,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
    ) -> Dict[str, object]:
        return {
            "injected": injected,
            "blocked": blocked,
            "warnings": warnings or [],
            "errors": errors or [],
        }

    if not (template_path and template_path.exists()):
        print_warning(f"⚠️ Template path invalid: {template_path}")
        return _result(False, True, warnings=[], errors=[f"Template path invalid: {template_path}"])

    template_variables: Dict[str, Any] = dict(variables or {})
    snippet_context = snippet_metadata.get("context") or {}
    if isinstance(snippet_context, dict):
        for key, value in snippet_context.items():
            template_variables.setdefault(key, value)
        template_variables.setdefault("snippet_context", snippet_context)

    snippet = render_template(template_path, template_variables)

    # --- Dynamic ENV validation for env snippets ---
    def is_env_snippet_text(snippet: str) -> bool:
        env_lines = [
            line
            for line in snippet.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        env_pattern = re.compile(r"^[A-Z0-9_]+\s*=")
        env_like = sum(1 for line in env_lines if env_pattern.match(line) and ":" not in line)
        return env_like >= max(1, len(env_lines) // 2)

    early_error: Optional[Dict[str, object]] = None

    if is_env_snippet_text(snippet) and not early_error:
        # --- Collect all env schemas dynamically ---
        # Start from the snippet's own schema properties (if provided) so per-snippet rules apply
        snippet_props = snippet_metadata.get("schema", {}).get("properties", {}) or {}
        merged_schema = dict(snippet_props)

        modules_path = Path(__file__).parent.parent.parent / "modules"
        if modules_path.exists():
            for module_dir in modules_path.iterdir():
                schema_path = module_dir / "config" / "env_schema.py"
                if not schema_path.exists():
                    continue
                try:
                    spec = util.spec_from_file_location(
                        f"env_schema_{module_dir.name}", str(schema_path)
                    )
                    if not spec or not spec.loader:  # guard
                        raise ImportError("Invalid spec for snippet hook module")
                    mod = util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    env_schema = getattr(mod, "ENV_SCHEMA", {}) or {}
                    for k, v in env_schema.items():
                        if k not in merged_schema:
                            merged_schema[k] = v
                except (ImportError, OSError):
                    continue

        # Parse env snippet to dict
        def parse_env_snippet(snippet: str) -> Dict[str, str]:
            env: Dict[str, str] = {}
            for line in snippet.splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
            return env

        env_dict = parse_env_snippet(snippet)
        try:
            _validated, is_valid, errors = validate_env(
                env_dict, schema=merged_schema, lenient=lenient
            )
        except (ValueError, TypeError) as e:
            print_warning(f"⚠️ ENV validation failed: {e}")
            early_error = _result(False, True, warnings=[str(e)], errors=[str(e)])
        if not is_valid or errors:
            print_warning("❌ ENV validation failed. Inject blocked. Errors:")
            for err in errors:
                print_warning(f"  - {err}")
            early_error = _result(False, True, warnings=[], errors=errors)

    # --- End dynamic env validation ---

    if not early_error and not validate_snippet_schema(snippet, schema):
        print_warning(f"⚠️ Snippet {snippet_id} failed schema validation")
        early_error = _result(
            False,
            True,
            warnings=[],
            errors=[f"schema validation failed for {snippet_id}"],
        )

    snippet_lines = [line.rstrip() for line in snippet.splitlines()]
    if not early_error and not any(line.strip() for line in snippet_lines):
        print_warning(f"⚠️ Snippet is empty for {destination_path.name}, skipping")
        early_error = _result(
            False,
            True,
            warnings=[],
            errors=[f"empty snippet for {destination_path.name}"],
        )

    def is_env_file(path: Path) -> bool:
        return path.name.startswith(".env")

    t_path = Path(destination_path)
    registry_root = project_root if project_root else t_path.parent
    registry = load_snippet_registry(registry_root)
    registry_key = f"{snippet_id}::{t_path.name}"

    # Default patch mode:
    # - Only for Python files
    # - Only when not explicitly provided
    # - Never for .env files
    patch_mode = snippet_metadata.get("patch_mode")
    if (
        t_path.suffix == ".py"
        and not is_env_file(t_path)
        and not (isinstance(patch_mode, str) and patch_mode.strip())
    ):
        snippet_metadata["patch_mode"] = "ast_py"

    # Ensure extra metadata is preserved for later reconcile.
    # (Do NOT persist user-provided variables; keep only module-owned metadata.)
    if "module_slug" not in snippet_metadata:
        snippet_metadata["module_slug"] = None
    if "template" not in snippet_metadata:
        snippet_metadata["template"] = None

    if not t_path.exists():
        # Never auto-create module-owned target files.
        # Cross-module injections must not create stubs for modules that aren't installed.
        owner_slug = infer_owner_module_slug(registry_root, t_path)
        if owner_slug:
            message = (
                f"Target file {t_path} does not exist. "
                f"Refusing to auto-create module-owned files for '{owner_slug}'. "
                "Install that module first (it owns this file), then retry or run `rapidkit reconcile`."
            )
            print_warning(f"❌ {message}")
            _record_snippet_registry_entry(
                registry_root=registry_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=t_path,
                anchor=anchor,
                snippet_metadata=snippet_metadata,
                status="pending",
                errors=[message],
            )
            return _result(False, True, warnings=[], errors=[message])

        t_path.parent.mkdir(parents=True, exist_ok=True)
        t_path.write_text(f"{anchor}\n", encoding="utf-8")

    content = t_path.read_text(encoding="utf-8")
    anchor_stripped = anchor.strip()
    anchor_pattern = re.compile(rf"^(\s*){re.escape(anchor_stripped)}\s*$", re.MULTILINE)
    matches = list(anchor_pattern.finditer(content))
    if not matches:
        message = f"anchor '{anchor_stripped}' not found in {t_path}"
        print_warning(f"❌ Anchor '{anchor_stripped}' not found in {t_path}. Injection blocked.")
        _record_snippet_registry_entry(
            registry_root=registry_root,
            registry=registry,
            registry_key=registry_key,
            destination_path=t_path,
            anchor=anchor,
            snippet_metadata=snippet_metadata,
            status="failed",
            errors=[message],
        )
        return _result(False, True, warnings=[], errors=[message])

    if len(matches) > 1:
        print_warning(
            f"⚠️ Multiple anchors found for '{anchor_stripped}' in {t_path.name}, injecting after first."
        )
    match = matches[0]
    indent = match.group(1)

    # Reuse the same comment/anchor prefix that appears in the template's
    # anchor so injected start/end markers match the host file's comment style
    # (e.g. '#' for shell/Python, '//' for TypeScript/JS).
    prefix = anchor_stripped.split("<<<", 1)[0] if "<<<" in anchor_stripped else "# "
    inject_group = _infer_inject_group_from_anchor(anchor_stripped)
    start_marker = f"{prefix}<<<inject:{inject_group}:{snippet_id}:start>>>"
    end_marker = f"{prefix}<<<inject:{inject_group}:{snippet_id}:end>>>"
    any_start_re = re.compile(rf"^.*<<<inject:[^:>]+:{re.escape(snippet_id)}:start>>>$")
    any_end_re = re.compile(rf"^.*<<<inject:[^:>]+:{re.escape(snippet_id)}:end>>>$")

    # Extract existing section if present
    lines = content.splitlines()
    existing_snippet_lines = []
    section_start = None
    section_end = None
    i = 0
    while i < len(lines):
        if any_start_re.match(lines[i].strip()):
            section_start = i
            j = i + 1
            while j < len(lines) and not any_end_re.match(lines[j].strip()):
                existing_snippet_lines.append(lines[j])
                j += 1
            section_end = j if j < len(lines) and any_end_re.match(lines[j].strip()) else None
            break
        i += 1

    if section_start is not None and section_end is None:
        message = (
            f"Malformed snippet block for '{snippet_id}' in {t_path.name}: start marker found but end marker is missing. "
            "Refusing to modify file; mark as conflicted and resolve manually."
        )
        print_warning(f"❌ {message}")
        _record_snippet_registry_entry(
            registry_root=registry_root,
            registry=registry,
            registry_key=registry_key,
            destination_path=t_path,
            anchor=anchor,
            snippet_metadata=snippet_metadata,
            status="conflicted",
            errors=[message],
        )
        return _result(False, True, warnings=[], errors=[message])

    if section_start is not None and section_end is not None:
        # Detect duplicate blocks (multiple start markers for the same snippet id).
        for k in range(section_end + 1, len(lines)):
            if any_start_re.match(lines[k].strip()):
                message = (
                    f"Multiple snippet blocks detected for '{snippet_id}' in {t_path.name}. "
                    "Refusing to modify file; mark as conflicted and resolve manually."
                )
                print_warning(f"❌ {message}")
                _record_snippet_registry_entry(
                    registry_root=registry_root,
                    registry=registry,
                    registry_key=registry_key,
                    destination_path=t_path,
                    anchor=anchor,
                    snippet_metadata=snippet_metadata,
                    status="conflicted",
                    errors=[message],
                )
                return _result(False, True, warnings=[], errors=[message])

    existing_snippet_lines_stripped = [ln.strip() for ln in existing_snippet_lines if ln.strip()]
    snippet_lines_stripped = [ln.strip() for ln in snippet_lines if ln.strip()]

    existing_reg = registry["snippets"].get(registry_key, {})
    if (
        not early_error
        and existing_reg.get("version") == snippet_version
        and existing_snippet_lines_stripped == snippet_lines_stripped
        and section_start is not None
    ):
        print_info(f"ℹ️ Snippet {snippet_id} (v{snippet_version}) already present in {t_path.name}")
        early_error = _result(
            False, False, warnings=[f"already present in {t_path.name}"], errors=[]
        )

    if conflict_resolution == "merge" and section_start is not None:
        merged = merge_snippets(existing_snippet_lines, snippet_lines, indent, snippet_metadata)
        new_snippet_lines = [ln for ln in merged if ln.strip()]
    else:
        new_snippet_lines = [
            ((indent + ln.rstrip("\r\n")) if ln.strip() else indent) for ln in snippet_lines
        ]

    # Build new file content: remove old section, inject new one after anchor
    new_lines = []
    injected = False
    i = 0
    while i < len(lines):
        if section_start is not None and section_start == i:
            # skip old section
            i = (section_end + 1) if section_end is not None else i + 1
            continue
        if not injected and anchor_pattern.match(lines[i]):
            new_lines.append(lines[i])
            new_lines.append(f"{indent}{start_marker}")
            new_lines.extend(new_snippet_lines)
            new_lines.append(f"{indent}{end_marker}")
            injected = True
            i += 1
            continue
        new_lines.append(lines[i])
        i += 1

    if not injected and not early_error:
        # If somehow anchor wasn’t matched in the loop (shouldn’t happen), append at top
        new_lines = [anchor, f"{start_marker}"] + new_snippet_lines + [f"{end_marker}"] + new_lines

    output = "\n".join(new_lines) + "\n"
    if early_error:
        # Record failure for auditability (do not create/modify the target beyond what we already did).
        errors_value = early_error.get("errors", []) if isinstance(early_error, dict) else []
        warnings_value = early_error.get("warnings", []) if isinstance(early_error, dict) else []
        errors_list = (
            [str(e) for e in errors_value]
            if isinstance(errors_value, list)
            else [str(errors_value)]
        )
        warnings_list = (
            [str(w) for w in warnings_value]
            if isinstance(warnings_value, list)
            else [str(warnings_value)]
        )
        _record_snippet_registry_entry(
            registry_root=registry_root,
            registry=registry,
            registry_key=registry_key,
            destination_path=t_path,
            anchor=anchor,
            snippet_metadata=snippet_metadata,
            status="failed",
            errors=errors_list,
            warnings=warnings_list,
        )
        return early_error

    patch_mode = snippet_metadata.get("patch_mode")
    patch_mode_norm = (
        patch_mode.strip().lower() if isinstance(patch_mode, str) and patch_mode.strip() else None
    )

    if is_env_file(t_path):
        t_path.write_text(output, encoding="utf-8")
    elif patch_mode_norm == "no_touch":
        # no-touch mode: do not run any formatter over the full file.
        t_path.write_text(output, encoding="utf-8")
    elif patch_mode_norm == "ast_py" and t_path.suffix == ".py":
        # ast_py mode: use libcst-aware anchor matching to insert/replace without formatters.
        input_parse_error = _try_parse_python_with_libcst(content)
        if input_parse_error:
            message = (
                f"AST validation failed for {t_path.name} before injection. "
                "Refusing to modify file; mark as conflicted. "
                f"Error: {input_parse_error}"
            )
            print_warning(f"❌ {message}")
            _record_snippet_registry_entry(
                registry_root=registry_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=t_path,
                anchor=anchor,
                snippet_metadata=snippet_metadata,
                status="conflicted",
                errors=[message],
            )
            return _result(False, True, warnings=[], errors=[message])

        new_source, inject_error = _inject_python_snippet_ast(
            source=content,
            anchor_stripped=anchor_stripped,
            snippet_id=snippet_id,
            snippet_lines=snippet_lines,
            indent=indent,
            prefix=prefix,
        )
        if inject_error:
            message = (
                f"AST injection failed for {t_path.name}: {inject_error}. "
                "Refusing to modify file; mark as conflicted."
            )
            print_warning(f"❌ {message}")
            _record_snippet_registry_entry(
                registry_root=registry_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=t_path,
                anchor=anchor,
                snippet_metadata=snippet_metadata,
                status="conflicted",
                errors=[message],
            )
            return _result(False, True, warnings=[], errors=[message])

        parse_error = _try_parse_python_with_libcst(new_source or "")
        if parse_error:
            message = (
                f"AST validation failed for {t_path.name} after injection. "
                "Refusing to write; mark as conflicted. "
                f"Error: {parse_error}"
            )
            print_warning(f"❌ {message}")
            _record_snippet_registry_entry(
                registry_root=registry_root,
                registry=registry,
                registry_key=registry_key,
                destination_path=t_path,
                anchor=anchor,
                snippet_metadata=snippet_metadata,
                status="conflicted",
                errors=[message],
            )
            return _result(False, True, warnings=[], errors=[message])

        t_path.write_text(new_source or "", encoding="utf-8")
    else:
        formatted, warn = _format_with_black(output)
        if warn:
            print_warning(f"{warn} (file: {t_path.name})")
        t_path.write_text(formatted, encoding="utf-8")

    print_success(f"✅ Injected snippet {snippet_id} (v{snippet_version}) into {t_path.name}")

    _record_snippet_registry_entry(
        registry_root=registry_root,
        registry=registry,
        registry_key=registry_key,
        destination_path=t_path,
        anchor=anchor,
        snippet_metadata=snippet_metadata,
        status="applied",
    )
    return _result(True, False, warnings=[], errors=[])
