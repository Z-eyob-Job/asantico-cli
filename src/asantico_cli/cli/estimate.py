"""Estimate commands for the CLI."""

import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, Optional

import typer
from rich.console import Console

from asantico_cli.domain.models import (
    DEFAULT_RATES,
    DOC_TYPE_ESTIMATE,
    Document,
    LineItem,
    Property,
)
from asantico_cli.domain.tax import compute_totals, format_currency
from asantico_cli.infra.config import increment_counter, load_rates
from asantico_cli.infra.loader import LoaderError, load_line_items, load_notes
from asantico_cli.infra.pdf import render_pdf

app = typer.Typer(help="Estimate commands")
console = Console()
error_console = Console(stderr=True)


def line_items_from_triage(
    triage: dict[str, Any], labor_rate: Decimal
) -> list[LineItem]:
    """Map a triaged work order into estimate line items.

    Produces a single labor line for the reported issue, priced at the
    configured labor rate. Tax is applied later by the existing engine, which
    taxes this labor-only line at the Seattle rate like any other line.

    Args:
        triage: A triage record in the shape emitted by "triage run --json".
        labor_rate: The labor unit price in USD.

    Returns:
        A list of LineItem objects for the estimate.
    """
    issue = (triage.get("issue_summary") or "").strip()
    trade = (triage.get("trade") or "general").strip()
    description = issue if issue else f"{trade} service"
    return [
        LineItem(
            description=description,
            quantity=Decimal("1"),
            unit="hr",
            unit_price=labor_rate,
        )
    ]


def _load_triage_record(source: str) -> dict[str, Any]:
    """Load a triage JSON record from a file path or stdin.

    Consumes the shape emitted by "triage run --json", including from stdin
    when source is "-".

    Args:
        source: Path to the triage JSON file, or "-" for standard input.

    Returns:
        Parsed triage record.

    Raises:
        typer.Exit: If the input cannot be read or parsed.
    """
    if source == "-":
        text = sys.stdin.read()
    else:
        path = Path(source)
        if not path.is_file():
            error_console.print(f"[red]Error:[/red] File not found: {source}")
            raise typer.Exit(code=1)
        text = path.read_text(encoding="utf-8")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        error_console.print(f"[red]Error:[/red] Invalid triage JSON: {exc}")
        raise typer.Exit(code=1)
    if not isinstance(data, dict):
        error_console.print("[red]Error:[/red] Triage JSON must be an object.")
        raise typer.Exit(code=1)
    return data


@app.command("new")
def new_estimate(
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
    from_triage: Annotated[
        Optional[str],
        typer.Option(
            "--from-triage",
            help="Path to a triage JSON record, or - for stdin (triage run --json shape)",
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
    """Generate a new estimate PDF.

    Provide either --from-triage (a triaged work order) or --from-file (a line
    items JSON). Interactive mode (without flags) is not yet implemented.
    """
    if from_triage is not None:
        line_items, resolved_property, notes = _estimate_inputs_from_triage(
            from_triage, property_name
        )
    elif from_file is not None:
        if property_name is None:
            error_console.print(
                "[red]Error:[/red] --property is required with --from-file."
            )
            raise typer.Exit(code=1)
        try:
            line_items = load_line_items(from_file)
            notes = load_notes(from_file)
        except LoaderError as e:
            error_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)
        resolved_property = property_name
    else:
        error_console.print(
            "[red]Error:[/red] provide --from-triage or --from-file. "
            "Interactive mode is not yet implemented."
        )
        raise typer.Exit(code=1)

    # Get next document number
    doc_number = increment_counter(DOC_TYPE_ESTIMATE)

    # Create document
    doc = Document(
        doc_type=DOC_TYPE_ESTIMATE,
        doc_number=doc_number,
        date=date.today(),
        property=Property(name=resolved_property),
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

    # Summarize totals via the existing tax engine for operator visibility.
    subtotal, total_tax, grand_total = compute_totals(line_items)
    console.print(
        f"Subtotal {format_currency(subtotal)}, "
        f"tax {format_currency(total_tax)}, "
        f"total {format_currency(grand_total)}"
    )


def _estimate_inputs_from_triage(
    from_triage: str, property_override: Optional[str]
) -> tuple[list[LineItem], str, Optional[str]]:
    """Resolve estimate inputs from a triage record.

    Args:
        from_triage: Path to the triage JSON, or - for stdin.
        property_override: Optional --property value that wins over the record.

    Returns:
        A tuple of (line_items, property_name, notes).

    Raises:
        typer.Exit: If no property can be resolved.
    """
    triage = _load_triage_record(from_triage)
    resolved_property = property_override or triage.get("property_name")
    if not resolved_property:
        error_console.print(
            "[red]Error:[/red] no property in triage record; pass --property."
        )
        raise typer.Exit(code=1)

    labor_rate = load_rates().get("labor", DEFAULT_RATES["labor"])
    line_items = line_items_from_triage(triage, labor_rate)
    issue = (triage.get("issue_summary") or "").strip()
    notes = f"Estimate prepared from triaged work order: {issue}" if issue else None
    return line_items, str(resolved_property), notes
