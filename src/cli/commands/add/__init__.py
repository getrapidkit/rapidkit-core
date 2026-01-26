# src/cli/commands/add/__init__.py
import typer

from .all import all_app

# Import the module command and the 'all' sub-typer
from .module import add_module

# Compose a single add_app Typer that exposes the module command and the 'all' sub-typer
add_app = typer.Typer(help="➕ Add components like modules, resources, etc.")

# Direct command: `rapidkit add module <name>` (backwards compatible)
add_app.command("module")(add_module)

# Sub-typer: `rapidkit add all module ...`
add_app.add_typer(all_app, name="all")
