"""Tests for tax calculation and currency formatting functions."""

from decimal import Decimal

import pytest

from asantico_cli.domain.models import LineItem
from asantico_cli.domain.tax import compute_line_tax, compute_totals, format_currency


class TestComputeLineTax:
    """Tests for compute_line_tax function."""

    def test_basic_tax_calculation(self) -> None:
        """Tax is calculated at 10.55% of line total."""
        line_total = Decimal("100.00")
        tax = compute_line_tax(line_total)
        assert tax == Decimal("10.55")

    def test_labor_tax_calculation(self) -> None:
        """Labor-only items are taxed (Seattle requirement)."""
        # 2.5 hours at $65/hr = $162.50
        line_total = Decimal("162.50")
        tax = compute_line_tax(line_total)
        # 162.50 * 0.1055 = 17.14375
        expected = Decimal("162.50") * Decimal("0.1055")
        assert tax == expected

    def test_rounding_behavior(self) -> None:
        """Tax calculation preserves full precision for internal use."""
        # $33.33 * 0.1055 = 3.516315
        line_total = Decimal("33.33")
        tax = compute_line_tax(line_total)
        expected = Decimal("33.33") * Decimal("0.1055")
        assert tax == expected


class TestComputeTotals:
    """Tests for compute_totals function."""

    def test_single_item_totals(self) -> None:
        """Totals computed correctly for a single line item."""
        item = LineItem(
            description="Replace faucet",
            quantity=Decimal("1"),
            unit="each",
            unit_price=Decimal("200.00"),
        )
        subtotal, total_tax, grand_total = compute_totals([item])
        assert subtotal == Decimal("200.00")
        expected_tax = Decimal("200.00") * Decimal("0.1055")
        assert total_tax == expected_tax
        assert grand_total == subtotal + total_tax

    def test_multiple_items_totals(self) -> None:
        """Totals computed correctly for multiple line items (per-line tax)."""
        items = [
            LineItem(
                description="Light fixture",
                quantity=Decimal("2"),
                unit="each",
                unit_price=Decimal("45.00"),
            ),
            LineItem(
                description="Installation labor",
                quantity=Decimal("1.5"),
                unit="hr",
                unit_price=Decimal("65.00"),
            ),
        ]
        subtotal, total_tax, grand_total = compute_totals(items)
        # subtotal = 90.00 + 97.50 = 187.50
        assert subtotal == Decimal("187.50")
        # Per-line tax: 90 * 0.1055 = 9.495, 97.50 * 0.1055 = 10.28625
        # total_tax = 9.495 + 10.28625 = 19.78125
        expected_tax = (Decimal("90.00") * Decimal("0.1055")) + (
            Decimal("97.50") * Decimal("0.1055")
        )
        assert total_tax == expected_tax
        assert grand_total == subtotal + total_tax


class TestFormatCurrency:
    """Tests for format_currency function."""

    def test_format_with_commas(self) -> None:
        """Large amounts have comma separators."""
        amount = Decimal("1234.56")
        assert format_currency(amount) == "$1,234.56"

    def test_format_large_amount(self) -> None:
        """Very large amounts formatted correctly."""
        amount = Decimal("12345678.90")
        assert format_currency(amount) == "$12,345,678.90"

    def test_format_zero(self) -> None:
        """Zero is formatted as $0.00."""
        amount = Decimal("0")
        assert format_currency(amount) == "$0.00"

    def test_format_rounds_half_up(self) -> None:
        """Amounts are rounded using ROUND_HALF_UP to 2 decimals."""
        # 123.455 should round to 123.46
        amount = Decimal("123.455")
        assert format_currency(amount) == "$123.46"

    def test_format_small_amount(self) -> None:
        """Small amounts under $1 formatted correctly."""
        amount = Decimal("0.99")
        assert format_currency(amount) == "$0.99"
