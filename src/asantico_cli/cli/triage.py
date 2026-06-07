"""Triage command for the CLI.

Reads a raw work order request, classifies it via the triage layer (offline by
default), prints a Rich table, and stops with a HUMAN REVIEW banner when the
case is flagged. PII is redacted before any model call inside the triage layer;
the table shows restored values for the operator's local view only.
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from asantico_cli.domain.triage import TriageResult
from asantico_cli.infra.llm import triage_request

app = typer.Typer(help="Triage commands")
console = Console()
error_console = Console(stderr=True)


def _extract_raw_text(content: str) -> str:
    """Extract the request text from file content.

    If the content is a work order JSON object with a "raw_text" field, returns
    that field so the cache key matches. Otherwise returns the content as is.

    Args:
        content: The raw file content.

    Returns:
        The request text to triage.
    """
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return content
    if isinstance(parsed, dict) and isinstance(parsed.get("raw_text"), str):
        return parsed["raw_text"]
    return content


def _read_source(source: str) -> str:
    """Read raw request text from a file path or stdin.

    A file that is a work order JSON object with a "raw_text" field has that
    field extracted. Plain text files and stdin are used verbatim.

    Args:
        source: A file path, or "-" to read from standard input.

    Returns:
        The raw request text.

    Raises:
        typer.Exit: If the file is missing or the input is empty.
    """
    if source == "-":
        raw_text = sys.stdin.read()
    else:
        path = Path(source)
        if not path.is_file():
            error_console.print(f"[red]Error:[/red] File not found: {source}")
            raise typer.Exit(code=1)
        raw_text = _extract_raw_text(path.read_text(encoding="utf-8"))

    if not raw_text.strip():
        error_console.print("[red]Error:[/red] No input text provided.")
        raise typer.Exit(code=1)
    return raw_text


def _result_table(result: TriageResult) -> Table:
    """Build a Rich table summarizing a triage result.

    Args:
        result: The triage result to display.

    Returns:
        A populated Rich Table.
    """

    def confidence(field_name: str) -> str:
        score = result.confidence.get(field_name)
        return f"{score:.2f}" if score is not None else ""

    table = Table(title="Triage result")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")
    table.add_column("Confidence", justify="right", style="dim")

    table.add_row("Urgency", result.urgency, confidence("urgency"))
    table.add_row("Trade", result.trade, confidence("trade"))
    table.add_row("Property", result.property_name or "", confidence("property_name"))
    table.add_row("Unit", result.unit or "", confidence("unit"))
    table.add_row(
        "Tenant contact", result.tenant_contact or "", confidence("tenant_contact")
    )
    table.add_row("Issue summary", result.issue_summary, confidence("issue_summary"))
    return table


@app.command("run")
def run_triage(
    source: Annotated[
        str,
        typer.Argument(
            help="Path to a file containing the raw request, or - for stdin",
        ),
    ],
    live: Annotated[
        bool,
        typer.Option(
            "--live",
            help="Call the live model instead of the offline recorded cache",
        ),
    ] = False,
    threshold: Annotated[
        float,
        typer.Option(
            "--threshold",
            help="Minimum acceptable per-field confidence before review",
        ),
    ] = 0.7,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print the TriageResult as JSON to stdout for command handoff",
        ),
    ] = False,
) -> None:
    """Triage a raw work order request and print the structured result.

    Reads raw text from a file or stdin, classifies urgency and trade, and
    prints a Rich table. With --json, prints the result as JSON to stdout for
    piping into draft-reply. If the case needs review, prints a HUMAN REVIEW
    banner and does not progress to drafting or estimating.
    """
    raw_text = _read_source(source)

    try:
        result = triage_request(raw_text, live=live, threshold=threshold)
    except RuntimeError as exc:
        error_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    if json_output:
        # Keep stdout pure JSON for piping; human messaging goes to stderr.
        typer.echo(json.dumps(asdict(result)))
        if result.needs_review:
            error_console.print(
                "HUMAN REVIEW REQUIRED: this request was flagged. "
                "Review before sending any reply or estimate."
            )
        return

    console.print(_result_table(result))

    if result.needs_review:
        console.print(
            Panel(
                "HUMAN REVIEW REQUIRED\n"
                "This request was flagged and will not progress automatically. "
                "An operator must review it before any reply or estimate.",
                title="Action needed",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=0)
