import re
from collections import defaultdict
from pathlib import Path


def organize_imports(filepath: Path) -> None:
    """
    Safe import organizer for simple cases only:
    - Operates only on top-level, single-line import statements.
    - Skips files that use multiline imports (parentheses or backslashes) or indented imports.
    - Merges duplicate "from X import a, b" and de-duplicates plain imports.
    - Rewrites import section at the top, preserving the rest of the file.

    If any complex pattern is detected, the function exits without modifying the file.
    """
    content = filepath.read_text(encoding="utf-8")

    # Bail out on complex patterns to avoid corruption
    if re.search(r"^\s*from\s+\S+\s+import\s*\(", content, re.M):
        return
    if re.search(r"\\\s*$", content, re.M):  # line continuation
        return

    lines = content.splitlines()
    other_lines = []
    shebang_lines = []

    # Only match top-level imports (no leading whitespace)
    from_import_pattern = re.compile(r"^from\s+(\S+)\s+import\s+(.+)")
    plain_import_pattern = re.compile(r"^import\s+(.+)")
    shebang_pattern = re.compile(r"^#!|^#.*coding[:=]")

    # Collect and group imports
    from_imports = defaultdict(set)
    plain_imports = set()

    for line in lines:
        if shebang_pattern.match(line):
            shebang_lines.append(line)
            continue
        fm = from_import_pattern.match(line)
        if fm:
            module = fm.group(1)
            symbols_part = (fm.group(2) or "").strip()
            # Reject if appears to be multiline start or contains parentheses
            if symbols_part.startswith("(") or ")" in symbols_part:
                # Complex import, abort organizing entirely
                return
            symbols = [s.strip() for s in symbols_part.split(",") if s.strip()]
            for symbol in symbols:
                from_imports[module].add(symbol)
            continue
        im = plain_import_pattern.match(line)
        if im:
            # Keep the original line for plain imports to preserve aliases
            plain_imports.add(line.strip())
        else:
            other_lines.append(line)

    # If no imports collected, do nothing
    if not from_imports and not plain_imports:
        return

    # Build unique, sorted import lines
    merged_imports = []
    for module in sorted(from_imports):
        symbols = sorted(from_imports[module])
        merged_imports.append(f"from {module} import {', '.join(symbols)}")
    merged_imports.extend(sorted(plain_imports))

    # Remove leading blank lines from other_lines
    while other_lines and other_lines[0].strip() == "":
        other_lines.pop(0)

    # Reconstruct the file
    new_content = []
    if shebang_lines:
        new_content.extend(shebang_lines)
    if merged_imports:
        if new_content:
            new_content.append("")  # Blank line after shebang/encoding
        new_content.extend(merged_imports)
        new_content.append("")  # Blank line after imports
    new_content.extend(other_lines)

    filepath.write_text("\n".join(new_content) + "\n", encoding="utf-8")
