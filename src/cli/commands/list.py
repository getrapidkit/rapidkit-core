import json

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
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """
    📦 List all available kits in the registry.

    Examples:
      rapidkit list
      rapidkit list --category fastapi
      rapidkit list --tag auth
      rapidkit list --detailed
    """
    # NOTE: When called directly from Python (e.g. unit tests), Typer's
    # Option(...) defaults are OptionInfo objects (truthy). Normalise them.
    category_val = category if isinstance(category, str) else None
    tag_val = tag if isinstance(tag, str) else None
    detailed_flag = detailed if isinstance(detailed, bool) else False
    json_flag = json_output if isinstance(json_output, bool) else False

    try:
        registry = KitRegistry()
        kits = registry.list_kits()

        # Filters
        if category_val:
            kits = [k for k in kits if k.category.lower() == category_val.lower()]

        if tag_val:
            kits = [k for k in kits if tag_val.lower() in map(str.lower, k.tags)]

        if not kits:
            print_error("😕 No kits found matching the criteria.")
            raise typer.Exit()

        if json_flag:
            payload = {
                "schema_version": 1,
                "ok": True,
                "filters": {
                    "category": category_val,
                    "tag": tag_val,
                    "detailed": bool(detailed_flag),
                },
                "count": len(kits),
                "kits": [
                    {
                        "name": kit.name,
                        "display_name": kit.display_name,
                        "category": kit.category,
                        "version": kit.version,
                        "tags": list(kit.tags or []),
                        "modules": list(kit.modules or []),
                        "description": kit.description,
                    }
                    for kit in kits
                ],
            }
            print(json.dumps(payload, ensure_ascii=False))
            return

        if detailed_flag:
            for kit in kits:
                console.rule(f"[bold green]📦 {kit.display_name}[/bold green]")
                console.print(f"[bold]Name:[/bold] {kit.name}")
                console.print(f"[bold]Version:[/bold] {kit.version}")
                console.print(f"[bold]Category:[/bold] {kit.category}")
                console.print(f"[bold]Tags:[/bold] {', '.join(kit.tags or [])}")
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
        if json_flag:
            payload = {
                "schema_version": 1,
                "ok": False,
                "error": "LIST_FAILED",
                "message": str(e),
            }
            print(json.dumps(payload, ensure_ascii=False))
            raise typer.Exit(code=1) from None

        print_error(f"❌ Error: {e}")
        raise typer.Exit(code=1) from None
