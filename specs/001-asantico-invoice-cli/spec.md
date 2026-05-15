# Feature Specification: Asantico Invoice CLI

**Feature Branch**: `001-asantico-invoice-cli`

**Created**: 2026-05-15

**Status**: Draft

**Input**: A Python CLI named `asantico` that generates professional PDF invoices and estimates for a Seattle property maintenance business. The operator runs the tool from the terminal, supplies a property, line items, and document type (invoice or estimate), and receives a styled PDF in ./output/.

---

## Product Summary

Asantico CLI is a command-line tool that generates professional PDF invoices and estimates for Asantico, a Seattle property maintenance business. The CLI replaces an ad-hoc ReportLab script with a structured, repeatable tool featuring config-driven property and rate management.

**Primary User**: A solo operator (the Asantico business owner, Eyob "Stark" Worku) who currently uses an ad-hoc ReportLab script and wants a structured, repeatable CLI with config-driven property and rate management.

**Primary Recipient**: Avenue One Residential (contacts: Andrew Miller, Saniya Zaveri).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Invoice from File (Priority: P1)

As an operator, I can run `asantico invoice new --from-file path/to/items.json --property "The Meridian"` and receive a professional PDF invoice in ./output/ with correct totals, tax calculations, and styling.

**Why this priority**: This is the core functionality. Invoice generation is the primary revenue-generating activity, and file-based input enables batch processing and repeatability for common jobs.

**Independent Test**: Can be fully tested by providing a sample JSON file with line items, running the command, and verifying the PDF output contains correct calculations, formatting, and all required sections.

**Acceptance Scenarios**:

1. **Given** a valid items.json file with line items and a configured property "The Meridian", **When** the operator runs `asantico invoice new --from-file items.json --property "The Meridian"`, **Then** a PDF is created in ./output/ named `invoice_the-meridian_2026-05-15.pdf` with correct subtotal, 10.55% tax per line, and total.
2. **Given** an items.json file with labor-only line items (unit: hr), **When** the operator generates an invoice, **Then** Seattle sales tax (10.55%) is applied to those labor lines.
3. **Given** a successful invoice generation, **When** the PDF is opened, **Then** it displays: Asantico header, Avenue One Residential recipient block, property name, document number (INV-0001 format), date, line item table, subtotal row, tax row, total row, and payment terms footer.

---

### User Story 2 - Generate Estimate from File (Priority: P1)

As an operator, I can run `asantico estimate new --from-file path/to/items.json --property "Garden"` and receive an estimate-styled PDF (no payment terms, "Estimate" title, validity period footer).

**Why this priority**: Estimates are equally critical for winning new work. The estimate flow shares 90% of invoice logic but differs in title, footer, and absence of payment terms.

**Independent Test**: Can be fully tested by running the estimate command with a sample JSON file and verifying the PDF has "Estimate" title, no payment terms, and includes a validity statement footer.

**Acceptance Scenarios**:

1. **Given** a valid items.json file and property "Garden", **When** the operator runs `asantico estimate new --from-file items.json --property "Garden"`, **Then** a PDF is created named `estimate_garden_2026-05-15.pdf` with "Estimate" as the document title.
2. **Given** a generated estimate PDF, **When** the operator reviews the footer, **Then** it contains a validity period statement (not payment terms).
3. **Given** a generated estimate, **When** the document number is checked, **Then** it follows the EST-0001 format (separate counter from invoices).

---

### User Story 3 - Interactive Invoice/Estimate Generation (Priority: P2)

As an operator, I can run `asantico invoice new` (or `asantico estimate new`) without flags and be prompted interactively for property selection, line items, and notes, then receive a PDF.

**Why this priority**: Interactive mode enables quick, one-off document generation when the operator does not have a pre-prepared JSON file. Important for flexibility but secondary to file-based workflow.

**Independent Test**: Can be tested by running the command and stepping through prompts, verifying each prompt appears in correct order and the final PDF reflects all entered data.

**Acceptance Scenarios**:

1. **Given** the operator runs `asantico invoice new` with no flags, **When** the CLI starts, **Then** it prompts for property selection (from configured list or new entry).
2. **Given** the operator is in interactive mode, **When** prompted for line items, **Then** they can enter description, quantity, unit (hr/each/flat), and unit price for each line, with an option to add more or finish.
3. **Given** all prompts are completed, **When** the operator confirms, **Then** a PDF is generated with all entered data.

---

### User Story 4 - Property Management (Priority: P2)

As an operator, I can run `asantico properties list`, `asantico properties add`, and `asantico properties remove` to manage my property registry stored in ~/.asantico/properties.json.

**Why this priority**: Property management enables the operator to maintain a reusable list of Avenue One locations, reducing repetitive data entry and ensuring consistency.

**Independent Test**: Can be tested by running each subcommand and verifying the properties.json file is created, updated, and reflects the changes.

**Acceptance Scenarios**:

1. **Given** no existing config, **When** the operator runs `asantico properties list`, **Then** the CLI creates ~/.asantico/properties.json with default properties and displays them.
2. **Given** an existing property list, **When** the operator runs `asantico properties add "New Property Name"`, **Then** the property is added to properties.json and confirmed.
3. **Given** a property exists, **When** the operator runs `asantico properties remove "Property Name"`, **Then** the property is removed and confirmed.

---

### User Story 5 - Rate Management (Priority: P3)

As an operator, I can run `asantico rates list` and `asantico rates set` to manage default labor and material rates stored in ~/.asantico/rates.json.

**Why this priority**: Rate management is a convenience feature for setting defaults. The operator can always override rates per line item, so this is lower priority than core document generation.

**Independent Test**: Can be tested by running rate commands and verifying rates.json is created and updated correctly.

**Acceptance Scenarios**:

1. **Given** no existing config, **When** the operator runs `asantico rates list`, **Then** the CLI creates ~/.asantico/rates.json with sensible defaults and displays them.
2. **Given** an existing rates config, **When** the operator runs `asantico rates set labor 75.00`, **Then** the labor rate is updated to $75.00 and confirmed.

---

### User Story 6 - CLI Help and Version (Priority: P3)

As an operator, I can run `asantico --version` and `asantico --help` for standard CLI affordances.

**Why this priority**: Standard CLI conventions. Important for usability but not core functionality.

**Independent Test**: Can be tested by running each flag and verifying appropriate output.

**Acceptance Scenarios**:

1. **Given** the CLI is installed, **When** the operator runs `asantico --help`, **Then** help text is displayed listing all commands and exits with code 0.
2. **Given** the CLI is installed, **When** the operator runs `asantico --version`, **Then** the version number is displayed.
3. **Given** the operator runs `asantico` with no arguments, **When** the CLI executes, **Then** help text is printed and the CLI exits with code 0.

---

### Edge Cases

- What happens when the specified property is not in the configured list? The CLI allows the user to proceed with the entered name or add it to the registry.
- What happens when items.json is malformed or missing required fields? The CLI exits non-zero with a clear Rich-formatted error message.
- What happens when quantity is negative or zero? The CLI rejects the input with a validation error.
- What happens when the output directory does not exist? The CLI creates ./output/ automatically.
- What happens when a PDF with the same filename already exists? The CLI overwrites it (or appends a numeric suffix, to be determined by implementation).
- What happens when ~/.asantico/ directory does not exist? The CLI creates it on first run with default config files.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute Seattle sales tax at 10.55% per line item, including labor-only lines. Tax is calculated per-line and summed, not applied once to the subtotal.
- **FR-002**: System MUST display in the PDF: business header (Asantico, Seattle WA), recipient block (Avenue One Residential, property name and address), document number, date, line item table, subtotal, tax row, total, and footer.
- **FR-003**: Invoice footer MUST contain payment terms. Estimate footer MUST contain a validity period statement instead of payment terms.
- **FR-004**: Document numbers MUST be auto-incrementing per document type, stored in ~/.asantico/counters.json (format: INV-0001, EST-0001).
- **FR-005**: Line items MUST support: description, quantity, unit (hr/each/flat), unit price, computed line total (qty x unit price), and computed line tax (line total x 10.55%).
- **FR-006**: All currency display MUST use $1,234.56 formatting (commas as thousand separators, two decimal places, USD).
- **FR-007**: PDF filenames MUST follow the pattern `{type}_{property-slug}_{YYYY-MM-DD}.pdf`. The property slug lowercases and replaces non-alphanumeric characters with hyphens.
- **FR-008**: No em dashes (Unicode U+2014) SHALL appear in any generated text or PDF content. Use commas, semicolons, or periods instead.
- **FR-009**: The CLI MUST exit non-zero on any validation failure (missing property, negative quantity, malformed JSON input) and print a clear error via Rich.
- **FR-010**: All config files MUST live under ~/.asantico/ and be created on first run with sensible defaults.
- **FR-011**: The CLI MUST support `asantico invoice new` and `asantico estimate new` commands with optional `--from-file` and `--property` flags.
- **FR-012**: The CLI MUST support `asantico properties list`, `asantico properties add <name>`, and `asantico properties remove <name>` commands.
- **FR-013**: The CLI MUST support `asantico rates list` and `asantico rates set <type> <value>` commands.
- **FR-014**: The CLI MUST support `asantico --help` and `asantico --version` flags.
- **FR-015**: Interactive mode MUST prompt for property selection from configured list or allow new entry.
- **FR-016**: Interactive mode MUST prompt for line items with description, quantity, unit, and unit price fields.
- **FR-017**: PDFs MUST be written to ./output/ directory by default, creating it if it does not exist.

### Non-Functional Requirements

- **NFR-001**: All business logic (tax calculation, totals, filename generation, slugification) MUST live in pure functions, unit-testable without PDF rendering.
- **NFR-002**: PDF rendering MUST be isolated in a single module so it can be swapped or mocked in tests.
- **NFR-003**: Test coverage target: at least one happy-path and one error-path test per command, plus full coverage of tax and total calculations. Minimum 15 tests.
- **NFR-004**: The CLI MUST run on Python 3.13 with no system-level dependencies beyond what pip installs.
- **NFR-005**: Zero network calls. The CLI MUST work fully offline.
- **NFR-006**: The CLI MUST use Typer for command parsing, ReportLab for PDF rendering, and Rich for terminal output.

### Key Entities

- **Line Item**: A single billable entry with description, quantity, unit, unit price, computed line total, and computed line tax. Represents work performed or materials provided.
- **Document**: Either an Invoice or Estimate. Contains metadata (number, date, type), property reference, collection of line items, subtotal, total tax, and grand total.
- **Property**: A real estate location managed by Avenue One Residential. Has a name and optional address. Stored in the property registry.
- **Rate**: A default price per unit for labor or materials. Stored in rates config for convenience.
- **Counter**: A persistent auto-incrementing integer per document type, used to generate document numbers.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operator can generate a complete invoice PDF in under 30 seconds from command entry to file output.
- **SC-002**: Operator can generate an estimate PDF with identical ease, differing only in title and footer content.
- **SC-003**: All tax calculations match expected values (10.55% per line, summed for total tax) with no rounding errors visible to two decimal places.
- **SC-004**: Generated PDFs are visually professional and match the existing Asantico style: clean header, organized line-item table, clear subtotal/tax/total rows, appropriate footer.
- **SC-005**: The CLI handles all common error conditions gracefully, displaying clear error messages without stack traces.
- **SC-006**: The test suite passes with at least 15 tests covering core functionality.
- **SC-007**: The CLI works entirely offline with no network dependencies.

---

## Assumptions

- The operator has Python 3.13 installed and can run pip install commands.
- The operator works from a terminal (macOS, Linux, or Windows with appropriate shell).
- Avenue One Residential is the sole recipient for all documents in Sprint 1.
- The existing Asantico visual style (header layout, fonts, colors) will be documented or provided for PDF rendering.
- Config files in ~/.asantico/ use JSON format for simplicity and human readability.
- The operator is comfortable with JSON file format for batch line-item input.
- Default properties list includes common Avenue One locations: Garden, The Meridian, Portal, Aprea View, Gilman's Fairway, Linden Avenue Condominiums, Canterbury Shores, Koda Condominiums, Clark Roadhouse.

---

## Out of Scope for Sprint 1

- Sending emails or SMTP integration
- Web UI or REST API
- Database persistence beyond JSON config files
- Multi-user or multi-tenant support
- Recurring invoices, payment tracking, accounts receivable
- Authentication or access control

---

## Acceptance Criteria for Sprint 1

- **AC-001**: `asantico invoice new --from-file examples/sample_items.json --property "The Meridian"` produces a valid PDF in ./output/ with correct totals and tax.
- **AC-002**: `asantico estimate new --from-file examples/sample_items.json --property "Garden"` produces an estimate-styled PDF with "Estimate" title and validity footer.
- **AC-003**: `pytest` passes with at least 15 tests covering tax math, slug generation, filename construction, config loading, and command dispatch.
- **AC-004**: Running `asantico` with no command prints help text and exits 0.
- **AC-005**: Generated PDFs visually match the existing Asantico style: clean header, line-item table, subtotal and tax rows, total row, footer.

---

## Glossary

| Term | Definition |
|------|------------|
| **Line Item** | A single billable entry on an invoice or estimate, containing a description, quantity, unit of measure (hr/each/flat), unit price, and computed totals. Each line item has tax calculated individually. |
| **Document Number** | A unique identifier for each invoice or estimate, auto-incremented per document type. Invoices use INV-0001 format; estimates use EST-0001 format. Stored in ~/.asantico/counters.json. |
| **Slug** | A URL-safe, lowercase version of a property name where non-alphanumeric characters are replaced with hyphens. Used in PDF filenames (e.g., "The Meridian" becomes "the-meridian"). |
| **Property** | A real estate location serviced by Asantico, typically managed by Avenue One Residential. Properties are stored in a registry at ~/.asantico/properties.json for reuse across documents. |
| **Rate** | A default price per unit for a type of work (labor) or materials. Stored in ~/.asantico/rates.json. Rates can be overridden per line item during document creation. |

---

## Requirement Traceability Matrix

This section maps each Functional Requirement (FR) and Non-Functional Requirement (NFR) to the User Stories (US) and Acceptance Criteria (AC) they support.

### Functional Requirements Traceability

| Requirement | User Stories | Acceptance Criteria | Description |
|-------------|--------------|---------------------|-------------|
| FR-001 | US-1, US-2 | AC-001, AC-002 | Seattle sales tax at 10.55% per line item |
| FR-002 | US-1, US-2 | AC-001, AC-002, AC-005 | PDF layout with header, recipient, line items, totals, footer |
| FR-003 | US-1, US-2 | AC-001, AC-002 | Invoice payment terms vs estimate validity footer |
| FR-004 | US-1, US-2 | AC-001, AC-002 | Auto-incrementing document numbers (INV/EST format) |
| FR-005 | US-1, US-2, US-3 | AC-001, AC-002 | Line item structure with computed totals and tax |
| FR-006 | US-1, US-2 | AC-001, AC-002, AC-005 | USD currency formatting ($1,234.56) |
| FR-007 | US-1, US-2 | AC-001, AC-002 | PDF filename pattern with property slug and date |
| FR-008 | US-1, US-2 | AC-001, AC-002, AC-005 | No em dashes in generated content |
| FR-009 | US-1, US-2, US-3 | AC-001, AC-002 | Non-zero exit on validation failure with Rich errors |
| FR-010 | US-4, US-5 | AC-003 | Config files in ~/.asantico/ with defaults |
| FR-011 | US-1, US-2, US-3 | AC-001, AC-002 | invoice/estimate new commands with flags |
| FR-012 | US-4 | AC-003 | properties list/add/remove commands |
| FR-013 | US-5 | AC-003 | rates list/set commands |
| FR-014 | US-6 | AC-004 | --help and --version flags |
| FR-015 | US-3 | AC-003 | Interactive property selection |
| FR-016 | US-3 | AC-003 | Interactive line item entry |
| FR-017 | US-1, US-2, US-3 | AC-001, AC-002 | Output to ./output/ directory |

### Non-Functional Requirements Traceability

| Requirement | User Stories | Acceptance Criteria | Description |
|-------------|--------------|---------------------|-------------|
| NFR-001 | US-1, US-2 | AC-003 | Pure functions for business logic (testability) |
| NFR-002 | US-1, US-2 | AC-003, AC-005 | Isolated PDF rendering module |
| NFR-003 | All | AC-003 | Minimum 15 tests with coverage targets |
| NFR-004 | All | AC-001, AC-002, AC-003 | Python 3.13, pip-only dependencies |
| NFR-005 | All | AC-001, AC-002 | Fully offline operation |
| NFR-006 | All | AC-001, AC-002, AC-005 | Typer, ReportLab, Rich stack |

### Acceptance Criteria Coverage

| Acceptance Criterion | Functional Requirements | Non-Functional Requirements |
|---------------------|------------------------|----------------------------|
| AC-001 | FR-001 through FR-011, FR-017 | NFR-001, NFR-002, NFR-004, NFR-005, NFR-006 |
| AC-002 | FR-001 through FR-011, FR-017 | NFR-001, NFR-002, NFR-004, NFR-005, NFR-006 |
| AC-003 | FR-010, FR-012, FR-013, FR-015, FR-016 | NFR-001, NFR-002, NFR-003, NFR-004 |
| AC-004 | FR-014 | NFR-004 |
| AC-005 | FR-002, FR-006, FR-008 | NFR-002, NFR-006 |
