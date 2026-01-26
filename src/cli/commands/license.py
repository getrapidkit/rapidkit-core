"""
CLI for RapidKit license management: inspect and activate license.json

This module provides commands for managing RapidKit licenses including:
- Inspecting current license information
- Activating new licenses from files
- Checking license status
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, cast

import typer

license_app = typer.Typer(help="Manage RapidKit license.")

# Path to the global license file
LICENSE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "license.json"
)


def load_license() -> Dict[str, Any]:
    """Load license data from the license file."""
    if not os.path.exists(LICENSE_PATH):
        typer.echo("No license.json found.")
        sys.exit(1)
    with open(LICENSE_PATH, encoding="utf-8") as f:
        return cast(Dict[str, Any], json.load(f))


def save_license(data: Dict[str, Any]) -> None:
    """Save license data to the license file."""
    with open(LICENSE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@license_app.command("inspect")
def inspect() -> None:
    """Show current license info."""
    lic = load_license()
    typer.echo(json.dumps(lic, indent=2))


@license_app.command("activate")
def activate(
    license_file: str = typer.Argument(help="Path to license file"),
) -> None:
    """Activate a new license from a file."""
    license_path = Path(license_file)
    if not license_path.exists():
        typer.echo(f"License file not found: {license_file}")
        sys.exit(1)

    with open(license_path, encoding="utf-8") as f:
        new_lic = json.load(f)
    # (Optional: verify signature here)
    save_license(new_lic)
    typer.echo("License activated successfully.")


@license_app.command("status")
def status() -> None:
    """Show license status."""
    if not os.path.exists(LICENSE_PATH):
        typer.echo("No license found. Using community edition.")
        return

    lic = load_license()
    typer.echo(f"License ID: {lic.get('license_id', 'Unknown')}")
    typer.echo(f"Tier: {lic.get('tier', 'Unknown')}")
    typer.echo(f"Expires: {lic.get('expires_at', 'Unknown')}")
    typer.echo(f"Issued to: {lic.get('issued_to', 'Unknown')}")


if __name__ == "__main__":
    license_app()
