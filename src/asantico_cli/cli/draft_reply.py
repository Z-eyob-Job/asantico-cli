"""Draft-reply command for the CLI.

Produces a tenant acknowledgment from a triage JSON record. The acknowledgment
is a DRAFT by default and is never sent. Marking it sent requires an explicit
--approve flag and, in this build, only appends a local record to
sent_log.jsonl. No real email or SMS is sent.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel

from asantico_cli.infra.config import ensure_config_dir, get_config_dir

app = typer.Typer(help="Draft tenant acknowledgment replies")
console = Console()
error_console = Console(stderr=True)


def get_sent_log_path() -> Path:
    """Return the path to the local sent log (~/.asantico/sent_log.jsonl).

    Returns:
        Path to the sent log file inside the config directory.
    """
    return get_config_dir() / "sent_log.jsonl"


def _load_triage(source: str) -> dict[str, Any]:
    """Load a triage JSON record from a file path or stdin.

    Consumes exactly the shape emitted by "triage run --json", including from
    stdin when source is "-".

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


def _location(triage: dict[str, Any]) -> str:
    """Build a human location phrase from property and unit, no PII beyond unit.

    Args:
        triage: The triage record.

    Returns:
        A phrase such as "The Meridian unit 312" or "the property".
    """
    property_name = triage.get("property_name")
    unit = triage.get("unit")
    if property_name and unit:
        return f"{property_name} unit {unit}"
    if property_name:
        return property_name
    return "the property"


def build_acknowledgment(triage: dict[str, Any]) -> str:
    """Build a brief, professional, first person tenant acknowledgment.

    Args:
        triage: The triage record with property_name, unit, and issue_summary.

    Returns:
        The acknowledgment body. Contains no em dashes.
    """
    location = _location(triage)
    issue = (triage.get("issue_summary") or "the issue you reported").strip()
    return (
        "Hi,\n\n"
        f"Thank you for reaching out about {location}. I have received your "
        f"report regarding {issue}, and I am arranging for it to be addressed. "
        "I will follow up shortly with the next steps.\n\n"
        "Best,\n"
        "Stark\n"
        "Asantico"
    )


def _append_sent_log(triage: dict[str, Any], body: str) -> None:
    """Append one local sent record. No real message is sent.

    The recorded entry is location and issue only, not tenant contact PII.

    Args:
        triage: The triage record.
        body: The acknowledgment body that was approved.
    """
    ensure_config_dir()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "sent",
        "property_name": triage.get("property_name"),
        "unit": triage.get("unit"),
        "issue_summary": triage.get("issue_summary"),
        "characters": len(body),
    }
    with open(get_sent_log_path(), "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


@app.command("new")
def new_draft(
    triage_json: Annotated[
        str,
        typer.Argument(
            help="Path to a triage JSON record, or - to read JSON from stdin",
        ),
    ],
    approve: Annotated[
        bool,
        typer.Option(
            "--approve",
            help="Mark the draft sent and record it locally in sent_log.jsonl",
        ),
    ] = False,
) -> None:
    """Produce a tenant acknowledgment from a triage record.

    Reads the JSON shape emitted by "triage run --json" from a file or stdin.
    Without --approve the output is a DRAFT and nothing is recorded as sent.
    With --approve the acknowledgment is marked sent and appended to the local
    sent_log.jsonl. No real email or SMS is sent in this build.
    """
    triage = _load_triage(triage_json)
    body = build_acknowledgment(triage)

    if approve:
        _append_sent_log(triage, body)
        console.print(
            Panel(
                body,
                title="SENT (recorded locally, no real message sent)",
                border_style="green",
            )
        )
        console.print(f"[green]Recorded in:[/green] {get_sent_log_path()}")
    else:
        console.print(
            Panel(
                body,
                title="DRAFT (not sent)",
                border_style="yellow",
            )
        )
        console.print(
            "This is a DRAFT. Nothing has been sent. "
            "Re-run with --approve to record it as sent."
        )
