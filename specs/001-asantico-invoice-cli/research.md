# Research: Asantico Invoice CLI

**Branch**: `001-asantico-invoice-cli` | **Date**: 2026-05-15

## Overview

This document captures research findings and decisions for the Asantico Invoice CLI implementation. All technical context was provided in the spec and CLAUDE.md, so no external research was required.

---

## Technology Decisions

### CLI Framework: Typer

**Decision**: Use Typer (built on Click) for command-line parsing.

**Rationale**:
- Required by NFR-006 in the spec
- Native type hints for argument validation
- Built-in --help generation
- Click compatibility for advanced features
- Rich integration for colored output

**Alternatives Considered**:
- argparse: Standard library but verbose, no type hints
- Click: Typer is built on it; Typer adds type hint support
- fire: Auto-generates CLI but less control over help text

---

### PDF Generation: ReportLab

**Decision**: Use ReportLab for PDF rendering.

**Rationale**:
- Required by NFR-006 in the spec
- Mature, well-documented library
- Precise control over layout for professional invoices
- No external dependencies (pure Python)
- Works offline (NFR-005)

**Alternatives Considered**:
- weasyprint: HTML-to-PDF, requires external libraries
- fpdf2: Simpler but less layout control
- borb: Newer, less battle-tested

---

### Terminal UX: Rich

**Decision**: Use Rich for terminal output and prompts.

**Rationale**:
- Required by NFR-006 in the spec
- Beautiful tables for property/rate listings
- Colored error messages (FR-009)
- Interactive prompts for line item entry (FR-015, FR-016)
- Progress indicators if needed

**Alternatives Considered**:
- Click's built-in styling: Less capable
- prompt_toolkit: More complex than needed
- questionary: Good prompts but no tables

---

### Data Precision: Python Decimal

**Decision**: Use `decimal.Decimal` for all monetary calculations.

**Rationale**:
- Avoids floating-point rounding errors in tax calculations
- Matches how financial software handles currency
- FR-006 requires $1,234.56 formatting with exact two decimals
- Tax at 10.55% can produce repeating decimals with float

**Implementation**:
```python
from decimal import Decimal, ROUND_HALF_UP

TAX_RATE = Decimal("0.1055")  # 10.55%

def compute_line_tax(line_total: Decimal) -> Decimal:
    return (line_total * TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

---

### Config Storage: JSON Files

**Decision**: Store configuration in JSON files under ~/.asantico/.

**Rationale**:
- Human-readable and editable
- No additional dependencies
- Simple schema for properties, rates, counters
- Matches spec assumption about JSON format

**Files**:
- `~/.asantico/properties.json`: Property list
- `~/.asantico/rates.json`: Default labor/material rates
- `~/.asantico/counters.json`: Document number counters

---

## Domain Decisions

### Tax Calculation: Per-Line

**Decision**: Calculate tax per line item, then sum for total tax.

**Rationale**:
- Explicitly required by FR-001
- Matches how sales tax is typically computed
- Avoids rounding discrepancies vs. single-tax-on-subtotal approach

**Example**:
```
Line 1: $100.00 -> Tax: $10.55
Line 2: $50.00  -> Tax: $5.28 (rounded from 5.275)
Subtotal: $150.00
Total Tax: $15.83
Grand Total: $165.83
```

---

### Filename Collision: Overwrite

**Decision**: When a PDF with the same filename exists, overwrite it.

**Rationale**:
- Simpler implementation
- Matches expected behavior when regenerating a document
- Operator can rename if preservation needed
- Spec edge case allowed either approach

**Alternative Rejected**: Appending numeric suffix (invoice_the-meridian_2026-05-15_2.pdf) adds complexity without clear benefit.

---

### Property Not in List: Proceed Without Adding

**Decision**: In file-based mode, allow any property name without auto-adding to registry.

**Rationale**:
- Operator may have one-off properties
- Avoids cluttering registry with typos
- Interactive mode will offer explicit "add to registry" option

---

### PDF Styling: Professional Minimal

**Decision**: Use clean, professional layout without spec's "existing Asantico style" (not provided).

**Layout Specifications**:
- Page: Letter size (8.5" x 11")
- Margins: 1" all sides
- Header: "Asantico" in bold 18pt, "Seattle, WA" below
- Title: "Invoice" or "Estimate" in bold 24pt, centered
- Recipient: "Bill To: Avenue One Residential" with property name
- Document info: Number (INV-0001/EST-0001), Date
- Table: Light gray (#EEEEEE) header row, alternating white rows
- Columns: Description, Qty, Unit, Unit Price, Line Total
- Summary: Right-aligned subtotal, tax (10.55%), total
- Footer: Payment terms (invoice) or "Estimate valid for 30 days" (estimate)
- Font: Helvetica (built into ReportLab)

---

### Units: hr, each, flat

**Decision**: Support three unit types as specified.

**Meanings**:
- `hr`: Hourly labor (e.g., "2 hr @ $65.00")
- `each`: Per-item materials (e.g., "4 each @ $12.50")
- `flat`: Flat-rate service (e.g., "1 flat @ $150.00")

---

## Validation Rules

### Line Item Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| description | Non-empty, no em dash (U+2014) | "Description required" / "Em dashes not allowed" |
| quantity | Positive number (> 0) | "Quantity must be positive" |
| unit | One of: hr, each, flat | "Unit must be hr, each, or flat" |
| unit_price | Non-negative (>= 0) | "Unit price cannot be negative" |

### Property Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| name | Non-empty, no em dash | "Property name required" / "Em dashes not allowed" |

---

## Default Configuration

### Default Properties

From CLAUDE.md and spec assumptions:
1. Garden
2. The Meridian
3. Portal
4. Aprea View
5. Gilman's Fairway
6. Linden Avenue Condominiums
7. Canterbury Shores
8. Koda Condominiums
9. Clark Roadhouse

### Default Rates

| Type | Default Value |
|------|---------------|
| labor | $65.00/hr |
| materials | 0% markup (at cost) |

---

## Testing Strategy

### Unit Tests (Domain Layer)

Pure function tests with no I/O:
- `test_tax.py`: Tax calculation edge cases, rounding
- `test_slug.py`: Property name slugification
- `test_validation.py`: Input validation rules
- `test_models.py`: Dataclass instantiation, computed fields

### Integration Tests (Infra Layer)

Tests using pytest tmp_path fixture:
- `test_config.py`: JSON file read/write, defaults
- `test_pdf.py`: PDF file creation, content verification
- `test_loader.py`: JSON loading, schema validation

### CLI Tests (CLI Layer)

Tests using Typer CliRunner:
- `test_app.py`: --help, --version, no args
- `test_invoice.py`: invoice new with various inputs
- `test_estimate.py`: estimate new with various inputs
- `test_properties.py`: properties list/add/remove
- `test_rates.py`: rates list/set

---

## Unresolved Items

None. All technical context was provided or decided.

---

## References

- Spec: `specs/001-asantico-invoice-cli/spec.md`
- Project context: `CLAUDE.md`
- Typer docs: https://typer.tiangolo.com/
- ReportLab docs: https://docs.reportlab.com/
- Rich docs: https://rich.readthedocs.io/
