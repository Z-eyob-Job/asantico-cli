"""Tests for invoice CLI commands."""

import json
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


@pytest.fixture
def valid_items_file(tmp_path: Path) -> Path:
    """Create a valid line items JSON file."""
    items_file = tmp_path / "items.json"
    items_file.write_text(json.dumps([
        {
            "description": "Replace faucet",
            "quantity": 1,
            "unit": "each",
            "unit_price": 150.00,
        }
    ]))
    return items_file


class TestInvoiceNew:
    """Tests for invoice new command."""

    def test_invoice_from_file_success(
        self,
        mock_config_dir: Path,
        valid_items_file: Path,
        tmp_path: Path,
    ) -> None:
        """invoice new with valid file creates PDF."""
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "invoice", "new",
            "--from-file", str(valid_items_file),
            "--property", "The Meridian",
            "--output", str(output_dir),
        ])

        assert result.exit_code == 0
        assert "Created:" in result.stdout

        # Verify PDF was created
        pdf_files = list(output_dir.glob("*.pdf"))
        assert len(pdf_files) == 1
        assert "invoice_the-meridian" in pdf_files[0].name

    def test_invoice_missing_property_error(
        self,
        mock_config_dir: Path,
        valid_items_file: Path,
    ) -> None:
        """invoice new without --property shows error."""
        result = runner.invoke(app, [
            "invoice", "new",
            "--from-file", str(valid_items_file),
        ], catch_exceptions=False)

        assert result.exit_code == 1
        # Error goes to stderr, check combined output
        output = result.stdout + (result.stderr or "")
        assert "--property is required" in output or "property" in output.lower()

    def test_invoice_missing_from_file_error(
        self,
        mock_config_dir: Path,
    ) -> None:
        """invoice new without --from-file shows error."""
        result = runner.invoke(app, [
            "invoice", "new",
            "--property", "Test",
        ], catch_exceptions=False)

        assert result.exit_code == 1
        # Error goes to stderr, check combined output
        output = result.stdout + (result.stderr or "")
        assert "--from-file is required" in output or "from-file" in output.lower()

    def test_invoice_invalid_json_error(
        self,
        mock_config_dir: Path,
        tmp_path: Path,
    ) -> None:
        """invoice new with invalid JSON shows error."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ not valid json }")

        result = runner.invoke(app, [
            "invoice", "new",
            "--from-file", str(invalid_file),
            "--property", "Test",
        ], catch_exceptions=False)

        assert result.exit_code == 1
        # Error goes to stderr, check combined output
        output = result.stdout + (result.stderr or "")
        assert "Invalid JSON" in output or "invalid" in output.lower()
