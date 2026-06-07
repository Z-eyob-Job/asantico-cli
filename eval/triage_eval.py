"""Offline triage evaluation harness.

Runs every labeled work order fixture through offline triage (no API key) and
compares predicted urgency and trade to the gold labels. Reports urgency and
trade accuracy and the key responsible-AI invariant from SPEC section 8: every
emergency must escalate to human review, with zero silent auto-progression.

Run with: python eval/triage_eval.py
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table

from asantico_cli.infra.llm import triage_request

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "workorders"


@dataclass
class FixtureRow:
    """A single fixture's gold labels and predictions."""

    fixture_id: str
    gold_urgency: str
    pred_urgency: str
    gold_trade: str
    pred_trade: str
    needs_review: bool

    @property
    def urgency_ok(self) -> bool:
        """True if predicted urgency matches gold."""
        return self.gold_urgency == self.pred_urgency

    @property
    def trade_ok(self) -> bool:
        """True if predicted trade matches gold."""
        return self.gold_trade == self.pred_trade

    @property
    def is_emergency(self) -> bool:
        """True if the gold urgency is emergency."""
        return self.gold_urgency == "emergency"

    @property
    def missed_escalation(self) -> bool:
        """True if a gold emergency failed to flag for review."""
        return self.is_emergency and not self.needs_review


@dataclass
class EvalReport:
    """Aggregate evaluation results across all fixtures."""

    rows: list[FixtureRow] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total number of fixtures evaluated."""
        return len(self.rows)

    @property
    def urgency_accuracy(self) -> float:
        """Fraction of fixtures with correct urgency."""
        if not self.rows:
            return 0.0
        return sum(r.urgency_ok for r in self.rows) / self.total

    @property
    def trade_accuracy(self) -> float:
        """Fraction of fixtures with correct trade."""
        if not self.rows:
            return 0.0
        return sum(r.trade_ok for r in self.rows) / self.total

    @property
    def emergencies_total(self) -> int:
        """Number of gold emergencies."""
        return sum(r.is_emergency for r in self.rows)

    @property
    def emergencies_escalated(self) -> int:
        """Number of gold emergencies that flagged for review."""
        return sum(r.is_emergency and r.needs_review for r in self.rows)

    @property
    def all_emergencies_escalated(self) -> bool:
        """True if every gold emergency escalated (SPEC section 8)."""
        return not any(r.missed_escalation for r in self.rows)


def load_fixtures(fixture_dir: Path = DEFAULT_FIXTURE_DIR) -> list[dict]:
    """Load all work order fixtures from a directory.

    Args:
        fixture_dir: Directory containing fixture JSON files.

    Returns:
        Parsed fixture records sorted by filename.
    """
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(fixture_dir.glob("*.json"))
    ]


def evaluate(
    fixture_dir: Path = DEFAULT_FIXTURE_DIR, threshold: float = 0.7
) -> EvalReport:
    """Run offline triage over all fixtures and score against gold labels.

    Args:
        fixture_dir: Directory of labeled work order fixtures.
        threshold: Confidence threshold passed to triage.

    Returns:
        An EvalReport with per-fixture rows and aggregate metrics.
    """
    report = EvalReport()
    for fixture in load_fixtures(fixture_dir):
        gold = fixture["gold"]
        result = triage_request(fixture["raw_text"], live=False, threshold=threshold)
        report.rows.append(
            FixtureRow(
                fixture_id=fixture.get("id", "unknown"),
                gold_urgency=gold["urgency"],
                pred_urgency=result.urgency,
                gold_trade=gold["trade"],
                pred_trade=result.trade,
                needs_review=result.needs_review,
            )
        )
    return report


def _mark(ok: bool) -> str:
    """Return a compact pass/fail marker for a cell."""
    return "ok" if ok else "MISS"


def print_report(report: EvalReport, console: Console | None = None) -> None:
    """Print per-fixture rows, an aggregate summary, and a PASS/FAIL line.

    Args:
        report: The evaluation report to render.
        console: Optional Rich console; a default is created if omitted.
    """
    # Force a readable width so values are not truncated when piped. This Rich
    # version only honors an explicit width when height is also provided.
    console = console or Console(width=120, height=40)

    table = Table(title="Offline triage evaluation")
    table.add_column("Fixture", style="cyan", no_wrap=True)
    table.add_column("Gold urg")
    table.add_column("Pred urg")
    table.add_column("Urg")
    table.add_column("Gold trade")
    table.add_column("Pred trade")
    table.add_column("Trade")
    table.add_column("Review")

    for row in report.rows:
        emergency_flag = "yes" if row.needs_review else "no"
        if row.missed_escalation:
            emergency_flag = "MISSED EMERGENCY"
        table.add_row(
            row.fixture_id,
            row.gold_urgency,
            row.pred_urgency,
            _mark(row.urgency_ok),
            row.gold_trade,
            row.pred_trade,
            _mark(row.trade_ok),
            emergency_flag,
        )

    console.print(table)

    summary = Table(title="Summary")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", justify="right")
    summary.add_row("Fixtures", str(report.total))
    summary.add_row("Urgency accuracy", f"{report.urgency_accuracy:.0%}")
    summary.add_row("Trade accuracy", f"{report.trade_accuracy:.0%}")
    summary.add_row(
        "Emergencies escalated",
        f"{report.emergencies_escalated}/{report.emergencies_total}",
    )
    console.print(summary)

    if report.all_emergencies_escalated:
        console.print(
            "[green]PASS[/green] SPEC section 8: 100 percent of emergencies escalated "
            "to human review."
        )
    else:
        console.print(
            "[red]FAIL[/red] SPEC section 8: at least one emergency did not escalate."
        )


def main() -> int:
    """Run the evaluation and print the report.

    Returns:
        Process exit code: 0 if all emergencies escalated, 1 otherwise.
    """
    report = evaluate()
    print_report(report)
    return 0 if report.all_emergencies_escalated else 1


if __name__ == "__main__":
    raise SystemExit(main())
