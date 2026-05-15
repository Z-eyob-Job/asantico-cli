"""Tax calculation and currency formatting functions.

All functions are pure with no I/O dependencies. Tax is calculated per-line
using the Seattle rate of 10.55%, then summed for totals.
"""

from decimal import ROUND_HALF_UP, Decimal

from asantico_cli.domain.models import SEATTLE_TAX_RATE, LineItem


def compute_line_tax(line_total: Decimal) -> Decimal:
    """Compute tax for a single line item.

    Args:
        line_total: The line total (quantity * unit_price).

    Returns:
        Tax amount (line_total * 10.55%), unrounded for internal use.
    """
    return line_total * SEATTLE_TAX_RATE


def compute_totals(line_items: list[LineItem]) -> tuple[Decimal, Decimal, Decimal]:
    """Compute subtotal, total tax, and grand total for a list of line items.

    Tax is calculated per-line and then summed (not applied to subtotal).

    Args:
        line_items: List of LineItem objects.

    Returns:
        Tuple of (subtotal, total_tax, grand_total).
    """
    subtotal = sum((item.line_total for item in line_items), Decimal("0"))
    total_tax = sum((item.line_tax for item in line_items), Decimal("0"))
    grand_total = subtotal + total_tax
    return subtotal, total_tax, grand_total


def format_currency(amount: Decimal) -> str:
    """Format a Decimal amount as USD currency string.

    Rounds to 2 decimal places using ROUND_HALF_UP, adds comma separators,
    and prefixes with dollar sign.

    Args:
        amount: The amount to format.

    Returns:
        Formatted string like "$1,234.56".
    """
    # Round to 2 decimal places
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    # Format with comma separators
    return f"${rounded:,.2f}"
