"""Lifecycle hooks for the FastAPI DDD kit."""

from __future__ import annotations

import getpass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def pre_generate(variables: Dict[str, Any]) -> None:
    """Ensure common metadata defaults before generation."""
    variables.setdefault("author", getpass.getuser())
    variables.setdefault("app_version", "0.1.0")
    variables.setdefault("description", "Domain-driven FastAPI service generated with RapidKit")
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

    # Generate a poetry.lock for reproducible installs unless the user opts out.
    try:
        import os
        import subprocess  # nosec - safe use for lock generation

        def _is_truthy(value: object) -> bool:
            return str(value).lower() in {"1", "true", "yes", "on"}

        env_toggle = os.environ.get("RAPIDKIT_GENERATE_LOCKS")
        if env_toggle is not None:
            should_lock = _is_truthy(env_toggle)
        elif _is_truthy(os.environ.get("RAPIDKIT_SKIP_LOCKS", "0")):
            should_lock = False
        elif variables and "generate_lock" in variables:
            should_lock = bool(variables.get("generate_lock", True))
        else:
            should_lock = True

        if should_lock:
            print("\nℹ️ Generating poetry.lock (automatic lockfiles enabled)")
            subprocess.run(
                ["poetry", "lock"], cwd=str(output_path), check=False
            )  # nosec - safe, static tool invocation
            print("ℹ️ poetry.lock generation attempted (check output above).")
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        print("WARN: Lockfile generation attempted and failed. Continuing without locking.")
    print(f"📁 Project: {project_name}")
    print(f"📂 Location: {output_path}")
    print("\nNext steps:")
    print(f"  1. cd {project_name}")
    print("  2. source .rapidkit/activate")
    print("  3. rapidkit init")
    print("  4. ./bootstrap.sh")
    print("  5. rapidkit dev")
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
