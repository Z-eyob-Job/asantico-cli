"""PDF generation using ReportLab.

Renders invoices and estimates with Asantico styling. Isolated from business logic.
"""

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from asantico_cli.domain.models import DOC_TYPE_ESTIMATE, DOC_TYPE_INVOICE, Document, get_recipient_name
from asantico_cli.domain.slug import build_pdf_filename
from asantico_cli.domain.tax import format_currency

# PDF styling constants
HEADER_FONT_SIZE = 18
TITLE_FONT_SIZE = 24
NORMAL_FONT_SIZE = 10
FOOTER_FONT_SIZE = 10

# Footer text (from SKILL.md, verbatim)
INVOICE_FOOTER = """Payment terms: Net 30. Make checks payable to Asantico, Seattle WA.
Questions: contact Asantico directly."""

ESTIMATE_FOOTER = """This estimate is valid for 30 days from the date issued. Pricing reflects work scope as described and may be revised if scope changes."""


def _format_display_currency(amount: Decimal) -> str:
    """Format currency for display, rounding to 2 decimal places."""
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"${rounded:,.2f}"


def render_pdf(document: Document, output_dir: Path) -> Path:
    """Render a Document to a PDF file.

    Args:
        document: The Document object to render.
        output_dir: Directory to write the PDF to.

    Returns:
        Path to the created PDF file.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build filename
    filename = build_pdf_filename(document.doc_type, document.property.name, document.date)
    output_path = output_dir / filename

    # Create PDF document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    # Build content
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontSize=HEADER_FONT_SIZE,
        fontName="Helvetica-Bold",
        spaceAfter=6,
    )
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=TITLE_FONT_SIZE,
        fontName="Helvetica-Bold",
        spaceAfter=12,
    )
    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=NORMAL_FONT_SIZE,
        spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=FOOTER_FONT_SIZE,
        fontName="Helvetica-Oblique",
        spaceBefore=20,
    )

    # --- Header Section ---
    elements.append(Paragraph("Asantico", header_style))
    elements.append(Paragraph("Seattle, WA", normal_style))
    elements.append(Spacer(1, 0.25 * inch))

    # --- Document Title ---
    title = "Invoice" if document.doc_type == DOC_TYPE_INVOICE else "Estimate"
    elements.append(Paragraph(title, title_style))

    # --- Document Info ---
    elements.append(Paragraph(f"<b>Document Number:</b> {document.doc_number}", normal_style))
    elements.append(Paragraph(f"<b>Date:</b> {document.date.strftime('%B %d, %Y')}", normal_style))
    elements.append(Spacer(1, 0.15 * inch))

    # --- Recipient Block ---
    recipient_name = get_recipient_name(document.property.name)
    elements.append(Paragraph("<b>Bill To:</b>", normal_style))
    elements.append(Paragraph("Avenue One Residential", normal_style))
    elements.append(Paragraph(f"Attn: {recipient_name}", normal_style))
    elements.append(Paragraph(f"Property: {document.property.name}", normal_style))
    elements.append(Spacer(1, 0.25 * inch))

    # --- Line Items Table ---
    table_data = [["Description", "Qty", "Unit", "Unit Price", "Total"]]

    for item in document.line_items:
        table_data.append([
            item.description,
            str(item.quantity),
            item.unit,
            _format_display_currency(item.unit_price),
            _format_display_currency(item.line_total),
        ])

    # Calculate column widths (total page width minus margins)
    page_width = letter[0] - 1.5 * inch
    col_widths = [
        page_width * 0.45,  # Description
        page_width * 0.10,  # Qty
        page_width * 0.10,  # Unit
        page_width * 0.17,  # Unit Price
        page_width * 0.18,  # Total
    ]

    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),

        # Data rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),

        # Alignment
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),  # Right-align numbers
        ("ALIGN", (0, 0), (0, -1), "LEFT"),    # Left-align description

        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.25 * inch))

    # --- Summary Section ---
    subtotal = document.subtotal
    total_tax = document.total_tax
    grand_total = document.grand_total

    summary_data = [
        ["", "", "", "Subtotal:", _format_display_currency(subtotal)],
        ["", "", "", "Tax (10.55%):", _format_display_currency(total_tax)],
        ["", "", "", "Total:", _format_display_currency(grand_total)],
    ]

    summary_table = Table(summary_data, colWidths=col_widths)
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (3, 2), (4, 2), "Helvetica-Bold"),  # Bold the total row
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.25 * inch))

    # --- Notes Section (if present) ---
    if document.notes:
        elements.append(Paragraph("<b>Notes:</b>", normal_style))
        elements.append(Paragraph(document.notes, normal_style))
        elements.append(Spacer(1, 0.15 * inch))

    # --- Footer ---
    footer_text = INVOICE_FOOTER if document.doc_type == DOC_TYPE_INVOICE else ESTIMATE_FOOTER
    # Replace newlines with <br/> for PDF rendering
    footer_text = footer_text.replace("\n", "<br/>")
    elements.append(Paragraph(footer_text, footer_style))

    # Build PDF
    doc.build(elements)

    return output_path
