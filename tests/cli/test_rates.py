"""Tests for rates CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from asantico_cli.cli.app import app

runner = CliRunner()


@pytest.fixture
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a temporary config directory for testing."""
    config_dir = tmp_path / ".asantico"
    monkeypatch.setenv("ASANTICO_CONFIG_DIR", str(config_dir))
    return config_dir


class TestRatesCommands:
    """Tests for rates commands."""

    def test_list_rates_shows_defaults(self, mock_config_dir: Path) -> None:
        """rates list shows default rates."""
        result = runner.invoke(app, ["rates", "list"])

        assert result.exit_code == 0
        assert "labor" in result.stdout
        assert "$65.00" in result.stdout
        assert "materials" in result.stdout
        assert "$0.00" in result.stdout

    def test_set_rate_labor(self, mock_config_dir: Path) -> None:
        """rates set updates labor rate."""
        result = runner.invoke(app, ["rates", "set", "labor", "75.00"])

        assert result.exit_code == 0
        assert "Set labor rate to" in result.stdout
        assert "$75.00" in result.stdout

        # Verify it persists
        list_result = runner.invoke(app, ["rates", "list"])
        assert "$75.00" in list_result.stdout

    def test_set_rate_materials(self, mock_config_dir: Path) -> None:
        """rates set updates materials rate."""
        result = runner.invoke(app, ["rates", "set", "materials", "10.00"])

        assert result.exit_code == 0
        assert "Set materials rate to" in result.stdout
        assert "$10.00" in result.stdout

    def test_set_invalid_rate_type_error(self, mock_config_dir: Path) -> None:
        """rates set with invalid type shows error."""
        result = runner.invoke(app, ["rates", "set", "invalid", "50.00"], catch_exceptions=False)

        assert result.exit_code == 1
        output = result.stdout + (result.stderr or "")
        assert "Invalid rate type" in output

    def test_set_negative_rate_error(self, mock_config_dir: Path) -> None:
        """rates set with negative value shows error."""
        # Use -- to separate options from arguments, so -10.00 is treated as argument
        result = runner.invoke(app, ["rates", "set", "labor", "--", "-10.00"], catch_exceptions=False)

        assert result.exit_code == 1
        output = result.stdout + (result.stderr or "")
        assert "cannot be negative" in output
