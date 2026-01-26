#!/usr/bin/env python3
"""Utilities for synchronising and validating community-facing documentation."""
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    import yaml  # type: ignore[import]
except ImportError as exc:  # pragma: no cover - dependency guard
    raise SystemExit(
        "❌ PyYAML is required to manage community docs. Install it and retry."
    ) from exc

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_MAP_PATH = REPO_ROOT / "docs" / "docs_map.yml"
TEMPLATE_PATH = REPO_ROOT / "docs" / "community" / "README.template.md"
ROOT_README_PATH = REPO_ROOT / "README.md"
DEFAULT_RENDER_PATH = REPO_ROOT / "build" / "community" / "README.md"

COMMUNITY_STAGING_TOKEN = "community" + "-staging"

BANNED_TOKENS: Dict[str, str] = {
    "fastapi.minimal": "Use the fastapi.standard kit in community documentation.",
    "pip install -e .": "Community docs should point to poetry install instead of editable installs.",
    "pip install -r": "Generated projects rely on Poetry; avoid pip install -r instructions.",
    COMMUNITY_STAGING_TOKEN: "Staging markers must not reach the community distribution.",
}


def load_docs_map() -> Dict[str, Sequence[str]]:
    try:
        data = yaml.safe_load(DOCS_MAP_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"❌ docs_map.yml not found at {DOCS_MAP_PATH}") from exc
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"❌ Failed to parse docs_map.yml: {exc}") from exc

    mapping = data.get("docs_map", {})
    if not isinstance(mapping, dict):  # pragma: no cover - defensive
        raise SystemExit("❌ docs_map.yml must contain a mapping under 'docs_map'")
    return mapping


def resolve_pattern(pattern: str) -> List[Path]:
    """Expand a docs_map pattern into concrete file paths."""
    normalized = pattern.replace("\\", "/")
    results: List[Path] = []

    # Directory match (pattern ending with a slash)
    if normalized.endswith("/"):
        dir_path = (REPO_ROOT / normalized.rstrip("/")).resolve()
        if dir_path.is_dir():
            results.extend(p for p in dir_path.rglob("*") if p.is_file())
        return results

    # Wildcard pattern
    if any(token in normalized for token in "*?[]"):
        for root, _dirs, files in os.walk(REPO_ROOT):
            for filename in files:
                rel_path = Path(os.path.join(root, filename)).relative_to(REPO_ROOT)
                if fnmatch.fnmatch(rel_path.as_posix(), normalized):
                    results.append(REPO_ROOT / rel_path)
        return results

    # Direct file path
    candidate = (REPO_ROOT / normalized).resolve()
    if candidate.exists():
        results.append(candidate)
    else:
        # Keep the original path so callers can surface a helpful error later.
        results.append(REPO_ROOT / normalized)
    return results


def gather_community_docs() -> List[Path]:
    mapping = load_docs_map()
    files: List[Path] = []

    for pattern, tiers in mapping.items():
        if not isinstance(tiers, Sequence):  # pragma: no cover - defensive
            continue
        if "community" not in tiers:
            continue
        files.extend(resolve_pattern(pattern))

    # Deduplicate while preserving missing paths for helpful warnings
    unique_paths: List[Path] = []
    seen = set()
    for path in sorted(files, key=lambda p: p.as_posix()):
        absolute = path if path.is_absolute() else (REPO_ROOT / path).resolve()
        if absolute in seen:
            continue
        seen.add(absolute)
        unique_paths.append(absolute)
    return unique_paths


def check_banned_tokens(files: Iterable[Path]) -> Tuple[bool, List[str]]:
    violations: List[str] = []
    ok = True
    for file_path in files:
        if not file_path.exists():
            violations.append(
                f"⚠️ Missing expected community doc: {file_path.relative_to(REPO_ROOT)}"
            )
            ok = False
            continue

        text = file_path.read_text(encoding="utf-8")
        for token, guidance in BANNED_TOKENS.items():
            if token in text:
                rel = file_path.relative_to(REPO_ROOT)
                violations.append(f"❌ {rel}: remove '{token}'. {guidance}")
                ok = False
    return ok, violations


def transform_template_for_root(template: str) -> str:
    content = template.replace("../../docs/", "docs/")
    content = content.replace("# RapidKit Community", "# RapidKit", 1)
    content = content.replace(
        "RapidKit Community ships under the [MIT License](LICENSE)",
        "RapidKit is distributed under the [MIT License](LICENSE)",
    )
    return content


def render_community_readme(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(TEMPLATE_PATH.read_text(encoding="utf-8"), encoding="utf-8")


def sync_root_readme() -> None:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    ROOT_README_PATH.write_text(transform_template_for_root(template), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sync-root", action="store_true", help="Regenerate README.md from the community template"
    )
    parser.add_argument(
        "--render-community",
        type=Path,
        nargs="?",
        const=DEFAULT_RENDER_PATH,
        help="Render the community README template to the given path (default: build/community/README.md)",
    )
    parser.add_argument(
        "--check-keywords",
        action="store_true",
        help="Validate that community docs do not contain forbidden keywords",
    )

    args = parser.parse_args(argv)

    # Default behaviour: run keyword checks if no explicit action requested
    if not any([args.sync_root, args.render_community, args.check_keywords]):
        args.check_keywords = True

    if args.render_community:
        render_community_readme(args.render_community)
        print(f"📄 Rendered community README to {args.render_community.relative_to(REPO_ROOT)}")

    if args.sync_root:
        sync_root_readme()
        print("📝 Regenerated README.md from docs/community/README.template.md")

    if args.check_keywords:
        files = gather_community_docs()
        ok, violations = check_banned_tokens(files)
        for message in violations:
            print(message)
        if not ok:
            return 1
        print("✅ Community documentation passed keyword validation")

    return 0


if __name__ == "__main__":
    sys.exit(main())
