# Quickstart: Asantico Invoice CLI

**Branch**: `001-asantico-invoice-cli` | **Date**: 2026-05-15

## Prerequisites

- Python 3.13 or later
- pip (Python package manager)

---

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd asantico-cli

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

---

## Verify Installation

```bash
asantico --version
# Output: asantico, version 0.1.0

asantico --help
# Shows available commands
```

---

## Generate Your First Invoice

### Option 1: From a JSON File

1. Create a file `items.json`:

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

2. Generate the invoice:

```bash
asantico invoice new --from-file items.json --property "The Meridian"
```

3. Find your PDF in `./output/invoice_the-meridian_2026-05-15.pdf`

### Option 2: Interactive Mode

```bash
asantico invoice new
```

Follow the prompts to:
1. Select or enter a property
2. Enter line items one by one
3. Confirm and generate

---

## Generate an Estimate

Same as invoice, but use the `estimate` command:

```bash
asantico estimate new --from-file items.json --property "Garden"
```

The estimate PDF will have "Estimate" as the title and a validity period in the footer instead of payment terms.

---

## Manage Properties

```bash
# List all properties
asantico properties list

# Add a new property
asantico properties add "New Building" --address "456 Oak St, Seattle WA"

# Remove a property
asantico properties remove "Old Building"
```

---

## Manage Rates

```bash
# List current rates
asantico rates list

# Set the labor rate
asantico rates set labor 75.00
```

---

## Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=asantico_cli

# Run specific test file
pytest tests/unit/test_tax.py
```

---

## Project Structure

```
asantico-cli/
├── src/asantico_cli/          # Main package
│   ├── domain/                # Business logic (pure functions)
│   ├── infra/                 # I/O (config, PDF, JSON loader)
│   └── cli/                   # Typer commands
├── tests/                     # Test suite
│   ├── unit/                  # Pure function tests
│   ├── integration/           # I/O tests
│   └── cli/                   # Command tests
├── examples/                  # Sample input files
└── output/                    # Generated PDFs (gitignored)
```

---

## Configuration Files

On first run, the CLI creates config files in `~/.asantico/`:

- `properties.json`: Property registry
- `rates.json`: Default labor/material rates
- `counters.json`: Document number counters

---

## Common Workflows

### Daily Invoice Generation

```bash
# Edit items.json with today's work
# Then generate:
asantico invoice new --from-file items.json --property "The Meridian"
```

### Quick Estimate

```bash
# Interactive mode for quick estimates
asantico estimate new
```

### Batch Processing

Create multiple JSON files for different jobs, then generate invoices:

```bash
asantico invoice new --from-file job1.json --property "Garden"
asantico invoice new --from-file job2.json --property "Portal"
```

---

## Troubleshooting

### "Command not found: asantico"

Ensure you activated the virtual environment:
```bash
source .venv/bin/activate
```

### "Invalid JSON" error

Check your JSON file for:
- Missing commas between objects
- Trailing commas
- Unquoted strings

### "Em dashes not allowed"

Replace any em dashes (the long dash character) with regular hyphens or commas in your descriptions.

---

## Next Steps

- Review the [CLI Contract](contracts/cli.md) for full command documentation
- See [Data Model](data-model.md) for entity definitions
- Check [Implementation Plan](plan.md) for development phases
