"""Migrate module generation outputs into src/modules/<slug>/ layout.

Usage:
    python scripts/migrate_modules_to_src_modules.py [--apply] [--module SLUG]

- Default is dry-run: prints planned rewrites without touching files.
- SLUG is the module slug relative to the modules root (e.g. free/communication/email).

The script rewrites generation.variants.*.files[].output paths that currently
start with `src/` to the new layout `src/modules/<slug>/...`. Paths outside `src/`
are left untouched. Vendor paths are not modified. Tests under `tests/` are
kept as-is for now to avoid breaking discovery.

This is the first step in the migration; template imports and auto-mount logic
still need coordinated changes. Run with --apply only after reviewing dry-run output.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Tuple

MODULES_ROOT = Path(__file__).resolve().parent.parent / "src" / "modules"


def iter_module_manifests(modules_root: Path) -> Iterable[Tuple[str, Path]]:
    for manifest in modules_root.rglob("module.yaml"):
        if not manifest.is_file():
            continue
        try:
            slug = manifest.parent.relative_to(modules_root).as_posix()
        except ValueError:
            continue
        yield slug, manifest


def rewrite_output_path(slug: str, path: str) -> str:
    """Return rewritten output path; leave untouched if not under src/."""
    prefix = "src/"
    if not path.startswith(prefix):
        return path

    already_under_modules = path.startswith("src/modules/")
    if already_under_modules:
        # Avoid nesting when a previous run (or partial migration) already rewrote the path
        return path

    remainder = path[len(prefix) :]

    # Avoid double-nesting when the first segment matches slug leaf or its parent category
    slug_parts = slug.split("/")
    slug_leaf = slug_parts[-1]
    slug_parent = slug_parts[-2] if len(slug_parts) > 1 else None
    parts = remainder.split("/")
    if parts and parts[0] in {slug_leaf, slug_parent}:
        remainder = "/".join(parts[1:]) or slug_leaf

    return f"src/modules/{slug}/{remainder}"


def process_manifest_text(slug: str, manifest_path: Path) -> Tuple[List[Tuple[str, str]], str]:
    """Rewrite output paths line-by-line to preserve anchors/formatting."""

    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    changes: List[Tuple[str, str]] = []

    def rewrite_line(line: str) -> str:
        prefix = "output:"
        if prefix not in line:
            return line
        # naive split preserving indentation
        try:
            before, after = line.split(prefix, 1)
        except ValueError:
            return line
        value = after.strip()
        if not value.startswith("src/"):
            return line
        new_value = rewrite_output_path(slug, value)
        if new_value == value:
            return line
        changes.append((value, new_value))
        return f"{before}{prefix} {new_value}"

    new_lines = [rewrite_line(line) for line in lines]
    new_text = "\n".join(new_lines) + ("\n" if lines and not lines[-1].endswith("\n") else "")
    return changes, new_text


def apply_changes(manifest_path: Path, new_text: str) -> None:
    manifest_path.write_text(new_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write changes instead of dry-run")
    parser.add_argument(
        "--module", dest="module", help="Module slug to limit (e.g. free/communication/email)"
    )
    parser.add_argument(
        "--modules-root",
        dest="modules_root",
        default=str(MODULES_ROOT),
        help="Path to modules root (default: ./src/modules)",
    )
    args = parser.parse_args()

    modules_root = Path(args.modules_root).resolve()
    if not modules_root.exists():
        raise SystemExit(f"Modules root not found: {modules_root}")

    targets = list(iter_module_manifests(modules_root))
    if args.module:
        targets = [(slug, path) for slug, path in targets if slug == args.module]
        if not targets:
            raise SystemExit(f"Module slug not found: {args.module}")

    total_changes = 0
    for slug, manifest_path in targets:
        changes, new_text = process_manifest_text(slug, manifest_path)
        if not changes:
            continue
        total_changes += len(changes)
        print(f"\n[{slug}] {manifest_path}")
        for old, new in changes:
            print(f"  src -> {old}\n         {new}")
        if args.apply:
            apply_changes(manifest_path, new_text)
            print("  ✅ applied")
        else:
            print("  (dry-run)")

    if total_changes == 0:
        print("No output paths needed rewriting.")
    elif not args.apply:
        print("\nDry-run complete. Re-run with --apply to persist changes.")


if __name__ == "__main__":
    main()
