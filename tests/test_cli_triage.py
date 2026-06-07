"""Tests for the triage CLI command (Phase 4, noun-verb command path)."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from asantico_cli.cli.app import app

runner = CliRunner()

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "workorders"


@pytest.fixture
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the config dir (audit log) to a temporary location."""
    config_dir = tmp_path / ".asantico"
    monkeypatch.setenv("ASANTICO_CONFIG_DIR", str(config_dir))
    return config_dir


def _raw_text(fixture_name: str) -> str:
    """Read the raw_text field from a work order fixture."""
    return json.loads((FIXTURE_DIR / fixture_name).read_text(encoding="utf-8"))["raw_text"]


class TestTriageCommand:
    """Tests for the triage command."""

    def test_routine_prints_result_and_exits_zero(self, mock_config_dir: Path) -> None:
        """A routine request prints the result table and exits 0, no banner."""
        result = runner.invoke(
            app, ["triage", "run", "-"], input=_raw_text("wo_03_routine_appliance.json")
        )
        assert result.exit_code == 0
        assert "Triage result" in result.stdout
        assert "routine" in result.stdout
        assert "appliance" in result.stdout
        assert "HUMAN REVIEW" not in result.stdout

    def test_emergency_prints_human_review_banner(self, mock_config_dir: Path) -> None:
        """An emergency request prints the HUMAN REVIEW banner."""
        result = runner.invoke(
            app, ["triage", "run", "-"], input=_raw_text("wo_01_emergency_plumbing.json")
        )
        assert "emergency" in result.stdout
        assert "HUMAN REVIEW" in result.stdout

    def test_ambiguous_prints_human_review_banner(self, mock_config_dir: Path) -> None:
        """A low-confidence request also triggers the HUMAN REVIEW banner."""
        result = runner.invoke(
            app, ["triage", "run", "-"], input=_raw_text("wo_07_ambiguous_noise.json")
        )
        assert "HUMAN REVIEW" in result.stdout

    def test_reads_from_file(self, mock_config_dir: Path, tmp_path: Path) -> None:
        """The command reads raw text from a file path argument."""
        request_file = tmp_path / "request.txt"
        request_file.write_text(
            _raw_text("wo_03_routine_appliance.json"), encoding="utf-8"
        )
        result = runner.invoke(app, ["triage", "run", str(request_file)])
        assert result.exit_code == 0
        assert "routine" in result.stdout

    def test_reads_workorder_json_file(self, mock_config_dir: Path) -> None:
        """A work order JSON file has its raw_text extracted, no cache miss."""
        result = runner.invoke(
            app,
            ["triage", "run", str(FIXTURE_DIR / "wo_03_routine_appliance.json")],
        )
        output = result.stdout + (result.stderr or "")
        assert "No recorded triage response" not in output
        assert result.exit_code == 0
        assert "routine" in result.stdout

    def test_missing_file_errors(self, mock_config_dir: Path) -> None:
        """A nonexistent file path exits with an error."""
        result = runner.invoke(app, ["triage", "run", "/no/such/request.txt"])
        assert result.exit_code == 1
        output = result.stdout + (result.stderr or "")
        assert "File not found" in output

    def test_empty_input_errors(self, mock_config_dir: Path) -> None:
        """Empty input is rejected before any triage call."""
        result = runner.invoke(app, ["triage", "run", "-"], input="   \n")
        assert result.exit_code == 1
        output = result.stdout + (result.stderr or "")
        assert "No input text provided" in output

    def test_json_output_is_pure_json(self, mock_config_dir: Path) -> None:
        """--json prints a parseable TriageResult shape to stdout."""
        result = runner.invoke(
            app,
            ["triage", "run", "-", "--json"],
            input=_raw_text("wo_03_routine_appliance.json"),
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["urgency"] == "routine"
        assert payload["trade"] == "appliance"
        assert set(payload) >= {
            "urgency",
            "trade",
            "property_name",
            "unit",
            "tenant_contact",
            "issue_summary",
            "confidence",
            "needs_review",
        }

    def test_json_output_emergency_still_emits_json(self, mock_config_dir: Path) -> None:
        """--json keeps stdout pure JSON even when the case needs review."""
        result = runner.invoke(
            app,
            ["triage", "run", "-", "--json"],
            input=_raw_text("wo_01_emergency_plumbing.json"),
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["needs_review"] is True


class TestTriageCacheKeyRoundTrip:
    """Guards against cache-key drift between build time and the real CLI path.

    A shell pipe to stdin appends a trailing newline. These tests drive the
    actual CLI input path with that newline and assert there is no cache miss,
    so the offline key must survive normalization.
    """

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "wo_01_emergency_plumbing.json",
            "wo_07_ambiguous_noise.json",
            "wo_09_heavy_pii_appliance.json",
        ],
    )
    def test_stdin_with_trailing_newline_hits_cache(
        self, mock_config_dir: Path, fixture_name: str
    ) -> None:
        """Piping exact raw_text plus a trailing newline must not miss the cache."""
        result = runner.invoke(
            app, ["triage", "run", "-"], input=_raw_text(fixture_name) + "\n"
        )
        output = result.stdout + (result.stderr or "")
        assert "No recorded triage response" not in output
        assert result.exit_code == 0
        assert "Triage result" in result.stdout

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "wo_01_emergency_plumbing.json",
            "wo_07_ambiguous_noise.json",
            "wo_09_heavy_pii_appliance.json",
        ],
    )
    def test_file_with_trailing_newline_hits_cache(
        self, mock_config_dir: Path, tmp_path: Path, fixture_name: str
    ) -> None:
        """A file whose content ends in a newline must not miss the cache."""
        request_file = tmp_path / "request.txt"
        request_file.write_text(_raw_text(fixture_name) + "\n", encoding="utf-8")
        result = runner.invoke(app, ["triage", "run", str(request_file)])
        output = result.stdout + (result.stderr or "")
        assert "No recorded triage response" not in output
        assert result.exit_code == 0
