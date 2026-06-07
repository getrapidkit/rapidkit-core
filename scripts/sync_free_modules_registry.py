#!/usr/bin/env python3
"""Synchronize the free modules registry from per-module manifests.

The per-module ``module.yaml`` files are the source of truth. This helper keeps
``src/modules/free/modules.yaml`` useful for legacy registry consumers without
letting it drift from the real module catalog.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FREE_ROOT = PROJECT_ROOT / "src" / "modules" / "free"
REGISTRY_PATH = FREE_ROOT / "modules.yaml"


CATEGORY_METADATA: dict[str, dict[str, Any]] = {
    "ai": {
        "name": "AI Modules",
        "description": "AI assistants, agents, RAG, and model infrastructure",
        "color": "indigo",
        "priority": 1,
    },
    "auth": {
        "name": "Authentication Modules",
        "description": "Authentication, sessions, API keys, and identity flows",
        "color": "blue",
        "priority": 2,
    },
    "users": {
        "name": "User Modules",
        "description": "User domain services, profiles, and account metadata",
        "color": "green",
        "priority": 3,
    },
    "security": {
        "name": "Security Modules",
        "description": "HTTP security, policy, audit, and abuse prevention",
        "color": "red",
        "priority": 4,
    },
    "database": {
        "name": "Database Modules",
        "description": "Database integrations and persistence adapters",
        "color": "purple",
        "priority": 5,
    },
    "cache": {
        "name": "Cache Modules",
        "description": "Caching and shared state infrastructure",
        "color": "orange",
        "priority": 6,
    },
    "billing": {
        "name": "Billing Modules",
        "description": "Payments, cart, inventory, and usage monetization",
        "color": "pink",
        "priority": 7,
    },
    "business": {
        "name": "Business Modules",
        "description": "SaaS, tenancy, storage, flags, and product operations",
        "color": "teal",
        "priority": 8,
    },
    "communication": {
        "name": "Communication Modules",
        "description": "Email, notifications, webhooks, and delivery channels",
        "color": "cyan",
        "priority": 9,
    },
    "tasks": {
        "name": "Task Modules",
        "description": "Background jobs, queues, schedulers, and workflows",
        "color": "magenta",
        "priority": 10,
    },
    "observability": {
        "name": "Observability Modules",
        "description": "Metrics, tracing, health checks, and diagnostics",
        "color": "yellow",
        "priority": 11,
    },
    "essentials": {
        "name": "Essential Modules",
        "description": "Core settings, logging, deployment, and middleware",
        "color": "gray",
        "priority": 12,
    },
}


PRIORITIES: dict[str, dict[str, Any]] = {
    "essential": {
        "name": "Essential",
        "description": "Required for basic application functionality",
        "install_by_default": True,
        "auto_install": True,
    },
    "recommended": {
        "name": "Recommended",
        "description": "Recommended for production applications",
        "install_by_default": False,
        "auto_install": False,
    },
    "optional": {
        "name": "Optional",
        "description": "Optional features based on product needs",
        "install_by_default": False,
        "auto_install": False,
    },
}


ESSENTIAL_MODULES = {
    "settings",
    "logging",
    "deployment",
    "security_headers",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Expected mapping in {path}")
    return data


def _module_priority(manifest: dict[str, Any]) -> str:
    name = str(manifest.get("name", ""))
    category = str(manifest.get("category", ""))
    if name in ESSENTIAL_MODULES:
        return "essential"
    if category in {"ai", "auth", "billing", "business", "database", "security", "tasks"}:
        return "recommended"
    return "optional"


def _templates_path(module_yaml: Path, manifest: dict[str, Any]) -> str:
    rel_dir = module_yaml.parent.relative_to(FREE_ROOT).as_posix()
    manifest_category = str(manifest.get("category", "")).strip("/")
    manifest_name = str(manifest.get("name", "")).strip("/")
    if manifest_category and manifest_name:
        expected = f"{manifest_category}/{manifest_name}"
        if rel_dir != expected:
            return rel_dir
    return rel_dir


def _kit_support(manifest: dict[str, Any]) -> dict[str, str]:
    variants = manifest.get("generation", {}).get("variants", {}) or {}
    profile_inherits = manifest.get("profile_inherits", {}) or {}
    support: dict[str, str] = {}
    if "fastapi" in variants or "fastapi" in profile_inherits:
        support["fastapi.standard"] = "supported"
        support["fastapi.ddd"] = "supported"
    if "nestjs" in variants or "nestjs" in profile_inherits:
        support["nestjs.standard"] = "supported"
    return support


def _registry_module(module_yaml: Path) -> tuple[str, dict[str, Any], dict[str, str]]:
    manifest = _load_yaml(module_yaml)
    name = str(manifest.get("name") or module_yaml.parent.name)
    entry: dict[str, Any] = OrderedDict()
    entry["name"] = name
    entry["display_name"] = manifest.get("display_name", name.replace("_", " ").title())
    entry["version"] = str(manifest.get("version", "0.1.0"))
    entry["access"] = "free"
    entry["tier"] = "free"
    entry["status"] = manifest.get("status", "stable")
    entry["description"] = manifest.get("description", "")
    entry["tags"] = manifest.get("tags", [])
    entry["category"] = manifest.get("category", module_yaml.parent.parent.name)
    entry["priority"] = _module_priority(manifest)
    entry["dependencies"] = manifest.get("depends_on", [])
    entry["capabilities"] = manifest.get("capabilities", [])
    entry["templates_path"] = _templates_path(module_yaml, manifest)
    entry["config_sources"] = manifest.get("config_sources", [])
    entry["compatibility"] = manifest.get("compatibility", {})
    entry["testing"] = manifest.get("testing", {})
    entry["documentation"] = manifest.get("documentation", {})
    entry["support"] = manifest.get("support", {})
    entry["changelog"] = manifest.get("changelog", [])
    entry["validation"] = manifest.get("validation", {})
    entry["rollback"] = manifest.get("rollback", {})
    entry["performance"] = manifest.get("performance", {})
    return name, dict(entry), _kit_support(manifest)


def build_registry() -> dict[str, Any]:
    modules: dict[str, dict[str, Any]] = OrderedDict()
    kit_support: dict[str, dict[str, str]] = OrderedDict()

    for module_yaml in sorted(FREE_ROOT.rglob("module.yaml")):
        name, entry, support = _registry_module(module_yaml)
        if name in modules:
            raise ValueError(f"Duplicate free module name: {name}")
        modules[name] = entry
        kit_support[name] = support

    categories: dict[str, dict[str, Any]] = OrderedDict()
    for category in sorted({entry["category"] for entry in modules.values()}):
        metadata = dict(CATEGORY_METADATA.get(category, {}))
        metadata.setdefault("name", f"{category.replace('_', ' ').title()} Modules")
        metadata.setdefault("description", f"{category.replace('_', ' ').title()} modules")
        metadata.setdefault("color", "gray")
        metadata.setdefault("priority", 99)
        metadata["module_count"] = sum(
            1 for entry in modules.values() if entry["category"] == category
        )
        metadata["essential_count"] = sum(
            1
            for entry in modules.values()
            if entry["category"] == category and entry["priority"] == "essential"
        )
        categories[category] = metadata

    return {
        "modules": dict(modules),
        "categories": dict(categories),
        "priorities": PRIORITIES,
        "global_config": {
            "version": "2.0.0",
            "last_updated": "2026-05-31",
            "maintainer": "RapidKit Team",
            "repository": "https://github.com/rapidkitlabs/rapidkit-core",
            "documentation": "https://docs.rapidkit.top",
            "source_of_truth": "src/modules/free/**/module.yaml",
            "compatibility": {
                "python_versions": ["3.9", "3.10", "3.11", "3.12"],
                "node_versions": [">=18"],
                "frameworks": ["fastapi", "nestjs"],
                "operating_systems": ["linux", "darwin", "windows"],
            },
        },
        "kit_support": dict(kit_support),
    }


def render_registry(registry: dict[str, Any]) -> str:
    rendered = yaml.safe_dump(registry, sort_keys=False, allow_unicode=False, width=100)
    header = (
        "# Free Modules Registry\n"
        "# Generated by scripts/sync_free_modules_registry.py.\n"
        "# Source of truth: each module's module.yaml manifest.\n\n"
    )
    return header + rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when src/modules/free/modules.yaml is not in sync",
    )
    args = parser.parse_args()

    registry = build_registry()
    rendered = render_registry(registry)
    if args.check:
        current = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
        if current != rendered:
            print(f"{REGISTRY_PATH} is not synchronized")
            return 1
        print(f"{REGISTRY_PATH} is synchronized")
        return 0

    REGISTRY_PATH.write_text(rendered, encoding="utf-8")
    print(f"Synced {len(registry['modules'])} free modules into {REGISTRY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
