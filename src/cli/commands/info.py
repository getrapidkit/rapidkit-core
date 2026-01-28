"""Kit inspection command."""

from __future__ import annotations

import json
from typing import Any, Dict

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.engine.registry import KitRegistry

from ..ui.printer import print_error

console = Console()

app = typer.Typer(help="Get detailed info about a kit")


@app.command()
def info(
    name: str = typer.Argument(help="Name of the kit to inspect"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    """
    🔍 Show detailed info about a specific kit

    Example:
      rapidkit info fastkit_minimal
    """
    # NOTE: When calling this function directly in Python (e.g. tests), the
    # default value can be a Typer OptionInfo object, which is truthy.
    # Normalise to a real bool.
    json_flag = json_output if isinstance(json_output, bool) else False
    try:
        registry = KitRegistry()

        if not registry.kit_exists(name):
            if json_flag:
                typer.echo(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "ok": False,
                            "error": "KIT_NOT_FOUND",
                            "message": f"Kit '{name}' not found",
                            "kit": None,
                        },
                        ensure_ascii=False,
                    )
                )
                raise typer.Exit(code=1)

            print_error(f"❌ Kit '{name}' not found")
            raise typer.Exit(code=1)

        kit = registry.get_kit(name)

        if json_flag:
            payload: Dict[str, Any] = {
                "schema_version": 1,
                "ok": True,
                "kit": {
                    "name": kit.name,
                    "display_name": getattr(kit, "display_name", kit.name),
                    "version": getattr(kit, "version", None),
                    "category": getattr(kit, "category", None),
                    "tags": list(getattr(kit, "tags", []) or []),
                    "modules": list(getattr(kit, "modules", []) or []),
                    "location": str(getattr(kit, "path", "")),
                    "description": getattr(kit, "description", None),
                    "variables": [
                        {
                            "name": v.name,
                            "required": bool(v.required),
                            "description": v.description or None,
                        }
                        for v in (getattr(kit, "variables", None) or [])
                    ],
                },
            }
            typer.echo(json.dumps(payload, ensure_ascii=False))
            return

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
        if json_flag:
            typer.echo(
                json.dumps(
                    {
                        "schema_version": 1,
                        "ok": False,
                        "error": "INFO_FAILED",
                        "message": str(e),
                        "kit": None,
                    },
                    ensure_ascii=False,
                )
            )
            raise typer.Exit(code=1) from None

        print_error(f"❌ Error: {e}")
        raise typer.Exit(code=1) from None
