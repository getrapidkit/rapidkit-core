import re
from pathlib import Path
from typing import List, Tuple

INJECT_PATTERN = re.compile(r"#\s*<<<inject:[^>]+>>>")


def _should_process_file(path: Path) -> bool:
    text_extensions = {".py", ".md", ".toml", ".yaml", ".yml", ".env", ".ini", ".cfg"}
    if path.suffix in text_extensions:
        return True
    # handle files like .env.dev, .env.prod
    if path.name.startswith(".env"):
        return True
    return False


def remove_inject_markers(
    project_root: Path, dry_run: bool = True
) -> Tuple[List[Path], List[Path]]:
    """Scan project files under project_root and remove inject marker lines.

    Returns (modified_files, skipped_files).
    - Removes whole line when the line contains only an inject marker.
    - If the inject marker is inline with other code, it strips the marker substring.
    """
    modified = []
    skipped = []
    for p in project_root.rglob("*"):
        if not p.is_file():
            continue
        if not _should_process_file(p):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            skipped.append(p)
            continue

        changed = False
        out_lines = []
        for raw in text.splitlines():
            line = raw.rstrip("\n")
            if INJECT_PATTERN.fullmatch(line.strip()):
                # line is only an inject marker -> drop it
                changed = True
                continue
            if INJECT_PATTERN.search(line):
                # marker inline with code -> remove only the marker substring
                new_line = INJECT_PATTERN.sub("", line)
                if new_line != line:
                    changed = True
                out_lines.append(new_line)
            else:
                out_lines.append(line)

        if changed:
            modified.append(p)
            if not dry_run:
                # write back trimming trailing newlines to match original style
                p.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    return modified, skipped
