from __future__ import annotations

import json
import re
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, cast

import yaml
from packaging.version import InvalidVersion, Version

DEFAULT_CHANGE_DESCRIPTION = "Automated patch release triggered by content hash change"
DEFAULT_STATE_FILENAME = ".module_state.json"
DEFAULT_PENDING_CHANGELOG_FILENAME = ".module_pending_changelog.yaml"
DEFAULT_EXCLUDED_DIRS = {".rapidkit", "__pycache__", ".pytest_cache", "tests", ".git"}
# ``module.verify.json`` is regenerated with timestamps during tests; ignore it to
# avoid content hash churn.
DEFAULT_EXCLUDED_FILES = {DEFAULT_STATE_FILENAME, "module.verify.json"}
_MIN_VERSION_COMPONENTS = 3


def ensure_version_consistency(
    module_root: Path,
    config: Optional[Mapping[str, Any]] = None,
    *,
    change_description: str = DEFAULT_CHANGE_DESCRIPTION,
    state_filename: str = DEFAULT_STATE_FILENAME,
    excluded_dirs: Optional[Iterable[str]] = None,
    excluded_files: Optional[Iterable[str]] = None,
    changelog_metadata: Optional[Mapping[str, Any]] = None,
    pending_changelog_filename: Optional[str] = DEFAULT_PENDING_CHANGELOG_FILENAME,
    clear_pending_changelog: bool = True,
) -> Tuple[Dict[str, Any], bool]:
    """Ensure ``module.yaml`` version reflects the current template hash.

    Returns a tuple of (updated_config, bumped?) where ``updated_config`` reflects the
    on-disk ``module.yaml`` after any potential patch increment.
    """

    root = module_root.resolve()
    if config is not None:
        config_payload: Dict[str, Any] = dict(config)
    else:
        config_payload = _load_config(root)

    directories = set(excluded_dirs or DEFAULT_EXCLUDED_DIRS)
    files = set(excluded_files or DEFAULT_EXCLUDED_FILES)
    files.add(state_filename)

    current_hash = _compute_module_hash(root, directories, files, state_filename)
    state = _load_state(root, state_filename)

    current_version = _coerce_version(config_payload.get("version", "0.0.0"))

    if state is None:
        _save_state(root, current_hash, str(current_version), state_filename)
        return config_payload, False
    else:
        state_payload: Dict[str, Any] = dict(state)

    state_hash = state_payload.get("hash")
    if not isinstance(state_hash, str):
        _save_state(root, current_hash, str(current_version), state_filename)
        return config_payload, False

    if state_hash == current_hash:
        if state_payload.get("version") != str(current_version):
            _save_state(root, current_hash, str(current_version), state_filename)
        return config_payload, False

    pending_metadata = _load_pending_changelog(root, pending_changelog_filename)
    merged_metadata = _merge_changelog_metadata(pending_metadata, changelog_metadata)
    effective_description = _resolve_change_description(merged_metadata, change_description)

    baseline = _coerce_version(state_payload.get("version", str(current_version)))
    base_version = current_version if current_version > baseline else baseline
    bumped_version = _bump_patch(base_version)

    _apply_version_update(root, bumped_version, effective_description, merged_metadata)

    refreshed_hash = _compute_module_hash(root, directories, files, state_filename)
    _save_state(root, refreshed_hash, bumped_version, state_filename)

    if pending_metadata and pending_changelog_filename and clear_pending_changelog:
        pending_path = root / pending_changelog_filename
        if pending_path.exists():
            pending_path.unlink()

    updated_config = _load_config(root)
    return updated_config, True


def _compute_module_hash(
    module_root: Path,
    excluded_dirs: Iterable[str],
    excluded_files: Iterable[str],
    state_filename: str,
) -> str:
    hasher = sha256()
    excluded_dir_set = {str(name) for name in excluded_dirs}
    excluded_files_set = {str(name) for name in excluded_files}

    for path in sorted(module_root.rglob("*"), key=lambda p: p.relative_to(module_root).as_posix()):
        if not path.is_file():
            continue

        relative = path.relative_to(module_root)
        if any(part in excluded_dir_set for part in relative.parts):
            continue
        if path.name in excluded_files_set or path.name == state_filename:
            continue

        if path.name == "module.yaml":
            text = path.read_text(encoding="utf-8")
            normalized = re.sub(
                r"^version:\s*.*$",
                "version: 0.0.0",
                text,
                count=1,
                flags=re.MULTILINE,
            )
            hasher.update(normalized.encode("utf-8"))
        else:
            # Read text files with UTF-8 and normalize line endings to LF so that
            # hashing is stable across platforms (CRLF on Windows vs LF on Linux).
            # If the file is not valid UTF-8 (binary), fall back to raw bytes.
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                hasher.update(path.read_bytes())
            else:
                normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
                hasher.update(normalized_text.encode("utf-8"))

    return hasher.hexdigest()


def _load_state(module_root: Path, state_filename: str) -> Optional[Dict[str, Any]]:
    state_path = module_root / state_filename
    if not state_path.exists():
        return None
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return cast(Dict[str, Any], payload)


def _save_state(module_root: Path, content_hash: str, version: str, state_filename: str) -> None:
    state_path = module_root / state_filename
    payload = {"hash": content_hash, "version": version}
    state_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _bump_patch(version: Version) -> str:
    components: list[int] = list(version.release)
    while len(components) < _MIN_VERSION_COMPONENTS:
        components.append(0)
    components[2] += 1
    return "{}".format(".".join(str(part) for part in components))


def _apply_version_update(
    module_root: Path,
    new_version: str,
    description: str,
    metadata: Optional[Mapping[str, Any]],
) -> None:
    module_yaml = module_root / "module.yaml"
    text = module_yaml.read_text(encoding="utf-8")

    text, replaced = re.subn(
        r"^version:\s*.*$",
        f"version: {new_version}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if replaced == 0:
        raise RuntimeError("Failed to locate version field in module.yaml")

    # Changelog policy:
    # - Keep only a single stub entry in module.yaml (points to docs/changelog.md)
    # - Write full history to docs/changelog.md
    _append_to_markdown_changelog(module_root, new_version, description, metadata)
    text = _ensure_module_yaml_changelog_stub(text, new_version)

    module_yaml.write_text(text, encoding="utf-8")


def _ensure_module_yaml_changelog_stub(module_yaml_text: str, version: str) -> str:
    """Replace the top-level `changelog:` block with a single stub entry.

    We intentionally avoid YAML dumping here to preserve anchors/formatting.
    """

    stub = (
        "changelog:\n"
        f'  - version: "{version}"\n'
        f'    date: "{date.today().isoformat()}"\n'
        '    notes: "See docs/changelog.md"\n'
    )

    pattern = re.compile(
        r"^changelog:\n(?P<body>(?:^[ \t].*\n|^\n)*)",
        flags=re.MULTILINE,
    )
    if pattern.search(module_yaml_text):
        updated = pattern.sub(stub, module_yaml_text, count=1)
    else:
        # If the module has no changelog section, append one at the end.
        if not module_yaml_text.endswith("\n"):
            module_yaml_text += "\n"
        updated = module_yaml_text.rstrip() + "\n" + stub

    # Clean up orphaned top-level entries like:
    # - version: 0.1.0
    #   date: ...
    #   ...
    # These were produced by earlier buggy append logic and break YAML parsing.
    updated = re.sub(
        r"(?m)^-\s+version:.*(?:\n^[ \t].*)*\n?",
        "",
        updated,
    )

    return updated


def _append_to_markdown_changelog(
    module_root: Path,
    version: str,
    description: str,
    metadata: Optional[Mapping[str, Any]],
) -> None:
    changelog_path = module_root / "docs" / "changelog.md"
    entry = _prepare_changelog_entry(version, description, metadata)
    section = _render_markdown_changelog_section(entry)

    if not changelog_path.exists():
        title = f"# Changelog — {module_root.as_posix()}\n\n"
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        changelog_path.write_text(title + section, encoding="utf-8")
        return

    existing = changelog_path.read_text(encoding="utf-8")
    if re.search(rf"^##\s+{re.escape(version)}\b", existing, flags=re.MULTILINE):
        return

    changelog_path.write_text(_insert_markdown_section(existing, section), encoding="utf-8")


def _render_markdown_changelog_section(entry: Mapping[str, Any]) -> str:
    version = str(entry.get("version", ""))
    entry_date = str(entry.get("date", ""))
    summary = ""

    # Prefer a human summary if present; otherwise fall back to the first change description.
    raw_changes = entry.get("changes")
    if isinstance(raw_changes, list) and raw_changes:
        first = raw_changes[0]
        if isinstance(first, Mapping):
            summary = str(first.get("description") or "")
    if not summary:
        summary = "Update"

    lines: list[str] = [f"## {version} — {summary} ({entry_date})", ""]

    changes = entry.get("changes")
    if isinstance(changes, list) and changes:
        for change in changes:
            if isinstance(change, Mapping):
                ctype = str(change.get("type", "chore"))
                desc = str(change.get("description", ""))
                change_extras: list[str] = []
                for key, value in change.items():
                    if key in {"type", "description"}:
                        continue
                    if value is None:
                        continue
                    change_extras.append(f"{key}={value}")
                suffix = f" ({', '.join(change_extras)})" if change_extras else ""
                lines.append(f"- {ctype}: {desc}{suffix}" if desc else f"- {ctype}{suffix}")
            else:
                lines.append(f"- {str(change)}")
    else:
        lines.append(f"- {summary}")

    breaking = entry.get("breaking_changes")
    if isinstance(breaking, list) and breaking:
        lines.append("- Breaking changes:")
        for item in breaking:
            lines.append(f"  - {str(item)}")

    deprecations = entry.get("deprecations")
    if isinstance(deprecations, list) and deprecations:
        lines.append("- Deprecations:")
        for item in deprecations:
            lines.append(f"  - {str(item)}")

    notes = entry.get("notes")
    if isinstance(notes, str) and notes.strip():
        lines.append(f"- Notes: {notes.strip()}")

    # Render any extra entry-level metadata for traceability.
    reserved = {"version", "date", "changes", "breaking_changes", "deprecations", "notes"}
    extras: list[str] = []
    for key, value in entry.items():
        if key in reserved or value is None:
            continue
        if isinstance(value, Mapping):
            flat = ", ".join(f"{k}={v}" for k, v in value.items())
            extras.append(f"{key}: {flat}" if flat else f"{key}: <empty>")
        else:
            extras.append(f"{key}: {value}")
    if extras:
        lines.append(f"- Metadata: {'; '.join(extras)}")

    lines.append("")
    return "\n".join(lines)


def _insert_markdown_section(existing: str, section: str) -> str:
    # Insert directly after the first H1 (or at top if none).
    lines = existing.splitlines(keepends=True)
    if not lines:
        return section

    if lines[0].lstrip().startswith("# "):
        insert_at = 1
        # Keep a single blank line after title.
        if insert_at < len(lines) and lines[insert_at].strip() != "":
            lines.insert(insert_at, "\n")
            insert_at += 1
        elif insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        return "".join(lines[:insert_at]) + section + "".join(lines[insert_at:])

    return section + ("\n" if not section.endswith("\n") else "") + existing


def _load_pending_changelog(module_root: Path, filename: Optional[str]) -> Optional[Dict[str, Any]]:
    if not filename:
        return None

    pending_path = module_root / filename
    if not pending_path.exists():
        return None

    try:
        payload = yaml.safe_load(pending_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None

    result: Optional[Dict[str, Any]] = None
    if isinstance(payload, Mapping):
        result = dict(payload)
    elif isinstance(payload, list):
        result = {"changes": list(payload)}
    elif isinstance(payload, str):
        result = {"description": payload}

    return result


def _merge_changelog_metadata(
    pending: Optional[Mapping[str, Any]],
    inline: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    list_keys = {"changes", "breaking_changes", "deprecations"}

    for source in (pending, inline):
        if not source:
            continue
        for key, value in source.items():
            if value is None:
                continue
            if key in list_keys:
                existing = _to_list(merged.get(key))
                merged[key] = existing + _to_list(value)
            else:
                merged[key] = value

    return merged


def _resolve_change_description(metadata: Dict[str, Any], fallback: str) -> str:
    raw = metadata.pop("description", None) if metadata else None
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return fallback


def _prepare_changelog_entry(
    version: str,
    description: str,
    metadata: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "version": version,
        "date": date.today().isoformat(),
    }

    metadata_payload = dict(metadata) if metadata else {}

    entry["changes"] = _normalize_changes(
        description,
        metadata_payload.get("changes"),
    )
    entry["breaking_changes"] = _normalize_string_sequence(metadata_payload.get("breaking_changes"))
    entry["deprecations"] = _normalize_string_sequence(metadata_payload.get("deprecations"))

    reserved = {"changes", "breaking_changes", "deprecations"}
    for key, value in metadata_payload.items():
        if key in reserved or value is None:
            continue
        entry[key] = value

    return entry


def _normalize_changes(
    default_description: str,
    raw_changes: Any,
) -> list[Dict[str, Any]]:
    normalized: list[Dict[str, Any]] = []

    for item in _to_list(raw_changes):
        if isinstance(item, Mapping):
            change_entry: Dict[str, Any] = {
                "type": str(item.get("type", "chore")),
                "description": str(item.get("description", default_description)),
            }
            for key, value in item.items():
                if key in {"type", "description"}:
                    continue
                change_entry[key] = value
            normalized.append(change_entry)
        elif item is not None:
            normalized.append(
                {
                    "type": "chore",
                    "description": str(item),
                }
            )

    if not normalized:
        normalized.append(
            {
                "type": "chore",
                "description": default_description,
            }
        )

    return normalized


def _normalize_string_sequence(value: Any) -> list[str]:
    result: list[str] = []
    for item in _to_list(value):
        if item is None:
            continue
        result.append(str(item))
    return result


def _to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _build_changelog_entry(
    version: str,
    description: str,
    metadata: Optional[Mapping[str, Any]],
) -> str:
    entry = _prepare_changelog_entry(version, description, metadata)

    lines = [
        f'  - version: "{entry["version"]}"',
        f'    date: "{entry["date"]}"',
        "    changes:",
    ]

    for change in entry["changes"]:
        lines.append(f'      - type: {_format_scalar(change.get("type", "chore"))}')
        lines.append(
            f'        description: {_format_scalar(change.get("description", description))}'
        )
        for key, value in change.items():
            if key in {"type", "description"}:
                continue
            lines.extend(_render_key_value(key, value, 8))

    lines.extend(_render_sequence("breaking_changes", entry["breaking_changes"], 4))
    lines.extend(_render_sequence("deprecations", entry["deprecations"], 4))

    for key, value in entry.items():
        if key in {"version", "date", "changes", "breaking_changes", "deprecations"}:
            continue
        lines.extend(_render_key_value(key, value, 4))

    lines.append("")
    return "\n".join(lines)


def _render_key_value(key: str, value: Any, indent: int) -> list[str]:
    prefix = " " * indent
    if isinstance(value, Mapping):
        lines = [f"{prefix}{key}:"]
        for sub_key, sub_value in value.items():
            lines.extend(_render_key_value(str(sub_key), sub_value, indent + 2))
        return lines
    if isinstance(value, list):
        return _render_sequence(key, value, indent)
    return [f"{prefix}{key}: {_format_scalar(value)}"]


def _render_sequence(key: str, items: Iterable[Any], indent: int) -> list[str]:
    prefix = " " * indent
    items_list = list(items)
    if key and not items_list:
        return [f"{prefix}{key}: []"]

    lines = [f"{prefix}{key}:"] if key else [f"{prefix}-"]
    if not items_list:
        return lines

    for item in items_list:
        if isinstance(item, Mapping):
            lines.append(" " * (indent + 2) + "-")
            for sub_key, sub_value in item.items():
                lines.extend(_render_key_value(str(sub_key), sub_value, indent + 4))
        else:
            lines.append(" " * (indent + 2) + f"- {_format_scalar(item)}")
    return lines


def _format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def _load_config(module_root: Path) -> Dict[str, Any]:
    config_path = module_root / "module.yaml"
    with config_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("module.yaml must resolve to a mapping")
    return cast(Dict[str, Any], data)


def _coerce_version(raw: Any) -> Version:
    try:
        return Version(str(raw))
    except (InvalidVersion, TypeError):
        return Version("0.0.0")
