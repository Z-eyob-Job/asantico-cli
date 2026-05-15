"""Tests for slug generation and filename building."""

from datetime import date

import pytest

from asantico_cli.domain.slug import build_pdf_filename, slugify_property_name


class TestSlugifyPropertyName:
    """Tests for slugify_property_name function."""

    def test_basic_slug(self) -> None:
        """Simple name is lowercased and spaces become hyphens."""
        assert slugify_property_name("The Meridian") == "the-meridian"

    def test_apostrophe_removed(self) -> None:
        """Apostrophes are removed, not replaced with hyphens."""
        assert slugify_property_name("Gilman's Fairway") == "gilmans-fairway"

    def test_multiple_spaces(self) -> None:
        """Multiple spaces collapse to a single hyphen."""
        assert slugify_property_name("Linden Avenue Condominiums") == "linden-avenue-condominiums"

    def test_special_characters(self) -> None:
        """Special characters are replaced with hyphens."""
        assert slugify_property_name("Test & Property #1") == "test-property-1"

    def test_leading_trailing_hyphens_stripped(self) -> None:
        """Leading and trailing hyphens are removed."""
        assert slugify_property_name("  Property  ") == "property"


class TestBuildPdfFilename:
    """Tests for build_pdf_filename function."""

    def test_invoice_filename(self) -> None:
        """Invoice filename follows the pattern."""
        filename = build_pdf_filename("invoice", "The Meridian", date(2026, 5, 15))
        assert filename == "invoice_the-meridian_2026-05-15.pdf"

    def test_estimate_filename(self) -> None:
        """Estimate filename follows the pattern."""
        filename = build_pdf_filename("estimate", "Garden", date(2026, 5, 15))
        assert filename == "estimate_garden_2026-05-15.pdf"

    def test_apostrophe_in_property(self) -> None:
        """Property with apostrophe generates correct filename."""
        filename = build_pdf_filename("invoice", "Gilman's Fairway", date(2026, 5, 15))
        assert filename == "invoice_gilmans-fairway_2026-05-15.pdf"
