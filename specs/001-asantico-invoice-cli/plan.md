# Implementation Plan: Asantico Invoice CLI

**Branch**: `001-asantico-invoice-cli` | **Date**: 2026-05-15 | **Spec**: [specs/001-asantico-invoice-cli/spec.md](spec.md)

**Input**: Feature specification from `/specs/001-asantico-invoice-cli/spec.md`

## Summary

Build a command-line tool that generates professional PDF invoices and estimates for Asantico, a Seattle property maintenance business. The CLI uses a three-layer architecture (domain, infrastructure, CLI) with Typer for command parsing, ReportLab for PDF rendering, and Rich for terminal UX. All business logic lives in pure functions for testability; PDF rendering is isolated for mockability.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Typer (CLI framework), ReportLab (PDF rendering), Rich (terminal UX)

**Storage**: JSON files in ~/.asantico/ (properties.json, rates.json, counters.json)

**Testing**: pytest with CliRunner for command tests, tmp_path for file I/O tests

**Target Platform**: macOS, Linux, Windows (any platform with Python 3.13)

**Project Type**: CLI application

**Performance Goals**: PDF generation under 30 seconds (per SC-001); typical generation under 2 seconds

**Constraints**: Fully offline (NFR-005), no network calls, pip-installable dependencies only (NFR-004)

**Scale/Scope**: Single operator, ~10 properties, ~50 documents/month

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution template has not been customized for this project. Applying sensible defaults:

| Principle | Status | Notes |
|-----------|--------|-------|
| Testability | PASS | All business logic in pure functions (NFR-001), PDF isolated (NFR-002) |
| Simplicity | PASS | Single CLI binary, JSON config, no database, no network |
| Offline-first | PASS | Zero network calls required (NFR-005) |

No constitution violations. Proceeding to design.

## Project Structure

### Documentation (this feature)

```text
specs/001-asantico-invoice-cli/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── cli.md           # CLI command contract
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
src/asantico_cli/
├── __init__.py
├── domain/                    # Layer 1: Pure business logic
│   ├── __init__.py
│   ├── models.py              # LineItem, Document, Property, Rate dataclasses
│   ├── tax.py                 # compute_line_tax, compute_totals
│   ├── slug.py                # slugify_property_name, build_pdf_filename
│   └── validation.py          # validate_line_item, validate_property_name
├── infra/                     # Layer 2: I/O and external concerns
│   ├── __init__.py
│   ├── config.py              # read/write JSON config (~/.asantico/)
│   ├── pdf.py                 # ReportLab PDF renderer
│   └── loader.py              # JSON line-item loader with schema validation
└── cli/                       # Layer 3: Typer entrypoint
    ├── __init__.py
    ├── app.py                 # Main Typer app, --version, --help
    ├── invoice.py             # invoice new command
    ├── estimate.py            # estimate new command
    ├── properties.py          # properties list/add/remove
    ├── rates.py               # rates list/set
    └── interactive.py         # Rich prompts for interactive mode

tests/
├── __init__.py
├── unit/                      # Pure function tests
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_tax.py
│   ├── test_slug.py
│   └── test_validation.py
├── integration/               # I/O tests with tmp_path
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_pdf.py
│   └── test_loader.py
└── cli/                       # CLI tests with CliRunner
    ├── __init__.py
    ├── test_app.py
    ├── test_invoice.py
    ├── test_estimate.py
    ├── test_properties.py
    └── test_rates.py

examples/
└── sample_items.json          # Example line items for testing/demo

output/                        # Generated PDFs (gitignored)
```

**Structure Decision**: Single-project CLI layout with src-layout packaging. Three-layer architecture separates domain logic (testable without I/O), infrastructure (mockable I/O), and CLI (thin command wrappers).

## Complexity Tracking

No constitution violations requiring justification.

---

## Implementation Phases

### Phase 1: Domain Models and Tax Math

**Goal**: Establish core data structures and tax calculation logic.

**Files Created**:
- `src/asantico_cli/__init__.py`
- `src/asantico_cli/domain/__init__.py`
- `src/asantico_cli/domain/models.py`
- `src/asantico_cli/domain/tax.py`

**Tests Added**:
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/unit/test_models.py` (3 tests: LineItem creation, Document creation, Property creation)
- `tests/unit/test_tax.py` (5 tests: line tax calculation, labor tax, totals computation, rounding, edge cases)

**Requirements Satisfied**: FR-001 (tax calculation), FR-005 (line item structure), FR-006 (currency formatting), NFR-001 (pure functions)

**Deliverables**:
- `LineItem` dataclass with description, quantity, unit, unit_price, computed line_total and line_tax
- `Document` dataclass with doc_type (invoice/estimate), doc_number, date, property, line_items, subtotal, total_tax, grand_total
- `Property` dataclass with name and optional address
- `Rate` dataclass with rate_type and value
- `compute_line_tax(line_total: Decimal) -> Decimal` (10.55% rounded to 2 decimals)
- `compute_totals(line_items: list[LineItem]) -> tuple[Decimal, Decimal, Decimal]` (subtotal, total_tax, grand_total)
- `format_currency(amount: Decimal) -> str` ($1,234.56 format)

---

### Phase 2: Slug, Filename, and Validation

**Goal**: Implement filename generation and input validation.

**Files Created**:
- `src/asantico_cli/domain/slug.py`
- `src/asantico_cli/domain/validation.py`

**Tests Added**:
- `tests/unit/test_slug.py` (4 tests: basic slug, special chars, filename pattern, date formatting)
- `tests/unit/test_validation.py` (4 tests: valid line item, negative quantity, zero quantity, invalid property)

**Requirements Satisfied**: FR-007 (filename pattern), FR-008 (no em dashes), FR-009 (validation errors), NFR-001 (pure functions)

**Deliverables**:
- `slugify_property_name(name: str) -> str` (lowercase, replace non-alphanumeric with hyphens)
- `build_pdf_filename(doc_type: str, property_name: str, date: date) -> str`
- `validate_line_item(item: LineItem) -> list[str]` (returns validation errors)
- `validate_property_name(name: str) -> list[str]`
- `contains_em_dash(text: str) -> bool` (check for U+2014)

---

### Phase 3: Config Persistence Layer

**Goal**: Implement JSON config file management under ~/.asantico/.

**Files Created**:
- `src/asantico_cli/infra/__init__.py`
- `src/asantico_cli/infra/config.py`

**Tests Added**:
- `tests/integration/__init__.py`
- `tests/integration/test_config.py` (6 tests: init config dir, read/write properties, read/write rates, read/write counters, increment counter, default values)

**Requirements Satisfied**: FR-004 (document numbering), FR-010 (config location), FR-012 (property CRUD), FR-013 (rate CRUD)

**Deliverables**:
- `get_config_dir() -> Path` (~/.asantico/)
- `ensure_config_dir() -> None` (create if missing)
- `load_properties() -> list[Property]` (with defaults if missing)
- `save_properties(properties: list[Property]) -> None`
- `load_rates() -> dict[str, Decimal]` (with defaults if missing)
- `save_rates(rates: dict[str, Decimal]) -> None`
- `load_counters() -> dict[str, int]`
- `increment_counter(doc_type: str) -> str` (returns formatted number like INV-0001)
- Default properties list: Garden, The Meridian, Portal, Aprea View, Gilman's Fairway, Linden Avenue Condominiums, Canterbury Shores, Koda Condominiums, Clark Roadhouse

---

### Phase 4: PDF Renderer

**Goal**: Implement ReportLab PDF generation with Asantico styling.

**Files Created**:
- `src/asantico_cli/infra/pdf.py`

**Tests Added**:
- `tests/integration/test_pdf.py` (4 tests: invoice PDF created, estimate PDF created, PDF contains required sections, output directory creation)

**Requirements Satisfied**: FR-002 (PDF layout), FR-003 (footer differences), FR-017 (output directory), NFR-002 (isolated rendering)

**Deliverables**:
- `render_pdf(document: Document, output_dir: Path) -> Path`
- PDF layout:
  - Header: Asantico business name, Seattle WA
  - Recipient: Avenue One Residential, property name
  - Document info: number, date, type title (Invoice/Estimate)
  - Line item table: description, qty, unit, unit price, line total
  - Summary: subtotal row, tax row (10.55%), total row
  - Footer: payment terms (invoice) or validity period (estimate)
- Auto-create output/ directory if missing

---

### Phase 5: JSON Loader

**Goal**: Load line items from JSON file with schema validation.

**Files Created**:
- `src/asantico_cli/infra/loader.py`
- `examples/sample_items.json`

**Tests Added**:
- `tests/integration/test_loader.py` (4 tests: load valid JSON, missing file error, malformed JSON error, invalid schema error)

**Requirements Satisfied**: FR-005 (line item loading), FR-009 (validation errors)

**Deliverables**:
- `load_line_items(path: Path) -> list[LineItem]`
- JSON schema: `[{"description": str, "quantity": number, "unit": "hr"|"each"|"flat", "unit_price": number}]`
- Rich-formatted error messages for validation failures

---

### Phase 6: CLI Entrypoint and Subcommands

**Goal**: Implement Typer CLI with all commands.

**Files Created**:
- `src/asantico_cli/cli/__init__.py`
- `src/asantico_cli/cli/app.py`
- `src/asantico_cli/cli/invoice.py`
- `src/asantico_cli/cli/estimate.py`
- `src/asantico_cli/cli/properties.py`
- `src/asantico_cli/cli/rates.py`
- `pyproject.toml` (update with entry point)

**Tests Added**:
- `tests/cli/__init__.py`
- `tests/cli/test_app.py` (3 tests: help, version, no args shows help)
- `tests/cli/test_invoice.py` (3 tests: invoice from file, missing property error, invalid JSON error)
- `tests/cli/test_estimate.py` (2 tests: estimate from file, estimate has correct title)
- `tests/cli/test_properties.py` (3 tests: list, add, remove)
- `tests/cli/test_rates.py` (2 tests: list, set)

**Requirements Satisfied**: FR-011 (invoice/estimate commands), FR-012 (properties commands), FR-013 (rates commands), FR-014 (help/version), NFR-006 (Typer/Rich)

**Deliverables**:
- `asantico --help` and `asantico --version`
- `asantico invoice new --from-file PATH --property NAME`
- `asantico estimate new --from-file PATH --property NAME`
- `asantico properties list`
- `asantico properties add NAME`
- `asantico properties remove NAME`
- `asantico rates list`
- `asantico rates set TYPE VALUE`

---

### Phase 7: Interactive Mode Prompts

**Goal**: Add Rich-based interactive prompts for document creation without flags.

**Files Created**:
- `src/asantico_cli/cli/interactive.py`

**Tests Added**:
- `tests/cli/test_interactive.py` (3 tests: property selection prompt, line item entry prompt, confirmation prompt)

**Requirements Satisfied**: FR-015 (interactive property selection), FR-016 (interactive line item entry)

**Deliverables**:
- `prompt_property_selection(properties: list[Property]) -> Property`
- `prompt_line_items() -> list[LineItem]`
- `prompt_confirmation(document: Document) -> bool`
- Integration with invoice/estimate commands when --from-file not provided

---

### Phase 8: Examples, README, and Polish

**Goal**: Finalize documentation, examples, and edge case handling.

**Files Updated**:
- `examples/sample_items.json` (comprehensive example)
- `pyproject.toml` (final metadata)

**Tests Added**:
- Additional edge case tests as needed to reach 20+ total

**Requirements Satisfied**: AC-001 through AC-005 verification

**Deliverables**:
- Complete sample_items.json with realistic Avenue One data
- Verify all acceptance criteria pass
- Final test count: 20+ tests

---

## Test Summary

| Phase | Test File | Test Count |
|-------|-----------|------------|
| 1 | test_models.py, test_tax.py | 8 |
| 2 | test_slug.py, test_validation.py | 8 |
| 3 | test_config.py | 6 |
| 4 | test_pdf.py | 4 |
| 5 | test_loader.py | 4 |
| 6 | test_app.py, test_invoice.py, test_estimate.py, test_properties.py, test_rates.py | 13 |
| 7 | test_interactive.py | 3 |
| **Total** | | **46** |

Target: 15 minimum (NFR-003). Planned: 46 tests.

---

## Dependency Versions

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "typer>=0.12,<1.0",
    "reportlab>=4.2,<5.0",
    "rich>=13.7,<14.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3,<9.0",
    "pytest-cov>=5.0,<6.0",
]
```

---

## Risks and Clarifications

### Resolved by Spec

1. **Tax calculation per-line vs subtotal**: Spec FR-001 explicitly states per-line calculation, then sum. Resolved.
2. **Filename collision handling**: Spec edge case says "overwrite or append suffix, to be determined." Decision: **Overwrite** (simpler, matches operator expectation for regenerating same-day documents).
3. **Em dash detection**: FR-008 requires no em dashes. Will validate all text inputs and raise error if detected.

### Requiring Implementation Decision

1. **PDF styling details**: Spec AC-005 references "existing Asantico style" but no style guide provided. Decision: Use clean professional layout with:
   - Business name in bold, 18pt
   - Document title (Invoice/Estimate) in bold, 24pt
   - Line item table with light gray header row
   - Subtotal/tax/total in right-aligned column
   - Footer in 10pt italic

2. **Property not in list behavior**: Spec edge case says "allow user to proceed or add to registry." Decision for file-based mode: Proceed with entered name, do not auto-add. Interactive mode will offer to add.

3. **Decimal precision**: Use Python `Decimal` with quantize to 2 places for all money calculations to avoid floating-point errors.

### Out of Scope Confirmed

- Email sending, web UI, database, multi-user, authentication, recurring invoices (per spec Out of Scope section).

---

## Next Steps

Run `/speckit-tasks` to generate actionable tasks from this plan.
