"""Integration tests for PDF generation."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from asantico_cli.domain.models import DOC_TYPE_ESTIMATE, DOC_TYPE_INVOICE, Document, LineItem, Property
from asantico_cli.infra.pdf import render_pdf


@pytest.fixture
def sample_invoice() -> Document:
    """Create a sample invoice document for testing."""
    return Document(
        doc_type=DOC_TYPE_INVOICE,
        doc_number="INV-0001",
        date=date(2026, 5, 15),
        property=Property(name="The Meridian"),
        line_items=[
            LineItem(
                description="Replace garbage disposal, unit 204",
                quantity=Decimal("1"),
                unit="each",
                unit_price=Decimal("285.00"),
            ),
            LineItem(
                description="Plumbing labor",
                quantity=Decimal("2.5"),
                unit="hr",
                unit_price=Decimal("65.00"),
            ),
        ],
    )


@pytest.fixture
def sample_estimate() -> Document:
    """Create a sample estimate document for testing."""
    return Document(
        doc_type=DOC_TYPE_ESTIMATE,
        doc_number="EST-0001",
        date=date(2026, 5, 15),
        property=Property(name="Garden"),
        line_items=[
            LineItem(
                description="Pressure washing, front walkway",
                quantity=Decimal("3"),
                unit="hr",
                unit_price=Decimal("65.00"),
            ),
        ],
        notes="Work to be scheduled for next week.",
    )


class TestRenderPdf:
    """Tests for render_pdf function."""

    def test_invoice_pdf_created(self, sample_invoice: Document, tmp_path: Path) -> None:
        """Invoice PDF is created in the output directory."""
        output_path = render_pdf(sample_invoice, tmp_path)

        assert output_path.exists()
        assert output_path.name == "invoice_the-meridian_2026-05-15.pdf"
        assert output_path.stat().st_size > 0

    def test_estimate_pdf_created(self, sample_estimate: Document, tmp_path: Path) -> None:
        """Estimate PDF is created in the output directory."""
        output_path = render_pdf(sample_estimate, tmp_path)

        assert output_path.exists()
        assert output_path.name == "estimate_garden_2026-05-15.pdf"
        assert output_path.stat().st_size > 0

    def test_output_directory_auto_created(self, sample_invoice: Document, tmp_path: Path) -> None:
        """Output directory is created if it does not exist."""
        output_dir = tmp_path / "nested" / "output"
        assert not output_dir.exists()

        output_path = render_pdf(sample_invoice, output_dir)

        assert output_dir.exists()
        assert output_path.exists()

    def test_pdf_contains_required_sections(self, sample_invoice: Document, tmp_path: Path) -> None:
        """PDF file is a valid PDF (starts with PDF header)."""
        output_path = render_pdf(sample_invoice, tmp_path)

        with open(output_path, "rb") as f:
            header = f.read(8)

        # PDF files start with %PDF-
        assert header.startswith(b"%PDF-")

    def test_invoice_with_notes(self, tmp_path: Path) -> None:
        """Invoice with notes renders successfully."""
        doc = Document(
            doc_type=DOC_TYPE_INVOICE,
            doc_number="INV-0002",
            date=date(2026, 5, 15),
            property=Property(name="Portal"),
            line_items=[
                LineItem(
                    description="Light fixture replacement",
                    quantity=Decimal("2"),
                    unit="each",
                    unit_price=Decimal("45.00"),
                ),
            ],
            notes="Tenant requested LED bulbs.",
        )

        output_path = render_pdf(doc, tmp_path)
        assert output_path.exists()

    def test_apostrophe_in_property_name(self, tmp_path: Path) -> None:
        """Property names with apostrophes generate valid filenames."""
        doc = Document(
            doc_type=DOC_TYPE_INVOICE,
            doc_number="INV-0003",
            date=date(2026, 5, 15),
            property=Property(name="Gilman's Fairway"),
            line_items=[
                LineItem(
                    description="Lawn maintenance",
                    quantity=Decimal("1"),
                    unit="flat",
                    unit_price=Decimal("150.00"),
                ),
            ],
        )

        output_path = render_pdf(doc, tmp_path)
        assert output_path.exists()
        assert output_path.name == "invoice_gilmans-fairway_2026-05-15.pdf"
