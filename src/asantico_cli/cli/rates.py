"""Rates management commands for the CLI."""

from decimal import Decimal, InvalidOperation
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from asantico_cli.domain.tax import format_currency
from asantico_cli.infra.config import load_rates, save_rates

app = typer.Typer(help="Rate management commands")
console = Console()
error_console = Console(stderr=True)

VALID_RATE_TYPES = {"labor", "materials"}


@app.command("list")
def list_rates() -> None:
    """List all configured rates."""
    rates = load_rates()

    table = Table(title="Rates")
    table.add_column("Type", style="cyan")
    table.add_column("Rate", style="green", justify="right")

    for rate_type, value in sorted(rates.items()):
        table.add_row(rate_type, format_currency(value))

    console.print(table)


@app.command("set")
def set_rate(
    rate_type: Annotated[
        str,
        typer.Argument(help="Rate type (labor or materials)"),
    ],
    value: Annotated[
        str,
        typer.Argument(help="Rate value in USD"),
    ],
) -> None:
    """Set a default rate."""
    # Validate rate type
    if rate_type.lower() not in VALID_RATE_TYPES:
        error_console.print(
            f"[red]Error:[/red] Invalid rate type: {rate_type}. "
            f"Must be one of: {', '.join(sorted(VALID_RATE_TYPES))}"
        )
        raise typer.Exit(code=1)

    # Parse and validate value
    try:
        decimal_value = Decimal(value)
        if decimal_value < 0:
            error_console.print(
                f"[red]Error:[/red] Rate value cannot be negative: {value}"
            )
            raise typer.Exit(code=1)
    except InvalidOperation:
        error_console.print(
            f"[red]Error:[/red] Invalid rate value: {value}. Must be a number."
        )
        raise typer.Exit(code=1)

    # Load, update, and save rates
    rates = load_rates()
    rates[rate_type.lower()] = decimal_value
    save_rates(rates)

    console.print(f"[green]Set {rate_type} rate to[/green] {format_currency(decimal_value)}")
