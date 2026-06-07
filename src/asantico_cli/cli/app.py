"""Main Typer application and CLI entrypoint."""

from typing import Annotated, Optional

import typer

from asantico_cli import __version__
from asantico_cli.cli import estimate, invoice, properties, rates, triage

app = typer.Typer(
    name="asantico",
    help="Generate professional PDF invoices and estimates for Asantico property maintenance.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"asantico, version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show version number and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Asantico Invoice CLI.

    Generate professional PDF invoices and estimates for property maintenance work.
    """
    pass


# Register subcommands
app.add_typer(invoice.app, name="invoice")
app.add_typer(estimate.app, name="estimate")
app.add_typer(properties.app, name="properties")
app.add_typer(rates.app, name="rates")
app.add_typer(triage.app, name="triage")


if __name__ == "__main__":
    app()
