from __future__ import annotations

import json

import typer

from core.config.version import get_version


def version(
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    """Print RapidKit version.

    Use this instead of parsing `--version` output when scripting.
    """

    payload = {"schema_version": 1, "version": get_version()}
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False))
        return

    typer.echo(f"RapidKit Version v{payload['version']}")
