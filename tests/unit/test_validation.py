"""Tests for validation functions."""

from decimal import Decimal

import pytest

from asantico_cli.domain.models import LineItem
from asantico_cli.domain.validation import (
    contains_em_dash,
    validate_line_item,
    validate_property_name,
)


class TestContainsEmDash:
    """Tests for contains_em_dash function."""

    def test_text_with_em_dash(self) -> None:
        """Returns True when text contains em dash."""
        text = "Replace faucet \u2014 primary unit"
        assert contains_em_dash(text) is True

    def test_text_without_em_dash(self) -> None:
        """Returns False when text has no em dash."""
        text = "Replace faucet, primary unit"
        assert contains_em_dash(text) is False

    def test_text_with_hyphen(self) -> None:
        """Regular hyphen is not confused with em dash."""
        text = "Pressure washing - front area"
        assert contains_em_dash(text) is False


class TestValidateLineItem:
    """Tests for validate_line_item function."""

    def test_valid_line_item(self) -> None:
        """Valid line item returns empty error list."""
        item = LineItem(
            description="Replace garbage disposal, unit 204",
            quantity=Decimal("1"),
            unit="each",
            unit_price=Decimal("285.00"),
        )
        errors = validate_line_item(item)
        assert errors == []

    def test_negative_quantity(self) -> None:
        """Negative quantity returns error."""
        item = LineItem(
            description="Test item",
            quantity=Decimal("-1"),
            unit="each",
            unit_price=Decimal("100.00"),
        )
        errors = validate_line_item(item)
        assert len(errors) == 1
        assert "positive" in errors[0].lower()

    def test_zero_quantity(self) -> None:
        """Zero quantity returns error."""
        item = LineItem(
            description="Test item",
            quantity=Decimal("0"),
            unit="each",
            unit_price=Decimal("100.00"),
        )
        errors = validate_line_item(item)
        assert len(errors) == 1
        assert "positive" in errors[0].lower()

    def test_em_dash_in_description(self) -> None:
        """Em dash in description returns error."""
        item = LineItem(
            description="Replace faucet \u2014 primary unit",
            quantity=Decimal("1"),
            unit="each",
            unit_price=Decimal("150.00"),
        )
        errors = validate_line_item(item)
        assert len(errors) == 1
        assert "em dash" in errors[0].lower()

    def test_invalid_unit(self) -> None:
        """Invalid unit returns error."""
        item = LineItem(
            description="Test item",
            quantity=Decimal("1"),
            unit="pieces",  # type: ignore[arg-type]
            unit_price=Decimal("100.00"),
        )
        errors = validate_line_item(item)
        assert len(errors) == 1
        assert "hr, each, or flat" in errors[0]

    def test_negative_price(self) -> None:
        """Negative unit price returns error."""
        item = LineItem(
            description="Test item",
            quantity=Decimal("1"),
            unit="each",
            unit_price=Decimal("-50.00"),
        )
        errors = validate_line_item(item)
        assert len(errors) == 1
        assert "negative" in errors[0].lower()

    def test_empty_description(self) -> None:
        """Empty description returns error."""
        item = LineItem(
            description="",
            quantity=Decimal("1"),
            unit="each",
            unit_price=Decimal("100.00"),
        )
        errors = validate_line_item(item)
        assert any("description" in e.lower() for e in errors)


class TestValidatePropertyName:
    """Tests for validate_property_name function."""

    def test_valid_property_name(self) -> None:
        """Valid property name returns empty error list."""
        errors = validate_property_name("The Meridian")
        assert errors == []

    def test_em_dash_in_property_name(self) -> None:
        """Em dash in property name returns error."""
        errors = validate_property_name("The \u2014 Meridian")
        assert len(errors) == 1
        assert "em dash" in errors[0].lower()

    def test_empty_property_name(self) -> None:
        """Empty property name returns error."""
        errors = validate_property_name("")
        assert len(errors) == 1
        assert "required" in errors[0].lower()

    def test_whitespace_only_property_name(self) -> None:
        """Whitespace-only property name returns error."""
        errors = validate_property_name("   ")
        assert len(errors) == 1
        assert "required" in errors[0].lower()
