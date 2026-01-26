"""Utilities to normalize Poetry dependencies.

Features:
 - Move known dev-only tools from main [tool.poetry.dependencies] to
   [tool.poetry.group.dev.dependencies].
 - Create dev group section if missing.
 - Deduplicate entries (dev tools only appear once, in dev group).
 - Preserve ordering of non-dev dependencies and keep comments intact where possible.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Tuple

DEV_TOOL_NAMES = {
    "black",
    "flake8",
    "pytest",
    "pytest-asyncio",
    "isort",
    "mypy",
    "ruff",
    "coverage",
    "pre-commit",
}


SECTION_PATTERN = re.compile(r"^\[(?P<header>[^\]]+)\]", re.MULTILINE)


def _split_sections(content: str) -> Dict[str, Tuple[str, int, int]]:
    """Return mapping of section header -> (body, start_index, end_index)."""
    matches = list(SECTION_PATTERN.finditer(content))
    sections = {}
    for idx, m in enumerate(matches):
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        header = m.group("header")
        sections[header] = (content[start:end], m.start(), end)
    return sections


def _strip_inline_comment(value: str) -> str:
    """Strip an inline # comment that is not inside quotes."""
    in_s = False
    in_d = False
    for i, ch in enumerate(value):
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif ch == "#" and not in_s and not in_d:
            return value[:i].rstrip()
    return value.strip()


def _parse_key_value_lines(body: str) -> Dict[str, str]:
    """Parse simple key = value lines from a TOML section, keeping raw value tokens.

    We don't attempt full TOML parsing—just enough for flat dependency specs while
    preserving dict-style tables and version strings. Inline comments are removed.
    """
    deps: Dict[str, str] = {}
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or " " in key:
            continue
        value = _strip_inline_comment(value.strip())
        deps[key] = value
    return deps


def _rebuild_section(header: str, original_body: str, new_kv: Dict[str, str]) -> str:
    preserved_comments = [ln for ln in original_body.splitlines() if ln.strip().startswith("#")]
    lines = [f"[{header}]"]
    # Keep comments at top
    for c in preserved_comments:
        lines.append(c)
    # Align equals for readability
    if new_kv:
        max_len = max(len(k) for k in new_kv)
        for k in sorted(new_kv):
            spaces = " " * (max_len - len(k))
            lines.append(f"{k}{spaces} = {new_kv[k]}")
    lines.append("")
    return "\n".join(lines)


def normalize_poetry_dependencies(pyproject_path: Path) -> bool:
    """Normalize dependencies in a pyproject.toml file.

    Returns True if file updated.
    """
    if not pyproject_path.exists():
        return False
    content = pyproject_path.read_text(encoding="utf-8")
    sections = _split_sections(content)

    main_key = "tool.poetry.dependencies"
    dev_key = "tool.poetry.group.dev.dependencies"
    if main_key not in sections:
        return False

    main_body, main_start, main_end = sections[main_key]
    main_deps = _parse_key_value_lines(main_body)

    dev_body = ""
    dev_deps = {}
    dev_exists = dev_key in sections
    if dev_exists:
        dev_body, dev_start, dev_end = sections[dev_key]
        dev_deps = _parse_key_value_lines(dev_body)

    changed = False

    # Collect dev tools from main
    to_move = {k: v for k, v in main_deps.items() if k in DEV_TOOL_NAMES}
    if to_move:
        for k in to_move:
            main_deps.pop(k, None)
        # Merge into dev deps (prefer existing spec if already there)
        for k, v in to_move.items():
            if k not in dev_deps:
                dev_deps[k] = v
        changed = True

    if changed:
        # rebuild main section
        new_main = _rebuild_section(main_key, main_body, main_deps)
        if dev_exists:
            new_dev = _rebuild_section(dev_key, dev_body, dev_deps)
            # Replace both slices carefully (process later indices first)
            new_content = content[:main_start] + new_main + content[main_end:]
            # After replacement, indices shift; recompute sections minimally
            new_sections = _split_sections(new_content)
            dev_body2, dev_start2, dev_end2 = new_sections.get(dev_key, ("", 0, 0))
            new_content = new_content[:dev_start2] + new_dev + new_content[dev_end2:]
        else:
            # append dev section before build-system if exists else end
            dev_section = _rebuild_section(dev_key, "", dev_deps)
            build_match = re.search(r"^\[build-system\]", content, re.MULTILINE)
            if build_match:
                insert_at = build_match.start()
                new_content = (
                    content[:main_start]
                    + new_main
                    + content[main_end:insert_at]
                    + dev_section
                    + content[insert_at:]
                )
            else:
                new_content = content[:main_start] + new_main + content[main_end:] + dev_section
        if new_content != content:
            pyproject_path.write_text(new_content, encoding="utf-8")
            return True
    return False
