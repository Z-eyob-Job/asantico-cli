"""JSON file loader for line items.

Loads and validates line items from JSON files with Rich-formatted error messages.
"""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from rich.console import Console

from asantico_cli.domain.models import VALID_UNITS, LineItem
from asantico_cli.domain.validation import contains_em_dash

console = Console(stderr=True)


class LoaderError(Exception):
    """Exception raised when loading line items fails."""

    pass


def load_line_items(path: Path) -> list[LineItem]:
    """Load line items from a JSON file.

    The JSON file should contain an object with a "line_items" key or a plain array.
    Supports both formats:
    - {"line_items": [...], "notes": "..."}
    - [...]

    Args:
        path: Path to the JSON file.

    Returns:
        List of LineItem objects.

    Raises:
        LoaderError: If the file cannot be loaded or validated.
    """
    # Check file exists
    if not path.exists():
        raise LoaderError(f"File not found: {path}")

    # Read and parse JSON
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise LoaderError(f"Invalid JSON in {path}: {e}")

    # Handle both formats: {"line_items": [...]} and [...]
    if isinstance(data, dict):
        if "line_items" not in data:
            raise LoaderError(f"Invalid schema in {path}: missing 'line_items' key")
        items_data = data["line_items"]
    elif isinstance(data, list):
        items_data = data
    else:
        raise LoaderError(f"Invalid schema in {path}: expected array or object with 'line_items'")

    if not isinstance(items_data, list):
        raise LoaderError(f"Invalid schema in {path}: 'line_items' must be an array")

    if len(items_data) == 0:
        raise LoaderError(f"Invalid schema in {path}: at least one line item is required")

    # Validate and convert each item
    line_items: list[LineItem] = []
    for i, item in enumerate(items_data, 1):
        if not isinstance(item, dict):
            raise LoaderError(f"Invalid schema in {path}: line item {i} must be an object")

        # Validate required fields
        required_fields = ["description", "quantity", "unit", "unit_price"]
        for field in required_fields:
            if field not in item:
                raise LoaderError(f"Line item {i} missing required field: {field}")

        # Validate description
        description = item["description"]
        if not isinstance(description, str) or not description.strip():
            raise LoaderError(f"Line item {i}: description must be a non-empty string")
        if contains_em_dash(description):
            raise LoaderError(f"Line item {i}: em dashes (U+2014) not allowed in description")

        # Validate and convert quantity
        try:
            quantity = Decimal(str(item["quantity"]))
            if quantity <= 0:
                raise LoaderError(f"Line item {i}: quantity must be positive, got {quantity}")
        except (InvalidOperation, ValueError):
            raise LoaderError(f"Line item {i}: quantity must be a number, got {item['quantity']}")

        # Validate unit
        unit = item["unit"]
        if unit not in VALID_UNITS:
            raise LoaderError(f"Line item {i}: unit must be hr, each, or flat, got {unit}")

        # Validate and convert unit_price
        try:
            unit_price = Decimal(str(item["unit_price"]))
            if unit_price < 0:
                raise LoaderError(f"Line item {i}: unit price cannot be negative, got {unit_price}")
        except (InvalidOperation, ValueError):
            raise LoaderError(f"Line item {i}: unit_price must be a number, got {item['unit_price']}")

        line_items.append(LineItem(
            description=description.strip(),
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
        ))

    return line_items


def load_notes(path: Path) -> str | None:
    """Load optional notes from a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Notes string if present, None otherwise.
    """
    if not path.exists():
        return None

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return None

    if isinstance(data, dict) and "notes" in data:
        notes = data["notes"]
        if isinstance(notes, str) and notes.strip():
            return notes.strip()

    return None
