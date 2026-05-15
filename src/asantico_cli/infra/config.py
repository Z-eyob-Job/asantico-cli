"""Configuration file management for ~/.asantico/ directory.

Handles reading and writing JSON config files for properties, rates, and counters.
"""

import json
import os
from decimal import Decimal
from pathlib import Path

from asantico_cli.domain.models import (
    DEFAULT_PROPERTIES,
    DEFAULT_RATES,
    DOC_PREFIX,
    Property,
)


def get_config_dir() -> Path:
    """Get the path to the config directory (~/.asantico/).

    Returns:
        Path to the config directory.
    """
    # Allow override via environment variable for testing
    if "ASANTICO_CONFIG_DIR" in os.environ:
        return Path(os.environ["ASANTICO_CONFIG_DIR"])
    return Path.home() / ".asantico"


def ensure_config_dir() -> None:
    """Create the config directory if it does not exist."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


def load_properties() -> list[Property]:
    """Load properties from config file.

    If the file does not exist, returns default properties and saves them.

    Returns:
        List of Property objects.
    """
    config_dir = get_config_dir()
    properties_file = config_dir / "properties.json"

    if not properties_file.exists():
        # Initialize with defaults
        ensure_config_dir()
        save_properties(DEFAULT_PROPERTIES)
        return list(DEFAULT_PROPERTIES)

    with open(properties_file, encoding="utf-8") as f:
        data = json.load(f)

    return [Property(name=p["name"], address=p.get("address")) for p in data]


def save_properties(properties: list[Property]) -> None:
    """Save properties to config file.

    Args:
        properties: List of Property objects to save.
    """
    ensure_config_dir()
    config_dir = get_config_dir()
    properties_file = config_dir / "properties.json"

    data = [
        {"name": p.name, "address": p.address}
        for p in properties
    ]

    with open(properties_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_rates() -> dict[str, Decimal]:
    """Load rates from config file.

    If the file does not exist, returns default rates and saves them.

    Returns:
        Dictionary mapping rate type to Decimal value.
    """
    config_dir = get_config_dir()
    rates_file = config_dir / "rates.json"

    if not rates_file.exists():
        # Initialize with defaults
        ensure_config_dir()
        save_rates(DEFAULT_RATES)
        return dict(DEFAULT_RATES)

    with open(rates_file, encoding="utf-8") as f:
        data = json.load(f)

    return {k: Decimal(str(v)) for k, v in data.items()}


def save_rates(rates: dict[str, Decimal]) -> None:
    """Save rates to config file.

    Args:
        rates: Dictionary mapping rate type to Decimal value.
    """
    ensure_config_dir()
    config_dir = get_config_dir()
    rates_file = config_dir / "rates.json"

    # Convert Decimal to float for JSON serialization
    data = {k: float(v) for k, v in rates.items()}

    with open(rates_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_counters() -> dict[str, int]:
    """Load document counters from config file.

    If the file does not exist, returns empty counters (invoice=0, estimate=0).

    Returns:
        Dictionary mapping doc type to counter value.
    """
    config_dir = get_config_dir()
    counters_file = config_dir / "counters.json"

    if not counters_file.exists():
        return {"invoice": 0, "estimate": 0}

    with open(counters_file, encoding="utf-8") as f:
        data = json.load(f)

    return data


def _save_counters(counters: dict[str, int]) -> None:
    """Save document counters to config file.

    Args:
        counters: Dictionary mapping doc type to counter value.
    """
    ensure_config_dir()
    config_dir = get_config_dir()
    counters_file = config_dir / "counters.json"

    with open(counters_file, "w", encoding="utf-8") as f:
        json.dump(counters, f, indent=2)


def increment_counter(doc_type: str) -> str:
    """Increment the counter for a document type and return the formatted number.

    Args:
        doc_type: Document type ("invoice" or "estimate").

    Returns:
        Formatted document number like "INV-0001" or "EST-0001".
    """
    counters = load_counters()

    # Increment the counter
    current = counters.get(doc_type, 0)
    new_value = current + 1
    counters[doc_type] = new_value

    # Save the updated counters
    _save_counters(counters)

    # Return formatted number
    prefix = DOC_PREFIX.get(doc_type, "DOC")
    return f"{prefix}-{new_value:04d}"
