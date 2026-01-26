# src/cli/commands/dev/dev_app.py
"""Development commands application."""

import typer

from .modules import modules_app

app = typer.Typer(help="Development tools for contributors")
app.add_typer(modules_app, name="modules", help="Module development tools")
