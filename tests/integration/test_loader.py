"""Integration tests for JSON line item loader."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from asantico_cli.infra.loader import LoaderError, load_line_items, load_notes


class TestLoadLineItems:
    """Tests for load_line_items function."""

    def test_load_valid_json_with_line_items_key(self, tmp_path: Path) -> None:
        """Valid JSON with line_items key loads correctly."""
        json_file = tmp_path / "items.json"
        json_file.write_text(json.dumps({
            "line_items": [
                {
                    "description": "Replace faucet",
                    "quantity": 1,
                    "unit": "each",
                    "unit_price": 150.00,
                }
            ]
        }))

        items = load_line_items(json_file)

        assert len(items) == 1
        assert items[0].description == "Replace faucet"
        assert items[0].quantity == Decimal("1")
        assert items[0].unit == "each"
        assert items[0].unit_price == Decimal("150.00")

    def test_load_valid_json_array_format(self, tmp_path: Path) -> None:
        """Valid JSON as plain array loads correctly."""
        json_file = tmp_path / "items.json"
        json_file.write_text(json.dumps([
            {
                "description": "Pressure washing",
                "quantity": 2.5,
                "unit": "hr",
                "unit_price": 65.00,
            }
        ]))

        items = load_line_items(json_file)

        assert len(items) == 1
        assert items[0].quantity == Decimal("2.5")

    def test_missing_file_error(self, tmp_path: Path) -> None:
        """Missing file raises LoaderError."""
        json_file = tmp_path / "nonexistent.json"

        with pytest.raises(LoaderError, match="File not found"):
            load_line_items(json_file)

    def test_malformed_json_error(self, tmp_path: Path) -> None:
        """Malformed JSON raises LoaderError."""
        json_file = tmp_path / "items.json"
        json_file.write_text("{ invalid json }")

        with pytest.raises(LoaderError, match="Invalid JSON"):
            load_line_items(json_file)

    def test_missing_required_field_error(self, tmp_path: Path) -> None:
        """Missing required field raises LoaderError."""
        json_file = tmp_path / "items.json"
        json_file.write_text(json.dumps([
            {
                "description": "Test",
                "quantity": 1,
                # missing unit and unit_price
            }
        ]))

        with pytest.raises(LoaderError, match="missing required field"):
            load_line_items(json_file)

    def test_invalid_unit_error(self, tmp_path: Path) -> None:
        """Invalid unit raises LoaderError."""
        json_file = tmp_path / "items.json"
        json_file.write_text(json.dumps([
            {
                "description": "Test",
                "quantity": 1,
                "unit": "pieces",
                "unit_price": 100,
            }
        ]))

        with pytest.raises(LoaderError, match="hr, each, or flat"):
            load_line_items(json_file)

    def test_negative_quantity_error(self, tmp_path: Path) -> None:
        """Negative quantity raises LoaderError."""
        json_file = tmp_path / "items.json"
        json_file.write_text(json.dumps([
            {
                "description": "Test",
                "quantity": -1,
                "unit": "each",
                "unit_price": 100,
            }
        ]))

        with pytest.raises(LoaderError, match="positive"):
            load_line_items(json_file)

    def test_em_dash_in_description_error(self, tmp_path: Path) -> None:
        """Em dash in description raises LoaderError."""
        json_file = tmp_path / "items.json"
        json_file.write_text(json.dumps([
            {
                "description": "Test \u2014 item",
                "quantity": 1,
                "unit": "each",
                "unit_price": 100,
            }
        ]))

        with pytest.raises(LoaderError, match="em dash"):
            load_line_items(json_file)

    def test_empty_line_items_error(self, tmp_path: Path) -> None:
        """Empty line items array raises LoaderError."""
        json_file = tmp_path / "items.json"
        json_file.write_text(json.dumps({"line_items": []}))

        with pytest.raises(LoaderError, match="at least one line item"):
            load_line_items(json_file)


class TestLoadNotes:
    """Tests for load_notes function."""

    def test_load_notes_present(self, tmp_path: Path) -> None:
        """Notes are loaded when present."""
        json_file = tmp_path / "items.json"
        json_file.write_text(json.dumps({
            "line_items": [],
            "notes": "Test notes",
        }))

        notes = load_notes(json_file)
        assert notes == "Test notes"

    def test_load_notes_absent(self, tmp_path: Path) -> None:
        """None returned when notes are absent."""
        json_file = tmp_path / "items.json"
        json_file.write_text(json.dumps([]))

        notes = load_notes(json_file)
        assert notes is None

    def test_load_notes_file_missing(self, tmp_path: Path) -> None:
        """None returned when file does not exist."""
        json_file = tmp_path / "nonexistent.json"

        notes = load_notes(json_file)
        assert notes is None
