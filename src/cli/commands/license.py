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
from typing import Any, Dict, List, Optional, cast

import typer
from typer.models import OptionInfo

from core.kit_utils import validate_license_auto
from core.license_utils import validate_license_for_item

license_app = typer.Typer(help="Manage RapidKit license.")

# Backward-compatible mutable path used by tests via monkeypatch.
LICENSE_PATH = str(Path.home() / ".rapidkit" / "license.json")


def _default_project_license_path(cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    return base / ".rapidkit" / "license.json"


def load_license(license_path: Optional[str] = None) -> Dict[str, Any]:
    """Load license data from the license file."""
    path = license_path or LICENSE_PATH
    if not os.path.exists(path):
        typer.echo("No license.json found.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return cast(Dict[str, Any], json.load(f))


def save_license(data: Dict[str, Any], license_path: Optional[str] = None) -> None:
    """Save license data to the license file."""
    path = license_path or LICENSE_PATH
    parent = Path(path).parent
    parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@license_app.command("inspect")
def inspect() -> None:
    """Show current license info."""
    lic = load_license()
    typer.echo(json.dumps(lic, indent=2))


@license_app.command("activate")
def activate(
    license_file: str = typer.Argument(help="Path to license file"),
    project: bool = typer.Option(
        False,
        "--project",
        help="Store active license in ./.rapidkit/license.json for current project.",
    ),
) -> None:
    """Activate a new license from a file."""
    project_obj: object = project
    if isinstance(project_obj, OptionInfo):
        default = project_obj.default if project_obj.default is not ... else False
        project = bool(default)

    license_path = Path(license_file)
    if not license_path.exists():
        typer.echo(f"License file not found: {license_file}")
        sys.exit(1)

    with open(license_path, encoding="utf-8") as f:
        new_lic = json.load(f)
    if not isinstance(new_lic, dict):
        typer.echo("Invalid license format: expected a JSON object.")
        sys.exit(1)

    target_path = str(_default_project_license_path()) if project else LICENSE_PATH

    # (Optional: verify signature here)
    save_license(new_lic, target_path)
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


@license_app.command("verify")
def verify(
    item_name: str = typer.Argument(help="Module/kit/addon name to verify"),
    item_type: str = typer.Option("modules", "--item-type", help="One of modules|kits|addons"),
    required_tier: Optional[str] = typer.Option(
        None, "--required-tier", help="Required tier (free|paid|enterprise)"
    ),
    required_features: str = typer.Option(
        "", "--required-features", help="Comma-separated required features"
    ),
    licenses_dir: Optional[str] = typer.Option(
        None,
        "--licenses-dir",
        help="Explicit licenses directory override",
    ),
) -> None:
    """Verify active license entitlement for a specific item."""
    parsed_features: List[str] = [
        part.strip() for part in required_features.split(",") if part.strip()
    ]

    try:
        active_path = Path(LICENSE_PATH)
        if licenses_dir is None and active_path.exists():
            validate_license_for_item(
                license_path=str(active_path),
                item_type=item_type,
                item_name=item_name,
                required_tier=required_tier,
                required_features=parsed_features or None,
            )
        else:
            validate_license_auto(
                item_type=item_type,
                item_name=item_name,
                required_tier=required_tier,
                required_features=parsed_features or None,
                licenses_dir=licenses_dir,
            )
    except RuntimeError as exc:
        typer.echo(f"License verification failed: {exc}")
        sys.exit(1)

    typer.echo("License verification successful.")


@license_app.command("revoke")
def revoke(
    license_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Expected license_id to revoke (optional safety check)",
    ),
) -> None:
    """Revoke local active license (removes active license file)."""
    path = Path(LICENSE_PATH)
    if not path.exists():
        typer.echo("No active license found.")
        return

    if license_id is not None:
        lic = load_license()
        current = str(lic.get("license_id", ""))
        if current != license_id:
            typer.echo(f"License ID mismatch: active={current or 'unknown'} expected={license_id}")
            sys.exit(1)

    try:
        path.unlink()
    except OSError as exc:
        typer.echo(f"Failed to revoke local license: {exc}")
        sys.exit(1)

    typer.echo("License revoked locally.")


@license_app.command("broker-serve")
def broker_serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8765, "--port", help="Bind port"),
) -> None:
    """Run the local Licensing Broker API service."""
    try:
        import uvicorn

        from core.licensing.api import create_app
    except ImportError as exc:
        typer.echo(f"Broker dependencies unavailable: {exc}")
        sys.exit(1)

    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    license_app()
