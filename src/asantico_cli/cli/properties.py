"""Properties management commands for the CLI."""

from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from asantico_cli.domain.models import Property
from asantico_cli.infra.config import load_properties, save_properties

app = typer.Typer(help="Property management commands")
console = Console()
error_console = Console(stderr=True)


@app.command("list")
def list_properties() -> None:
    """List all configured properties."""
    properties = load_properties()

    table = Table(title="Properties")
    table.add_column("Name", style="cyan")
    table.add_column("Address", style="dim")

    for prop in properties:
        table.add_row(prop.name, prop.address or "")

    console.print(table)


@app.command("add")
def add_property(
    name: Annotated[
        str,
        typer.Argument(help="Property name to add"),
    ],
    address: Annotated[
        Optional[str],
        typer.Option(
            "--address",
            help="Optional property address",
        ),
    ] = None,
) -> None:
    """Add a new property to the registry."""
    properties = load_properties()

    # Check if property already exists
    existing_names = {p.name.lower() for p in properties}
    if name.lower() in existing_names:
        error_console.print(f"[red]Error:[/red] Property already exists: {name}")
        raise typer.Exit(code=1)

    # Add new property
    new_property = Property(name=name, address=address)
    properties.append(new_property)
    save_properties(properties)

    console.print(f"[green]Added property:[/green] {name}")


@app.command("remove")
def remove_property(
    name: Annotated[
        str,
        typer.Argument(help="Property name to remove"),
    ],
) -> None:
    """Remove a property from the registry."""
    properties = load_properties()

    # Find property (case-insensitive)
    found_index = None
    for i, prop in enumerate(properties):
        if prop.name.lower() == name.lower():
            found_index = i
            break

    if found_index is None:
        error_console.print(f"[red]Error:[/red] Property not found: {name}")
        raise typer.Exit(code=1)

    # Remove property
    removed = properties.pop(found_index)
    save_properties(properties)

    console.print(f"[green]Removed property:[/green] {removed.name}")
