# src / cli / commands / add.py

import typer

from .add import all as add_all
from .add.module import add_module

add_app = typer.Typer(help="➕ Add components like modules, resources, etc.")

# Create a Typer app for the module command
module_app = typer.Typer()
module_app.command()(add_module)

# Register subcommands
add_app.add_typer(module_app, name="module")
add_app.add_typer(add_all.all_app, name="all")
