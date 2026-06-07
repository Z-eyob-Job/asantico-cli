"""Tests for the draft-reply CLI command and approval gate (Phase 5, noun-verb)."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from asantico_cli.cli.app import app

runner = CliRunner()

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "workorders"


@pytest.fixture
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the config dir (sent log) to a temporary location."""
    config_dir = tmp_path / ".asantico"
    monkeypatch.setenv("ASANTICO_CONFIG_DIR", str(config_dir))
    return config_dir


@pytest.fixture
def triage_file(tmp_path: Path) -> Path:
    """Write a representative triage JSON record to disk."""
    path = tmp_path / "triage.json"
    path.write_text(
        json.dumps(
            {
                "urgency": "routine",
                "trade": "appliance",
                "property_name": "Garden",
                "unit": "204",
                "tenant_contact": "tenant",
                "issue_summary": "Dishwasher not draining fully",
                "confidence": {"urgency": 0.92, "trade": 0.9},
                "needs_review": False,
            }
        ),
        encoding="utf-8",
    )
    return path


def _sent_log_lines(config_dir: Path) -> list[str]:
    """Return the non-empty lines currently in sent_log.jsonl (empty if absent)."""
    sent_log = config_dir / "sent_log.jsonl"
    if not sent_log.exists():
        return []
    return [line for line in sent_log.read_text(encoding="utf-8").splitlines() if line.strip()]


class TestDraftReplyWithoutApprove:
    """Tests for the default DRAFT behavior."""

    def test_output_marked_draft(self, mock_config_dir: Path, triage_file: Path) -> None:
        """Without --approve the output is labeled DRAFT."""
        result = runner.invoke(app, ["draft-reply", "new", str(triage_file)])
        assert result.exit_code == 0
        assert "DRAFT" in result.stdout
        assert "Garden unit 204" in result.stdout

    def test_sent_log_untouched(self, mock_config_dir: Path, triage_file: Path) -> None:
        """Without --approve the sent log gains no entry."""
        before = _sent_log_lines(mock_config_dir)
        result = runner.invoke(app, ["draft-reply", "new", str(triage_file)])
        assert result.exit_code == 0
        after = _sent_log_lines(mock_config_dir)
        assert before == []
        assert after == []
        assert not (mock_config_dir / "sent_log.jsonl").exists()

    def test_no_em_dash_in_draft(self, mock_config_dir: Path, triage_file: Path) -> None:
        """The draft body contains no em dash."""
        result = runner.invoke(app, ["draft-reply", "new", str(triage_file)])
        assert "\u2014" not in result.stdout


class TestDraftReplyWithApprove:
    """Tests for the approved send-record behavior."""

    def test_sent_entry_written(self, mock_config_dir: Path, triage_file: Path) -> None:
        """With --approve exactly one sent entry is appended to the local log."""
        before = _sent_log_lines(mock_config_dir)
        result = runner.invoke(app, ["draft-reply", "new", str(triage_file), "--approve"])
        assert result.exit_code == 0
        after = _sent_log_lines(mock_config_dir)
        assert len(after) == len(before) + 1

        entry = json.loads(after[-1])
        assert entry["status"] == "sent"
        assert entry["property_name"] == "Garden"
        assert entry["unit"] == "204"

    def test_approve_appends_not_overwrites(
        self, mock_config_dir: Path, triage_file: Path
    ) -> None:
        """Repeated approvals append, they do not overwrite prior entries."""
        runner.invoke(app, ["draft-reply", "new", str(triage_file), "--approve"])
        runner.invoke(app, ["draft-reply", "new", str(triage_file), "--approve"])
        assert len(_sent_log_lines(mock_config_dir)) == 2

    def test_sent_log_records_no_contact_pii(
        self, mock_config_dir: Path, tmp_path: Path
    ) -> None:
        """The sent log records location and issue only, not tenant contact."""
        path = tmp_path / "pii_triage.json"
        path.write_text(
            json.dumps(
                {
                    "urgency": "routine",
                    "trade": "appliance",
                    "property_name": "Clark Roadhouse",
                    "unit": "417",
                    "tenant_contact": "James O'Brien, (206) 555-0188",
                    "issue_summary": "Clothes dryer will not heat",
                }
            ),
            encoding="utf-8",
        )
        runner.invoke(app, ["draft-reply", "new", str(path), "--approve"])
        contents = (mock_config_dir / "sent_log.jsonl").read_text(encoding="utf-8")
        assert "James O'Brien" not in contents
        assert "(206) 555-0188" not in contents


class TestDraftReplyFromStdin:
    """Tests that draft-reply consumes the triage run --json shape from stdin."""

    def test_consumes_triage_json_from_stdin(self, mock_config_dir: Path) -> None:
        """draft-reply new - reads the JSON shape emitted by triage run --json."""
        triage_payload = json.dumps(
            {
                "urgency": "routine",
                "trade": "appliance",
                "property_name": "Garden",
                "unit": "204",
                "tenant_contact": None,
                "issue_summary": "Dishwasher not draining fully",
                "confidence": {"urgency": 0.92, "trade": 0.9},
                "needs_review": False,
            }
        )
        result = runner.invoke(app, ["draft-reply", "new", "-"], input=triage_payload)
        assert result.exit_code == 0
        assert "DRAFT" in result.stdout
        assert "Garden unit 204" in result.stdout

    def test_pipeline_handoff_from_triage_run(self, mock_config_dir: Path) -> None:
        """The triage run --json output feeds straight into draft-reply new -."""
        raw_text = json.loads(
            (FIXTURE_DIR / "wo_03_routine_appliance.json").read_text(encoding="utf-8")
        )["raw_text"]
        triage_result = runner.invoke(
            app, ["triage", "run", "-", "--json"], input=raw_text
        )
        assert triage_result.exit_code == 0
        draft_result = runner.invoke(
            app, ["draft-reply", "new", "-"], input=triage_result.stdout
        )
        assert draft_result.exit_code == 0
        assert "DRAFT" in draft_result.stdout
