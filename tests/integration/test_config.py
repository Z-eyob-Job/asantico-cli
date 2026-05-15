"""Integration tests for config file management."""

import json
import os
from decimal import Decimal
from pathlib import Path

import pytest

from asantico_cli.domain.models import Property
from asantico_cli.infra.config import (
    ensure_config_dir,
    get_config_dir,
    increment_counter,
    load_counters,
    load_properties,
    load_rates,
    save_properties,
    save_rates,
)


@pytest.fixture
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a temporary config directory for testing."""
    config_dir = tmp_path / ".asantico"
    monkeypatch.setenv("ASANTICO_CONFIG_DIR", str(config_dir))
    return config_dir


class TestEnsureConfigDir:
    """Tests for ensure_config_dir function."""

    def test_creates_directory(self, mock_config_dir: Path) -> None:
        """ensure_config_dir creates the directory if it does not exist."""
        assert not mock_config_dir.exists()
        ensure_config_dir()
        assert mock_config_dir.exists()
        assert mock_config_dir.is_dir()

    def test_idempotent(self, mock_config_dir: Path) -> None:
        """ensure_config_dir can be called multiple times safely."""
        ensure_config_dir()
        ensure_config_dir()
        assert mock_config_dir.exists()


class TestProperties:
    """Tests for properties config functions."""

    def test_load_properties_returns_defaults(self, mock_config_dir: Path) -> None:
        """load_properties returns default properties if file does not exist."""
        properties = load_properties()
        assert len(properties) == 9
        names = [p.name for p in properties]
        assert "Garden" in names
        assert "The Meridian" in names
        assert "Gilman's Fairway" in names

    def test_save_and_load_properties(self, mock_config_dir: Path) -> None:
        """Properties can be saved and loaded."""
        test_properties = [
            Property(name="Test Property 1", address="123 Test St"),
            Property(name="Test Property 2"),
        ]
        save_properties(test_properties)

        loaded = load_properties()
        assert len(loaded) == 2
        assert loaded[0].name == "Test Property 1"
        assert loaded[0].address == "123 Test St"
        assert loaded[1].name == "Test Property 2"
        assert loaded[1].address is None

    def test_properties_file_format(self, mock_config_dir: Path) -> None:
        """Properties are saved as JSON with expected structure."""
        test_properties = [Property(name="Test", address="123 Main St")]
        save_properties(test_properties)

        properties_file = mock_config_dir / "properties.json"
        with open(properties_file) as f:
            data = json.load(f)

        assert data == [{"name": "Test", "address": "123 Main St"}]


class TestRates:
    """Tests for rates config functions."""

    def test_load_rates_returns_defaults(self, mock_config_dir: Path) -> None:
        """load_rates returns default rates if file does not exist."""
        rates = load_rates()
        assert rates["labor"] == Decimal("65.00")
        assert rates["materials"] == Decimal("0.00")

    def test_save_and_load_rates(self, mock_config_dir: Path) -> None:
        """Rates can be saved and loaded."""
        test_rates = {
            "labor": Decimal("75.00"),
            "materials": Decimal("10.00"),
        }
        save_rates(test_rates)

        loaded = load_rates()
        assert loaded["labor"] == Decimal("75.00")
        assert loaded["materials"] == Decimal("10.00")


class TestCounters:
    """Tests for document counter functions."""

    def test_load_counters_returns_zeros(self, mock_config_dir: Path) -> None:
        """load_counters returns zeros if file does not exist."""
        counters = load_counters()
        assert counters["invoice"] == 0
        assert counters["estimate"] == 0

    def test_increment_counter_invoice(self, mock_config_dir: Path) -> None:
        """increment_counter returns formatted invoice number."""
        doc_num = increment_counter("invoice")
        assert doc_num == "INV-0001"

        doc_num = increment_counter("invoice")
        assert doc_num == "INV-0002"

    def test_increment_counter_estimate(self, mock_config_dir: Path) -> None:
        """increment_counter returns formatted estimate number."""
        doc_num = increment_counter("estimate")
        assert doc_num == "EST-0001"

        doc_num = increment_counter("estimate")
        assert doc_num == "EST-0002"

    def test_counters_persist(self, mock_config_dir: Path) -> None:
        """Counter values persist across load calls."""
        increment_counter("invoice")
        increment_counter("invoice")
        increment_counter("estimate")

        counters = load_counters()
        assert counters["invoice"] == 2
        assert counters["estimate"] == 1
