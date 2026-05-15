# Data Model: Asantico Invoice CLI

**Branch**: `001-asantico-invoice-cli` | **Date**: 2026-05-15

## Overview

This document defines the data structures for the Asantico Invoice CLI. All models are Python dataclasses in `src/asantico_cli/domain/models.py`.

---

## Entities

### LineItem

A single billable entry on an invoice or estimate.

```python
@dataclass
class LineItem:
    description: str          # Work performed or materials (no em dashes)
    quantity: Decimal         # Number of units (must be > 0)
    unit: str                 # "hr", "each", or "flat"
    unit_price: Decimal       # Price per unit in USD (>= 0)

    @property
    def line_total(self) -> Decimal:
        """Computed: quantity * unit_price"""

    @property
    def line_tax(self) -> Decimal:
        """Computed: line_total * 0.1055 (Seattle tax rate)"""
```

**Validation Rules**:
| Field | Constraint | Error |
|-------|------------|-------|
| description | len > 0 | "Description required" |
| description | no U+2014 | "Em dashes not allowed in description" |
| quantity | > 0 | "Quantity must be positive" |
| unit | in {"hr", "each", "flat"} | "Unit must be hr, each, or flat" |
| unit_price | >= 0 | "Unit price cannot be negative" |

**Example**:
```json
{
  "description": "Pressure washing, front walkway",
  "quantity": 2.5,
  "unit": "hr",
  "unit_price": 65.00
}
```

---

### Document

A generated invoice or estimate containing line items and computed totals.

```python
@dataclass
class Document:
    doc_type: str             # "invoice" or "estimate"
    doc_number: str           # "INV-0001" or "EST-0001"
    date: date                # Document date
    property: Property        # Associated property
    line_items: list[LineItem]
    notes: str | None = None  # Optional notes

    @property
    def subtotal(self) -> Decimal:
        """Sum of all line_total values"""

    @property
    def total_tax(self) -> Decimal:
        """Sum of all line_tax values"""

    @property
    def grand_total(self) -> Decimal:
        """subtotal + total_tax"""
```

**Validation Rules**:
| Field | Constraint | Error |
|-------|------------|-------|
| doc_type | in {"invoice", "estimate"} | "Invalid document type" |
| doc_number | matches pattern | "Invalid document number format" |
| line_items | len > 0 | "Document must have at least one line item" |

**Document Number Format**:
- Invoice: `INV-{NNNN}` where NNNN is zero-padded 4-digit counter
- Estimate: `EST-{NNNN}`

---

### Property

A real estate location serviced by Asantico.

```python
@dataclass
class Property:
    name: str                 # Display name (e.g., "The Meridian")
    address: str | None = None  # Optional full address

    @property
    def slug(self) -> str:
        """URL-safe lowercase version for filenames"""
```

**Validation Rules**:
| Field | Constraint | Error |
|-------|------------|-------|
| name | len > 0 | "Property name required" |
| name | no U+2014 | "Em dashes not allowed in property name" |

**Slug Generation**:
- Lowercase
- Replace non-alphanumeric with hyphens
- Collapse multiple hyphens
- Strip leading/trailing hyphens

**Examples**:
| Name | Slug |
|------|------|
| The Meridian | the-meridian |
| Gilman's Fairway | gilmans-fairway |
| Linden Avenue Condominiums | linden-avenue-condominiums |

---

### Rate

A default price for a type of work.

```python
@dataclass
class Rate:
    rate_type: str            # "labor" or "materials"
    value: Decimal            # Price per unit
```

**Note**: Rates are convenience defaults. Line items always specify their own unit_price, which may differ from the default rate.

---

### Counter

Persistent document number counter.

```python
@dataclass
class Counter:
    invoice: int = 0          # Last used invoice number
    estimate: int = 0         # Last used estimate number
```

**Behavior**:
- `increment_counter("invoice")` returns "INV-0001" on first call, "INV-0002" on second
- Counters persist in `~/.asantico/counters.json`
- Never decremented (even if document deleted)

---

## Relationships

```
Property (1) ---- (0..*) Document
                          |
                          | (1..*)
                          v
                      LineItem
```

- A **Property** can have zero or more **Documents** associated with it
- A **Document** must have at least one **LineItem**
- **Rates** are standalone configuration, not linked to documents

---

## State Transitions

Documents have no state machine. Once created, a document is immutable (regenerating creates a new file with the same or incremented number based on date collision handling).

---

## JSON Schemas

### Line Items Input (--from-file)

```json
[
  {
    "description": "string (required, no em dashes)",
    "quantity": "number (required, > 0)",
    "unit": "string (required, one of: hr, each, flat)",
    "unit_price": "number (required, >= 0)"
  }
]
```

### properties.json

```json
[
  {
    "name": "string",
    "address": "string | null"
  }
]
```

### rates.json

```json
{
  "labor": "number",
  "materials": "number"
}
```

### counters.json

```json
{
  "invoice": "integer",
  "estimate": "integer"
}
```

---

## Constants

```python
# Tax rate for Seattle (10.55%)
SEATTLE_TAX_RATE = Decimal("0.1055")

# Valid units
VALID_UNITS = frozenset({"hr", "each", "flat"})

# Document types
DOC_TYPE_INVOICE = "invoice"
DOC_TYPE_ESTIMATE = "estimate"

# Document number prefixes
DOC_PREFIX = {
    "invoice": "INV",
    "estimate": "EST",
}

# Unicode em dash (forbidden character)
EM_DASH = "\u2014"
```

---

## Default Values

### Default Properties

```python
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
```

### Default Rates

```python
DEFAULT_RATES = {
    "labor": Decimal("65.00"),
    "materials": Decimal("0.00"),  # At cost, no markup
}
```

---

## Computed Fields Summary

| Entity | Field | Computation |
|--------|-------|-------------|
| LineItem | line_total | quantity * unit_price |
| LineItem | line_tax | line_total * 0.1055 |
| Document | subtotal | sum(item.line_total for item in line_items) |
| Document | total_tax | sum(item.line_tax for item in line_items) |
| Document | grand_total | subtotal + total_tax |
| Property | slug | slugify(name) |
