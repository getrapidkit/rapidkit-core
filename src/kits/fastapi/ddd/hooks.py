"""Lifecycle hooks for the FastAPI DDD kit."""

from __future__ import annotations

import getpass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from kits.shared import attempt_lockfile_generation, should_generate_lockfile


def pre_generate(variables: Dict[str, Any]) -> None:
    """Ensure common metadata defaults before generation."""
    variables.setdefault("author", getpass.getuser())
    variables.setdefault("app_version", "0.1.0")
    variables.setdefault(
        "description", "Domain-driven FastAPI service generated for Workspai with RapidKit Core"
    )
    variables.setdefault("year", str(datetime.now().year))


def post_generate(
    output_path: Optional[Path] = None, variables: Optional[Dict[str, Any]] = None
) -> None:
    """Display follow-up instructions once the scaffold is ready."""
    if not output_path:
        return

    project_name = (
        variables.get("project_name", "fastapi-ddd-service") if variables else "fastapi-ddd-service"
    )

    print("\n" + "=" * 60)
    print("🎉 FastAPI DDD project scaffolded!")
    print("=" * 60)

    if should_generate_lockfile(variables):
        attempt_lockfile_generation(
            output_path=output_path,
            command=["poetry", "lock"],
            label="poetry.lock",
        )
    print(f"📁 Project: {project_name}")
    print(f"📂 Location: {output_path}")
    print("\nNext steps:")
    print(f"  1. cd {project_name}")
    print("  2. source .rapidkit/activate  # loads the project-local RapidKit Core launcher")
    print("  3. rapidkit init              # project bootstrap")
    print("  4. ./bootstrap.sh")
    print("  5. rapidkit dev               # project runtime")
    print("\nWorkspace intelligence:")
    print("  • From the workspace root, run: npx workspai workspace model --json")
    print(
        "\nExplore the layered structure under src/app to connect domain, application,"
        " infrastructure, and presentation boundaries."
    )
    print(
        "Use `poetry export --format requirements.txt --output requirements.txt` if tooling needs a requirements file."
    )

    if variables:
        module_toggles = [
            ("install_logging", "logging", True),
            ("install_settings", "settings", True),
            ("install_deployment", "deployment", True),
            ("enable_postgres", "db_postgres", False),
            ("enable_sqlite", "db_sqlite", True),
            ("enable_redis", "redis", False),
            ("enable_monitoring", "monitoring", False),
            ("enable_tracing", "tracing", False),
            ("enable_docs", "openapi_docs", True),
        ]

        missing_modules = [
            module_name
            for flag, module_name, default in module_toggles
            if not variables.get(flag, default)
        ]

        if missing_modules:
            print("\nConsider enriching the architecture with additional RapidKit modules:")
            for module_name in dict.fromkeys(missing_modules):
                print(f"  • rapidkit add module {module_name}")

    print("=" * 60)
