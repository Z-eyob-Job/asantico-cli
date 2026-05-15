"""Input validation functions.

All functions are pure with no I/O dependencies. Returns lists of error
messages (empty list means valid).
"""

from asantico_cli.domain.models import EM_DASH, VALID_UNITS, LineItem


def contains_em_dash(text: str) -> bool:
    """Check if text contains an em dash (U+2014).

    Em dashes are forbidden in all Asantico document content.

    Args:
        text: The text to check.

    Returns:
        True if the text contains an em dash, False otherwise.
    """
    return EM_DASH in text


def validate_line_item(item: LineItem) -> list[str]:
    """Validate a line item and return a list of error messages.

    Checks:
    - Description is non-empty
    - Description contains no em dashes
    - Quantity is positive (> 0)
    - Unit is one of hr, each, flat
    - Unit price is non-negative (>= 0)

    Args:
        item: The LineItem to validate.

    Returns:
        List of error messages. Empty list means the item is valid.
    """
    errors: list[str] = []

    # Check description
    if not item.description or not item.description.strip():
        errors.append("Description required")
    elif contains_em_dash(item.description):
        errors.append("Em dashes not allowed in description")

    # Check quantity
    if item.quantity <= 0:
        errors.append(f"Quantity must be positive, got {item.quantity}")

    # Check unit
    if item.unit not in VALID_UNITS:
        errors.append(f"Unit must be hr, each, or flat, got {item.unit}")

    # Check unit price
    if item.unit_price < 0:
        errors.append(f"Unit price cannot be negative, got {item.unit_price}")

    return errors


def validate_property_name(name: str) -> list[str]:
    """Validate a property name and return a list of error messages.

    Checks:
    - Name is non-empty
    - Name contains no em dashes

    Args:
        name: The property name to validate.

    Returns:
        List of error messages. Empty list means the name is valid.
    """
    errors: list[str] = []

    if not name or not name.strip():
        errors.append("Property name required")
    elif contains_em_dash(name):
        errors.append("Em dashes not allowed in property name")

    return errors
