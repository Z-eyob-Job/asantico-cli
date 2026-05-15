# CLI Contract: Asantico Invoice CLI

**Branch**: `001-asantico-invoice-cli` | **Date**: 2026-05-15

## Overview

This document defines the command-line interface contract for the `asantico` CLI tool. All commands, flags, arguments, and exit codes are specified here.

---

## Global Options

| Flag | Type | Description |
|------|------|-------------|
| `--help` | flag | Show help message and exit |
| `--version` | flag | Show version number and exit |

**Version Output Format**:
```
asantico, version X.Y.Z
```

---

## Commands

### `asantico` (no subcommand)

**Behavior**: Display help text and exit with code 0.

---

### `asantico invoice new`

Generate a new invoice PDF.

**Usage**:
```
asantico invoice new [OPTIONS]
```

**Options**:

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--from-file` | PATH | No* | Path to JSON file containing line items |
| `--property` | TEXT | No* | Property name (from registry or new) |

*If `--from-file` is not provided, interactive mode is entered.
*If `--property` is not provided, interactive selection is offered.

**Output**:
- Creates PDF in `./output/` directory
- Prints path to created PDF on success
- Prints Rich-formatted error on failure

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success, PDF created |
| 1 | Validation error (invalid JSON, negative quantity, etc.) |
| 2 | File error (JSON file not found, output directory issue) |

**Example**:
```bash
asantico invoice new --from-file items.json --property "The Meridian"
# Output: Created: ./output/invoice_the-meridian_2026-05-15.pdf
```

---

### `asantico estimate new`

Generate a new estimate PDF.

**Usage**:
```
asantico estimate new [OPTIONS]
```

**Options**: Same as `asantico invoice new`.

**Output**: Same as invoice, but:
- PDF title is "Estimate" instead of "Invoice"
- Document number format is `EST-NNNN`
- Footer contains validity period instead of payment terms

**Exit Codes**: Same as `asantico invoice new`.

**Example**:
```bash
asantico estimate new --from-file items.json --property "Garden"
# Output: Created: ./output/estimate_garden_2026-05-15.pdf
```

---

### `asantico properties list`

List all configured properties.

**Usage**:
```
asantico properties list
```

**Output**:
- Rich table with property names and addresses
- Creates default properties on first run if none exist

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success |

**Example Output**:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Name                       ┃ Address ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ Garden                     │         │
│ The Meridian               │         │
│ Portal                     │         │
│ ...                        │         │
└────────────────────────────┴─────────┘
```

---

### `asantico properties add`

Add a new property to the registry.

**Usage**:
```
asantico properties add NAME [OPTIONS]
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| NAME | TEXT | Yes | Property name to add |

**Options**:
| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--address` | TEXT | No | Optional property address |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success, property added |
| 1 | Property already exists |

**Example**:
```bash
asantico properties add "New Property" --address "123 Main St"
# Output: Added property: New Property
```

---

### `asantico properties remove`

Remove a property from the registry.

**Usage**:
```
asantico properties remove NAME
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| NAME | TEXT | Yes | Property name to remove |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success, property removed |
| 1 | Property not found |

**Example**:
```bash
asantico properties remove "Old Property"
# Output: Removed property: Old Property
```

---

### `asantico rates list`

List all configured rates.

**Usage**:
```
asantico rates list
```

**Output**:
- Rich table with rate types and values
- Creates defaults on first run if none exist

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success |

**Example Output**:
```
┏━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Type       ┃ Rate     ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━┩
│ labor      │ $65.00   │
│ materials  │ $0.00    │
└────────────┴──────────┘
```

---

### `asantico rates set`

Set a default rate.

**Usage**:
```
asantico rates set TYPE VALUE
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| TYPE | TEXT | Yes | Rate type ("labor" or "materials") |
| VALUE | FLOAT | Yes | Rate value in USD |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success, rate updated |
| 1 | Invalid rate type |
| 1 | Invalid value (negative) |

**Example**:
```bash
asantico rates set labor 75.00
# Output: Set labor rate to $75.00
```

---

## Interactive Mode

When `asantico invoice new` or `asantico estimate new` is run without `--from-file`:

### Property Selection Prompt

```
Select property:
[1] Garden
[2] The Meridian
[3] Portal
...
[0] Enter new property name

Choice: _
```

If "Enter new property name" is selected:
```
Property name: _
Add to registry? [y/N]: _
```

### Line Item Entry Prompt

```
Line Item #1
Description: _
Quantity: _
Unit (hr/each/flat): _
Unit Price: _

Add another line item? [Y/n]: _
```

### Confirmation Prompt

```
Document Summary
────────────────────────────────────────
Property: The Meridian
Type: Invoice
Lines: 3

  Description                  Qty  Unit  Price     Total
  Pressure washing             2.5  hr    $65.00   $162.50
  ...

  Subtotal:                                        $XXX.XX
  Tax (10.55%):                                    $XX.XX
  Total:                                           $XXX.XX

Generate PDF? [Y/n]: _
```

---

## Line Items JSON Schema

Input file for `--from-file` must be a JSON array:

```json
[
  {
    "description": "Pressure washing, front walkway",
    "quantity": 2.5,
    "unit": "hr",
    "unit_price": 65.00
  },
  {
    "description": "Replacement light bulbs",
    "quantity": 4,
    "unit": "each",
    "unit_price": 8.50
  }
]
```

**Required Fields**:
- `description`: string, non-empty, no em dashes
- `quantity`: number, > 0
- `unit`: string, one of "hr", "each", "flat"
- `unit_price`: number, >= 0

---

## Error Messages

All errors are displayed using Rich formatting.

| Error Condition | Message |
|-----------------|---------|
| JSON file not found | `Error: File not found: {path}` |
| Invalid JSON syntax | `Error: Invalid JSON in {path}: {details}` |
| Missing required field | `Error: Line item missing required field: {field}` |
| Invalid quantity | `Error: Quantity must be positive, got {value}` |
| Invalid unit | `Error: Unit must be hr, each, or flat, got {value}` |
| Negative price | `Error: Unit price cannot be negative, got {value}` |
| Em dash detected | `Error: Em dashes (—) not allowed in {field}` |
| Property not found (remove) | `Error: Property not found: {name}` |
| Property exists (add) | `Error: Property already exists: {name}` |

---

## Output Directory

- PDFs are written to `./output/` relative to current working directory
- Directory is created automatically if it does not exist
- Filename format: `{type}_{property-slug}_{YYYY-MM-DD}.pdf`

**Examples**:
- `./output/invoice_the-meridian_2026-05-15.pdf`
- `./output/estimate_garden_2026-05-15.pdf`
- `./output/invoice_gilmans-fairway_2026-05-15.pdf`
