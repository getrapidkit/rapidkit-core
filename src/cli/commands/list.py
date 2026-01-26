import typer
from rich.console import Console
from rich.table import Table

from core.engine.registry import KitRegistry

from ..ui.printer import print_error

_DESC_PREVIEW_LEN = 60

console = Console()


def list_kits(
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed info"),
) -> None:
    """
    📦 List all available kits in the registry.

    Examples:
      rapidkit list
      rapidkit list --category fastapi
      rapidkit list --tag auth
      rapidkit list --detailed
    """
    try:
        registry = KitRegistry()
        kits = registry.list_kits()

        # Filters
        if category:
            kits = [k for k in kits if k.category.lower() == category.lower()]

        if tag:
            kits = [k for k in kits if tag.lower() in map(str.lower, k.tags)]

        if not kits:
            print_error("😕 No kits found matching the criteria.")
            raise typer.Exit()

        if detailed:
            for kit in kits:
                console.rule(f"[bold green]📦 {kit.display_name}[/bold green]")
                console.print(f"[bold]Name:[/bold] {kit.name}")
                console.print(f"[bold]Version:[/bold] {kit.version}")
                console.print(f"[bold]Category:[/bold] {kit.category}")
                console.print(f"[bold]Tags:[/bold] {', '.join(kit.tags)}")
                console.print(f"[bold]Modules:[/bold] {', '.join(kit.modules or [])}")
                console.print(f"[bold]Description:[/bold] {kit.description}")
                console.print()
        else:
            table = Table(title="📦 Available Kits", show_lines=True)
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Display Name", style="green")
            table.add_column("Category", style="magenta")
            table.add_column("Version", style="yellow")
            table.add_column("Description", style="white")

            for kit in kits:
                table.add_row(
                    kit.name,
                    kit.display_name,
                    kit.category,
                    kit.version,
                    kit.description[:_DESC_PREVIEW_LEN]
                    + ("..." if len(kit.description) > _DESC_PREVIEW_LEN else ""),
                )

            console.print(table)

        console.print(f"\n📊 Total: {len(kits)} kit(s)")

    except (OSError, ValueError, KeyError) as e:
        print_error(f"❌ Error: {e}")
        raise typer.Exit(code=1) from None
