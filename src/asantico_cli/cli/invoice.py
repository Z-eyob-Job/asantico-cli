"""Invoice commands for the CLI."""

from datetime import date
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from asantico_cli.domain.models import DOC_TYPE_INVOICE, Document, Property
from asantico_cli.infra.config import increment_counter
from asantico_cli.infra.loader import LoaderError, load_line_items, load_notes
from asantico_cli.infra.pdf import render_pdf

app = typer.Typer(help="Invoice commands")
console = Console()
error_console = Console(stderr=True)


@app.command("new")
def new_invoice(
    from_file: Annotated[
        Optional[Path],
        typer.Option(
            "--from-file",
            help="Path to JSON file containing line items",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    property_name: Annotated[
        Optional[str],
        typer.Option(
            "--property",
            help="Property name (from registry or new)",
        ),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output directory for PDF",
        ),
    ] = Path("./output"),
) -> None:
    """Generate a new invoice PDF.

    Requires both --from-file and --property for file-based mode.
    Interactive mode (without flags) is not yet implemented.
    """
    # Validate required arguments for file-based mode
    if from_file is None:
        error_console.print(
            "[red]Error:[/red] --from-file is required. "
            "Interactive mode is not yet implemented."
        )
        raise typer.Exit(code=1)

    if property_name is None:
        error_console.print(
            "[red]Error:[/red] --property is required. "
            "Interactive mode is not yet implemented."
        )
        raise typer.Exit(code=1)

    # Load line items from JSON
    try:
        line_items = load_line_items(from_file)
        notes = load_notes(from_file)
    except LoaderError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    # Get next document number
    doc_number = increment_counter(DOC_TYPE_INVOICE)

    # Create document
    doc = Document(
        doc_type=DOC_TYPE_INVOICE,
        doc_number=doc_number,
        date=date.today(),
        property=Property(name=property_name),
        line_items=line_items,
        notes=notes,
    )

    # Render PDF
    try:
        output_path = render_pdf(doc, output_dir)
        console.print(f"[green]Created:[/green] {output_path}")
    except Exception as e:
        error_console.print(f"[red]Error:[/red] Failed to create PDF: {e}")
        raise typer.Exit(code=2)
