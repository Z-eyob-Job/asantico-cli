"""Tests for estimate CLI commands."""

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
            "description": "Pressure washing",
            "quantity": 2,
            "unit": "hr",
            "unit_price": 65.00,
        }
    ]))
    return items_file


class TestEstimateNew:
    """Tests for estimate new command."""

    def test_estimate_from_file_success(
        self,
        mock_config_dir: Path,
        valid_items_file: Path,
        tmp_path: Path,
    ) -> None:
        """estimate new with valid file creates PDF."""
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "estimate", "new",
            "--from-file", str(valid_items_file),
            "--property", "Garden",
            "--output", str(output_dir),
        ])

        assert result.exit_code == 0
        assert "Created:" in result.stdout

        # Verify PDF was created
        pdf_files = list(output_dir.glob("*.pdf"))
        assert len(pdf_files) == 1
        assert "estimate_garden" in pdf_files[0].name

    def test_estimate_filename_has_estimate_prefix(
        self,
        mock_config_dir: Path,
        valid_items_file: Path,
        tmp_path: Path,
    ) -> None:
        """estimate PDF filename starts with 'estimate_'."""
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "estimate", "new",
            "--from-file", str(valid_items_file),
            "--property", "Portal",
            "--output", str(output_dir),
        ])

        assert result.exit_code == 0

        pdf_files = list(output_dir.glob("*.pdf"))
        assert len(pdf_files) == 1
        assert pdf_files[0].name.startswith("estimate_")
