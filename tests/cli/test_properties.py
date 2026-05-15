"""Tests for properties CLI commands."""

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


class TestPropertiesCommands:
    """Tests for properties commands."""

    def test_list_properties_shows_defaults(self, mock_config_dir: Path) -> None:
        """properties list shows default properties."""
        result = runner.invoke(app, ["properties", "list"])

        assert result.exit_code == 0
        assert "Garden" in result.stdout
        assert "The Meridian" in result.stdout
        assert "Gilman's Fairway" in result.stdout

    def test_add_property(self, mock_config_dir: Path) -> None:
        """properties add adds a new property."""
        result = runner.invoke(app, ["properties", "add", "Test Property"])

        assert result.exit_code == 0
        assert "Added property:" in result.stdout
        assert "Test Property" in result.stdout

        # Verify it appears in list
        list_result = runner.invoke(app, ["properties", "list"])
        assert "Test Property" in list_result.stdout

    def test_add_property_with_address(self, mock_config_dir: Path) -> None:
        """properties add with --address includes address."""
        result = runner.invoke(app, [
            "properties", "add", "New Building",
            "--address", "123 Main St",
        ])

        assert result.exit_code == 0
        assert "Added property:" in result.stdout

    def test_add_duplicate_property_error(self, mock_config_dir: Path) -> None:
        """properties add with existing name shows error."""
        # First add succeeds
        runner.invoke(app, ["properties", "add", "Duplicate"])

        # Second add fails
        result = runner.invoke(app, ["properties", "add", "Duplicate"], catch_exceptions=False)

        assert result.exit_code == 1
        output = result.stdout + (result.stderr or "")
        assert "already exists" in output

    def test_remove_property(self, mock_config_dir: Path) -> None:
        """properties remove removes a property."""
        # Add a property first
        runner.invoke(app, ["properties", "add", "To Remove"])

        # Remove it
        result = runner.invoke(app, ["properties", "remove", "To Remove"])

        assert result.exit_code == 0
        assert "Removed property:" in result.stdout

        # Verify it's gone
        list_result = runner.invoke(app, ["properties", "list"])
        assert "To Remove" not in list_result.stdout

    def test_remove_nonexistent_property_error(self, mock_config_dir: Path) -> None:
        """properties remove with nonexistent name shows error."""
        result = runner.invoke(app, ["properties", "remove", "Nonexistent"], catch_exceptions=False)

        assert result.exit_code == 1
        output = result.stdout + (result.stderr or "")
        assert "not found" in output
