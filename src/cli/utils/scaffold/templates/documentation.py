"""Documentation template helpers for module scaffolding."""

from __future__ import annotations

import textwrap
from pathlib import Path
from string import Template
from typing import Dict, Mapping


def build_documentation_files(identifiers: Mapping[str, str]) -> Dict[Path, Template]:
    """Return repository-relative documentation files for the new module."""

    doc_parts = identifiers["doc_parts_list"].split("/") if identifiers["doc_parts_list"] else []
    doc_root = Path("docs", "modules", *doc_parts)

    return {
        doc_root / "README.md": Template(_docs_readme_template()),
        Path(identifiers["doc_overview_path"]): Template(_docs_overview_template()),
        Path(identifiers["doc_usage_path"]): Template(_docs_usage_template()),
        Path(identifiers["doc_api_reference_path"]): Template(_docs_api_reference_template()),
        Path(identifiers["doc_advanced_path"]): Template(_docs_advanced_template()),
        Path(identifiers["doc_changelog_path"]): Template(_docs_changelog_template()),
        Path(identifiers["doc_troubleshooting_path"]): Template(_docs_troubleshooting_template()),
        Path(identifiers["doc_migration_path"]): Template(_docs_migration_template()),
    }


def _docs_readme_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Module Docs

        This directory houses the living documentation set for the ${module_title_lower} module.
        Keep each guide lightweight, actionable, and in sync with the production implementation.

        | Document | Purpose |
        | -------- | ------- |
        | [Overview](overview.md) | Executive summary, capabilities, and architecture notes |
        | [Usage](usage.md) | CLI flows, configuration examples, and integration walkthroughs |
        | [API Reference](api-reference.md) | Public classes, functions, and environment variables |
        | [Advanced](advanced.md) | Extension patterns, override contracts, and operator playbooks |
        | [Changelog](changelog.md) | Release history, breaking changes, and operator notes |
        | [Troubleshooting](troubleshooting.md) | Common issues, diagnostics, and remediation steps |
        | [Migration](migration.md) | Upgrade checklists, compatibility notes, and rollback guidance |
        """
    ).strip()


def _docs_overview_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Overview

        ## Purpose
        Summarise why this module exists, which user journeys it accelerates, and the measurable
        outcomes it provides to product teams.

        ## Capabilities
        - Key runtime behaviours
        - Supported frameworks (FastAPI, NestJS)
        - Optional integrations or vendor touchpoints

        ## Architecture
        Describe the high-level flow from generator inputs to rendered outputs. Highlight how
        overrides, snippets, and framework plugins slot into the pipeline.
        """
    ).strip()


def _docs_usage_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Usage

        ## Quickstart
        ```bash
        rapidkit modules add ${module_name} --tier ${tier} --category ${category_path}
        python -m ${module_import_path}.generate fastapi ./tmp/${module_name}
        ```

        ## Configuration
        Document required config keys, defaults sourced from `config/base.yaml`, and any optional
        feature flags.

        ## Framework Examples
        Provide end-to-end examples for both FastAPI and NestJS, including health endpoints and
        dependency injection patterns.
        """
    ).strip()


def _docs_api_reference_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} API Reference

        ## Runtime Surface
        Detail the primary classes and functions emitted by the runtime templates. Include method
        signatures, expected inputs/outputs, and error semantics.

        ## Environment Variables
        | Variable | Description |
        | -------- | ----------- |
        | `RAPIDKIT_${module_name_upper}_EXAMPLE` | Placeholder flag toggling experimental behaviour |

        ## CLI Entrypoints
        Document generator commands and arguments exposed to consumers.
        """
    ).strip()


def _docs_advanced_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Advanced Guide

        Capture extension hooks, override strategies, and observability integrations. Reference
        concrete code snippets where possible and keep guidance aligned with production practices.
        """
    ).strip()


def _docs_troubleshooting_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Troubleshooting

        | Symptom | Diagnostic Steps | Resolution |
        | ------- | ---------------- | ---------- |
        | Example issue | `rapidkit modules doctor ${module_slug}` | Describe remediation |

        Encourage contributors to note log messages, health endpoints, and verification commands
        that speed up incident response.
        """
    ).strip()


def _docs_migration_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Migration Guide

        Track version bumps, breaking changes, and rollback strategies. Each release should include:
        - Impacted features or templates
        - Required operator actions
        - Compatibility notes with adjacent modules
        """
    ).strip()


def _docs_changelog_template() -> str:
    return textwrap.dedent(
        """
        # ${module_title} Changelog

        ## 0.1.0 — Initial baseline
        - Initial public baseline
        - See migration.md for upgrade steps
        """
    ).strip()


__all__ = ["build_documentation_files"]
