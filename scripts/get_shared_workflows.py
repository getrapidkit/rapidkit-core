#!/usr/bin/env python3
"""Emit newline separated workflows that should be shared for a given tier."""
from __future__ import annotations

import argparse
from pathlib import Path


def load_shared_workflows(config_path: Path, tier: str) -> list[str]:
    try:
        import yaml
    except ImportError:  # pragma: no cover - action runtime should have pyyaml
        return []

    if not config_path.exists():
        return []

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    workflows = data.get("shared_workflows", {})
    selected: list[str] = []

    for name, meta in workflows.items():
        tiers: list[str] | str | None = meta.get("tiers") if isinstance(meta, dict) else meta

        if tiers is None:
            selected.append(str(name))
            continue

        if isinstance(tiers, str):
            if tiers in {"all", "*"} or tiers == tier:
                selected.append(str(name))
            continue

        if isinstance(tiers, list):
            normalized = {str(item) for item in tiers}
            if "all" in normalized or "*" in normalized or tier in normalized:
                selected.append(str(name))

    # Preserve order while removing duplicates
    deduped: list[str] = []
    for item in selected:
        if item not in deduped:
            deduped.append(item)
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(description="Print shared workflows for a tier")
    parser.add_argument("config", type=Path)
    parser.add_argument("tier", type=str)
    args = parser.parse_args()

    for workflow in load_shared_workflows(args.config, args.tier):
        print(workflow)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
