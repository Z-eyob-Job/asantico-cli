"""Tests for domain models."""

from datetime import date
from decimal import Decimal

import pytest

from asantico_cli.domain.models import (
    Document,
    LineItem,
    Property,
    get_recipient_name,
)


class TestLineItem:
    """Tests for LineItem dataclass."""

    def test_line_item_creation(self) -> None:
        """LineItem can be created with valid data."""
        item = LineItem(
            description="Replace garbage disposal, unit 204",
            quantity=Decimal("1"),
            unit="each",
            unit_price=Decimal("285.00"),
        )
        assert item.description == "Replace garbage disposal, unit 204"
        assert item.quantity == Decimal("1")
        assert item.unit == "each"
        assert item.unit_price == Decimal("285.00")

    def test_line_total_computed(self) -> None:
        """line_total is computed as quantity * unit_price."""
        item = LineItem(
            description="Plumbing labor, kitchen",
            quantity=Decimal("2.5"),
            unit="hr",
            unit_price=Decimal("95.00"),
        )
        assert item.line_total == Decimal("237.50")

    def test_line_tax_computed(self) -> None:
        """line_tax is computed as line_total * 10.55%."""
        item = LineItem(
            description="Pressure washing, walkway",
            quantity=Decimal("2"),
            unit="hr",
            unit_price=Decimal("65.00"),
        )
        # line_total = 130.00
        # line_tax = 130.00 * 0.1055 = 13.715
        expected_tax = Decimal("130.00") * Decimal("0.1055")
        assert item.line_tax == expected_tax


class TestDocument:
    """Tests for Document dataclass."""

    def test_document_creation(self) -> None:
        """Document can be created with line items."""
        prop = Property(name="The Meridian")
        item = LineItem(
            description="Light fixture replacement",
            quantity=Decimal("1"),
            unit="each",
            unit_price=Decimal("150.00"),
        )
        doc = Document(
            doc_type="invoice",
            doc_number="INV-0001",
            date=date(2026, 5, 15),
            property=prop,
            line_items=[item],
        )
        assert doc.doc_type == "invoice"
        assert doc.doc_number == "INV-0001"
        assert len(doc.line_items) == 1

    def test_document_totals_computed(self) -> None:
        """subtotal, total_tax, and grand_total are computed correctly."""
        prop = Property(name="Garden")
        items = [
            LineItem(
                description="Garbage disposal replacement",
                quantity=Decimal("1"),
                unit="each",
                unit_price=Decimal("285.00"),
            ),
            LineItem(
                description="Labor",
                quantity=Decimal("2"),
                unit="hr",
                unit_price=Decimal("65.00"),
            ),
        ]
        doc = Document(
            doc_type="invoice",
            doc_number="INV-0002",
            date=date(2026, 5, 15),
            property=prop,
            line_items=items,
        )
        # subtotal = 285.00 + 130.00 = 415.00
        assert doc.subtotal == Decimal("415.00")
        # Per-line tax: 285 * 0.1055 = 30.0675, 130 * 0.1055 = 13.715
        # total_tax = 30.0675 + 13.715 = 43.7825
        expected_tax = (Decimal("285.00") * Decimal("0.1055")) + (
            Decimal("130.00") * Decimal("0.1055")
        )
        assert doc.total_tax == expected_tax
        assert doc.grand_total == doc.subtotal + doc.total_tax


class TestProperty:
    """Tests for Property dataclass."""

    def test_property_creation(self) -> None:
        """Property can be created with name and optional address."""
        prop = Property(name="The Meridian", address="123 Meridian Way")
        assert prop.name == "The Meridian"
        assert prop.address == "123 Meridian Way"

    def test_property_slug_basic(self) -> None:
        """Slug is lowercase with hyphens for spaces."""
        prop = Property(name="The Meridian")
        assert prop.slug == "the-meridian"

    def test_property_slug_apostrophe(self) -> None:
        """Slug handles apostrophes by replacing with hyphen."""
        prop = Property(name="Gilman's Fairway")
        assert prop.slug == "gilmans-fairway"


class TestRecipientRouting:
    """Tests for recipient routing based on property."""

    def test_andrew_property(self) -> None:
        """Andrew receives documents for Garden, Meridian, Portal, Aprea View."""
        assert get_recipient_name("Garden") == "Andrew Miller"
        assert get_recipient_name("The Meridian") == "Andrew Miller"

    def test_saniya_property(self) -> None:
        """Saniya receives documents for Gilman's Fairway and others."""
        assert get_recipient_name("Gilman's Fairway") == "Saniya Zaveri"
        assert get_recipient_name("Canterbury Shores") == "Saniya Zaveri"

    def test_unknown_property_defaults_to_andrew(self) -> None:
        """Unknown properties default to Andrew."""
        assert get_recipient_name("Unknown Property") == "Andrew Miller"
