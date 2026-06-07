"""Tests for the triage CLI command (Phase 4)."""

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
            app, ["triage", "-"], input=_raw_text("wo_03_routine_appliance.json")
        )
        assert result.exit_code == 0
        assert "Triage result" in result.stdout
        assert "routine" in result.stdout
        assert "appliance" in result.stdout
        assert "HUMAN REVIEW" not in result.stdout

    def test_emergency_prints_human_review_banner(self, mock_config_dir: Path) -> None:
        """An emergency request prints the HUMAN REVIEW banner."""
        result = runner.invoke(
            app, ["triage", "-"], input=_raw_text("wo_01_emergency_plumbing.json")
        )
        assert "emergency" in result.stdout
        assert "HUMAN REVIEW" in result.stdout

    def test_ambiguous_prints_human_review_banner(self, mock_config_dir: Path) -> None:
        """A low-confidence request also triggers the HUMAN REVIEW banner."""
        result = runner.invoke(
            app, ["triage", "-"], input=_raw_text("wo_07_ambiguous_noise.json")
        )
        assert "HUMAN REVIEW" in result.stdout

    def test_reads_from_file(self, mock_config_dir: Path, tmp_path: Path) -> None:
        """The command reads raw text from a file path argument."""
        request_file = tmp_path / "request.txt"
        request_file.write_text(
            _raw_text("wo_03_routine_appliance.json"), encoding="utf-8"
        )
        result = runner.invoke(app, ["triage", str(request_file)])
        assert result.exit_code == 0
        assert "routine" in result.stdout

    def test_missing_file_errors(self, mock_config_dir: Path) -> None:
        """A nonexistent file path exits with an error."""
        result = runner.invoke(app, ["triage", "/no/such/request.txt"])
        assert result.exit_code == 1
        output = result.stdout + (result.stderr or "")
        assert "File not found" in output

    def test_empty_input_errors(self, mock_config_dir: Path) -> None:
        """Empty input is rejected before any triage call."""
        result = runner.invoke(app, ["triage", "-"], input="   \n")
        assert result.exit_code == 1
        output = result.stdout + (result.stderr or "")
        assert "No input text provided" in output


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
            app, ["triage", "-"], input=_raw_text(fixture_name) + "\n"
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
        result = runner.invoke(app, ["triage", str(request_file)])
        output = result.stdout + (result.stderr or "")
        assert "No recorded triage response" not in output
        assert result.exit_code == 0
