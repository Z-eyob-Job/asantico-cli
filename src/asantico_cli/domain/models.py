"""Domain models for Asantico invoices and estimates.

All models are dataclasses with computed properties. No I/O or external dependencies.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal

# Constants
SEATTLE_TAX_RATE = Decimal("0.1055")
VALID_UNITS = frozenset({"hr", "each", "flat"})
DOC_TYPE_INVOICE = "invoice"
DOC_TYPE_ESTIMATE = "estimate"
DOC_PREFIX = {
    DOC_TYPE_INVOICE: "INV",
    DOC_TYPE_ESTIMATE: "EST",
}
EM_DASH = "\u2014"


@dataclass
class LineItem:
    """A single billable entry on an invoice or estimate.

    Args:
        description: Work performed or materials (no em dashes allowed).
        quantity: Number of units (must be > 0).
        unit: One of "hr", "each", or "flat".
        unit_price: Price per unit in USD (>= 0).
    """

    description: str
    quantity: Decimal
    unit: Literal["hr", "each", "flat"]
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        """Compute total for this line item (quantity * unit_price)."""
        return self.quantity * self.unit_price

    @property
    def line_tax(self) -> Decimal:
        """Compute tax for this line item (line_total * Seattle rate)."""
        return self.line_total * SEATTLE_TAX_RATE


@dataclass
class Property:
    """A real estate location serviced by Asantico.

    Args:
        name: Display name (e.g., "The Meridian").
        address: Optional full address.
    """

    name: str
    address: str | None = None

    @property
    def slug(self) -> str:
        """Generate URL-safe lowercase version for filenames."""
        import re

        # Lowercase
        result = self.name.lower()
        # Remove apostrophes (e.g., "Gilman's" -> "gilmans")
        result = result.replace("'", "")
        # Replace any run of non-alphanumeric characters with a single hyphen
        result = re.sub(r"[^a-z0-9]+", "-", result)
        # Strip leading/trailing hyphens
        result = result.strip("-")
        return result


@dataclass
class Rate:
    """A default price for a type of work.

    Args:
        rate_type: "labor" or "materials".
        value: Price per unit in USD.
    """

    rate_type: str
    value: Decimal


@dataclass
class Document:
    """A generated invoice or estimate containing line items.

    Args:
        doc_type: "invoice" or "estimate".
        doc_number: Formatted number like "INV-0001" or "EST-0001".
        date: Document date.
        property: Associated property.
        line_items: List of billable items.
        notes: Optional notes for the document footer.
    """

    doc_type: Literal["invoice", "estimate"]
    doc_number: str
    date: date
    property: Property
    line_items: list[LineItem] = field(default_factory=list)
    notes: str | None = None

    @property
    def subtotal(self) -> Decimal:
        """Sum of all line_total values."""
        return sum((item.line_total for item in self.line_items), Decimal("0"))

    @property
    def total_tax(self) -> Decimal:
        """Sum of all line_tax values (per-line tax calculation)."""
        return sum((item.line_tax for item in self.line_items), Decimal("0"))

    @property
    def grand_total(self) -> Decimal:
        """Total amount due: subtotal + total_tax."""
        return self.subtotal + self.total_tax


# Default properties for Avenue One Residential
DEFAULT_PROPERTIES = [
    Property(name="Garden"),
    Property(name="The Meridian"),
    Property(name="Portal"),
    Property(name="Aprea View"),
    Property(name="Gilman's Fairway"),
    Property(name="Linden Avenue Condominiums"),
    Property(name="Canterbury Shores"),
    Property(name="Koda Condominiums"),
    Property(name="Clark Roadhouse"),
]

# Default rates
DEFAULT_RATES = {
    "labor": Decimal("65.00"),
    "materials": Decimal("0.00"),
}

# Recipient routing: Andrew vs Saniya based on property
ANDREW_PROPERTIES = frozenset({"Garden", "The Meridian", "Portal", "Aprea View"})
SANIYA_PROPERTIES = frozenset({
    "Gilman's Fairway",
    "Linden Avenue Condominiums",
    "Canterbury Shores",
    "Koda Condominiums",
    "Clark Roadhouse",
})


def get_recipient_name(property_name: str) -> str:
    """Determine recipient (Andrew Miller or Saniya Zaveri) based on property.

    Args:
        property_name: The property name.

    Returns:
        "Andrew Miller" or "Saniya Zaveri".
    """
    if property_name in SANIYA_PROPERTIES:
        return "Saniya Zaveri"
    # Default to Andrew for unknown properties
    return "Andrew Miller"
