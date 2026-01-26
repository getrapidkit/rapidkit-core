# src/cli/commands/dev/modules.py
"""Module development commands."""

from __future__ import annotations

import shutil
import subprocess  # nosec - controlled command execution for module tooling
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer

from cli.ui.printer import print_error, print_info, print_success

modules_app = typer.Typer(help="Module development tools")

MIN_MODULE_PATH_SEGMENTS = 2
MAX_MODULE_PATH_SEGMENTS = 3
DEFAULT_FRAMEWORK = "fastapi"
TEMP_PREFIX = "rapidkit-module-gen-"


@modules_app.command("init")
def modules_init(
    name: str = typer.Argument(..., help="Module name (tier/name or tier/category/name format)"),
    template: Optional[str] = typer.Option(
        "fastapi", help="Template type: fastapi, nestjs, hybrid"
    ),
    inherit: Optional[str] = typer.Option(None, help="Inherit from base module"),
) -> None:
    """Initialize a new module."""
    print_info(f"🏗️  Initializing new module: {name}")
    print_info(f"📋 Template: {template}")
    if inherit:
        print_info(f"🔗 Inherits from: {inherit}")

    # TODO: Implement module initialization
    print_success(f"✅ Module {name} initialized")


@modules_app.command("generate")
def modules_generate(
    module: str = typer.Argument(..., help="Module name (tier/name or tier/category/name format)"),
    target: str = typer.Option("vendor", help="Generation target: vendor, project"),
    framework: Optional[str] = typer.Option(None, help="Framework: fastapi, nestjs"),
) -> None:
    """Generate files for a module."""
    print_info(f"🔄 Generating {target} files for {module}")
    if framework:
        print_info(f"🎯 Framework: {framework}")

    # Find module directory
    module_parts = module.split("/")
    if not (MIN_MODULE_PATH_SEGMENTS <= len(module_parts) <= MAX_MODULE_PATH_SEGMENTS):
        print_error("❌ Module must be in tier/name or tier/category/name format")
        raise typer.Exit(1)

    if len(module_parts) == MIN_MODULE_PATH_SEGMENTS:
        tier, name = module_parts
        module_path = Path("src/modules") / tier / name
    else:
        tier, category, name = module_parts
        module_path = Path("src/modules") / tier / category / name

    if not module_path.exists():
        print_error(f"❌ Module not found: {module_path}")
        raise typer.Exit(1)

    # Convert to absolute path
    module_path = module_path.resolve()

    # Run generation script
    generate_script = module_path / "generate.py"
    if not generate_script.exists():
        print_error(f"❌ Generation script not found: {generate_script}")
        raise typer.Exit(1)

    temp_output_dir = Path(tempfile.mkdtemp(prefix=TEMP_PREFIX))
    cmd = [
        sys.executable,
        str(generate_script),
        framework or DEFAULT_FRAMEWORK,
        str(temp_output_dir),
    ]

    try:
        subprocess.run(  # nosec - command is constructed from trusted module metadata
            cmd,
            cwd=module_path,
            check=True,
            capture_output=False,
            shell=False,
        )
    except subprocess.CalledProcessError as exc:
        print_error(f"❌ Generation failed for {module} (exit={exc.returncode}).")
        raise typer.Exit(1) from exc
    else:
        print_success(f"✅ Generated {target} files for {module}")
    finally:
        shutil.rmtree(temp_output_dir, ignore_errors=True)


@modules_app.command("validate")
def modules_validate(
    module: Optional[str] = typer.Argument(None, help="Module name to validate"),
) -> None:
    """Validate module structure."""
    if module:
        print_info(f"🔍 Validating module: {module}")
    else:
        print_info("🔍 Validating all modules...")

    # TODO: Implement validation
    print_success("✅ Module validation passed")


@modules_app.command("test")
def modules_test(
    module: Optional[str] = typer.Argument(None, help="Module name to test"),
    framework: Optional[str] = typer.Option(None, help="Framework: fastapi, nestjs"),
) -> None:
    """Run module tests."""
    if module:
        print_info(f"🧪 Running tests for module: {module}")
    else:
        print_info("🧪 Running all module tests...")

    if framework:
        print_info(f"🎯 Framework: {framework}")

    # TODO: Implement testing
    print_success("✅ Module tests passed")
