"""Tests for estimate --from-triage (Phase 6).

Verifies the triage to estimate mapping reuses the existing tax engine: totals
match a direct compute_totals call to the cent, and the labor-only line carries
Seattle tax.
"""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from typer.testing import CliRunner

from asantico_cli.cli.app import app
from asantico_cli.cli.estimate import line_items_from_triage
from asantico_cli.domain.models import LineItem
from asantico_cli.domain.tax import compute_totals

runner = CliRunner()

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "workorders"

TRIAGE_RECORD = {
    "urgency": "routine",
    "trade": "appliance",
    "property_name": "Garden",
    "unit": "204",
    "tenant_contact": None,
    "issue_summary": "Dishwasher not draining fully",
    "confidence": {"urgency": 0.92, "trade": 0.9},
    "needs_review": False,
}


@pytest.fixture
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the config dir (counters) to a temporary location."""
    config_dir = tmp_path / ".asantico"
    monkeypatch.setenv("ASANTICO_CONFIG_DIR", str(config_dir))
    return config_dir


class TestTriageMapping:
    """Tests for the pure line_items_from_triage mapping."""

    def test_totals_match_existing_engine_to_the_cent(self) -> None:
        """compute_totals on mapped items equals a direct engine call, to the cent."""
        labor_rate = Decimal("65.00")
        mapped = line_items_from_triage(TRIAGE_RECORD, labor_rate)

        expected = [
            LineItem(
                description="Dishwasher not draining fully",
                quantity=Decimal("1"),
                unit="hr",
                unit_price=Decimal("65.00"),
            )
        ]
        assert compute_totals(mapped) == compute_totals(expected)

        subtotal, total_tax, grand_total = compute_totals(mapped)
        cents = Decimal("0.01")
        assert subtotal.quantize(cents) == Decimal("65.00")
        # 65.00 * 0.1055 = 6.8575 -> 6.86 to the cent
        assert total_tax.quantize(cents) == Decimal("6.86")
        assert grand_total.quantize(cents) == Decimal("71.86")

    def test_labor_only_line_is_taxed(self) -> None:
        """The mapped labor-only line carries Seattle tax."""
        mapped = line_items_from_triage(TRIAGE_RECORD, Decimal("65.00"))
        assert len(mapped) == 1
        labor = mapped[0]
        assert labor.unit == "hr"
        assert labor.line_tax == Decimal("65.00") * Decimal("0.1055")
        assert labor.line_tax > 0

    def test_falls_back_to_trade_when_no_summary(self) -> None:
        """An empty issue summary falls back to a trade-based description."""
        record = {**TRIAGE_RECORD, "issue_summary": ""}
        mapped = line_items_from_triage(record, Decimal("65.00"))
        assert mapped[0].description == "appliance service"


class TestEstimateFromTriageCli:
    """Tests for the estimate new --from-triage entry path."""

    def test_from_triage_file_creates_pdf(
        self, mock_config_dir: Path, tmp_path: Path
    ) -> None:
        """--from-triage with a file produces an estimate PDF and totals line."""
        triage_file = tmp_path / "triage.json"
        triage_file.write_text(json.dumps(TRIAGE_RECORD), encoding="utf-8")
        output_dir = tmp_path / "output"

        result = runner.invoke(
            app,
            [
                "estimate",
                "new",
                "--from-triage",
                str(triage_file),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0, result.stdout + (result.stderr or "")
        assert "Created:" in result.stdout
        assert "tax $6.86" in result.stdout
        pdfs = list(output_dir.glob("*.pdf"))
        assert len(pdfs) == 1
        assert "estimate_garden" in pdfs[0].name

    def test_from_triage_stdin_creates_pdf(
        self, mock_config_dir: Path, tmp_path: Path
    ) -> None:
        """--from-triage - reads the triage JSON shape from stdin."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            ["estimate", "new", "--from-triage", "-", "--output", str(output_dir)],
            input=json.dumps(TRIAGE_RECORD),
        )
        assert result.exit_code == 0, result.stdout + (result.stderr or "")
        assert len(list(output_dir.glob("*.pdf"))) == 1

    def test_pipeline_from_triage_run(
        self, mock_config_dir: Path, tmp_path: Path
    ) -> None:
        """triage run --json output feeds straight into estimate --from-triage -."""
        raw_text = json.loads(
            (FIXTURE_DIR / "wo_03_routine_appliance.json").read_text(encoding="utf-8")
        )["raw_text"]
        triage_result = runner.invoke(
            app, ["triage", "run", "-", "--json"], input=raw_text
        )
        assert triage_result.exit_code == 0

        output_dir = tmp_path / "output"
        estimate_result = runner.invoke(
            app,
            ["estimate", "new", "--from-triage", "-", "--output", str(output_dir)],
            input=triage_result.stdout,
        )
        assert estimate_result.exit_code == 0, estimate_result.stdout
        assert len(list(output_dir.glob("*.pdf"))) == 1
