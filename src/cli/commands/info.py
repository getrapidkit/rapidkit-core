# cli/commands/info.py
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.engine.registry import KitRegistry

from ..ui.printer import print_error

console = Console()

app = typer.Typer(help="Get detailed info about a kit")


@app.command()
def info(name: str = typer.Argument(help="Name of the kit to inspect")) -> None:
    """
    🔍 Show detailed info about a specific kit

    Example:
      rapidkit info fastkit_minimal
    """
    try:
        registry = KitRegistry()

        if not registry.kit_exists(name):
            print_error(f"❌ Kit '{name}' not found")
            raise typer.Exit(code=1)

        kit = registry.get_kit(name)

        console.rule(f"[bold green]📦 {kit.display_name}[/bold green]")

        table = Table(show_header=False, show_lines=True)
        table.add_row("Name", kit.name)
        table.add_row("Version", kit.version)
        table.add_row("Category", kit.category)
        table.add_row("Tags", ", ".join(kit.tags or []))
        table.add_row("Modules", ", ".join(kit.modules or []))
        table.add_row("Location", str(kit.path))

        console.print(table)

        if kit.variables:
            var_table = Table(title="🔧 Required Variables", show_lines=True)
            var_table.add_column("Name", style="cyan", no_wrap=True)
            var_table.add_column("Required", style="red")
            var_table.add_column("Description", style="white")

            for var in kit.variables:
                var_table.add_row(
                    var.name,
                    "✅ Yes" if var.required else "❌ No",
                    var.description or "-",
                )

            console.print(var_table)

        if kit.description:
            console.print(Panel.fit(kit.description, title="📘 Description", border_style="blue"))

    except (FileNotFoundError, OSError, ValueError, KeyError) as e:
        print_error(f"❌ Error: {e}")
        raise typer.Exit(code=1) from None
