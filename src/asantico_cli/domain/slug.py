"""Slug generation and filename building functions.

All functions are pure with no I/O dependencies.
"""

import re
from datetime import date


def slugify_property_name(name: str) -> str:
    """Convert a property name to a URL-safe slug for filenames.

    Converts to lowercase, removes apostrophes, replaces any run of
    non-alphanumeric characters with a single hyphen, and trims
    leading/trailing hyphens.

    Args:
        name: The property name to slugify.

    Returns:
        A URL-safe slug string.
    """
    # Lowercase
    result = name.lower()
    # Remove apostrophes (e.g., "Gilman's" -> "gilmans")
    result = result.replace("'", "")
    # Replace any run of non-alphanumeric characters with a single hyphen
    result = re.sub(r"[^a-z0-9]+", "-", result)
    # Strip leading/trailing hyphens
    result = result.strip("-")
    return result


def build_pdf_filename(doc_type: str, property_name: str, doc_date: date) -> str:
    """Build the PDF filename following the project pattern.

    Pattern: {type}_{property-slug}_{YYYY-MM-DD}.pdf

    Args:
        doc_type: Document type ("invoice" or "estimate").
        property_name: The property name.
        doc_date: The document date.

    Returns:
        Filename string like "invoice_the-meridian_2026-05-15.pdf".
    """
    slug = slugify_property_name(property_name)
    date_str = doc_date.strftime("%Y-%m-%d")
    return f"{doc_type}_{slug}_{date_str}.pdf"
