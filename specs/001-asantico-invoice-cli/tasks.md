# Tasks: Asantico Invoice CLI

**Input**: Design documents from `/specs/001-asantico-invoice-cli/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Included as required by NFR-003 (minimum 15 tests)

**Organization**: Tasks are grouped by the 8 phases from plan.md, with user story labels where applicable.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- All file paths are relative to repository root

---

## Phase 1: Domain Models and Tax Math

**Goal**: Establish core data structures and tax calculation logic (FR-001, FR-005, FR-006, NFR-001)

**Files Created**: `src/asantico_cli/__init__.py`, `src/asantico_cli/domain/__init__.py`, `src/asantico_cli/domain/models.py`, `src/asantico_cli/domain/tax.py`

**Tests Added**: `tests/__init__.py`, `tests/unit/__init__.py`, `tests/unit/test_models.py`, `tests/unit/test_tax.py`

### Setup Tasks

- [x] T001 Create package structure: `src/asantico_cli/__init__.py` with `__version__ = "0.1.0"`
- [x] T002 [P] Create domain package: `src/asantico_cli/domain/__init__.py`
- [x] T003 [P] Create test package structure: `tests/__init__.py`, `tests/unit/__init__.py`

### Implementation Tasks

- [x] T004 Implement `LineItem` dataclass with computed `line_total` and `line_tax` properties in `src/asantico_cli/domain/models.py`
- [x] T005 Implement `Document` dataclass with computed `subtotal`, `total_tax`, `grand_total` properties in `src/asantico_cli/domain/models.py`
- [x] T006 [P] Implement `Property` dataclass with `name`, `address`, and computed `slug` property in `src/asantico_cli/domain/models.py`
- [x] T007 [P] Implement `Rate` dataclass in `src/asantico_cli/domain/models.py`
- [x] T008 Implement `SEATTLE_TAX_RATE`, `VALID_UNITS`, `DOC_TYPE_*`, `DOC_PREFIX` constants in `src/asantico_cli/domain/models.py`
- [x] T009 Implement `compute_line_tax(line_total: Decimal) -> Decimal` in `src/asantico_cli/domain/tax.py`
- [x] T010 Implement `compute_totals(line_items: list[LineItem]) -> tuple[Decimal, Decimal, Decimal]` in `src/asantico_cli/domain/tax.py`
- [x] T011 Implement `format_currency(amount: Decimal) -> str` returning `$1,234.56` format in `src/asantico_cli/domain/tax.py`

### Test Tasks

- [x] T012 [P] Write tests for `LineItem` creation and computed properties in `tests/unit/test_models.py` (3 tests)
- [x] T013 [P] Write tests for `Document` creation and computed properties in `tests/unit/test_models.py` (2 tests)
- [x] T014 [P] Write tests for `Property` creation and slug generation in `tests/unit/test_models.py` (2 tests)
- [x] T015 Write tests for `compute_line_tax` in `tests/unit/test_tax.py` (3 tests: basic, labor, rounding)
- [x] T016 Write tests for `compute_totals` in `tests/unit/test_tax.py` (2 tests: single item, multiple items)
- [x] T017 Write tests for `format_currency` in `tests/unit/test_tax.py` (2 tests: with commas, zero)

**Checkpoint**: Run `pytest tests/unit/` and verify 14 tests pass. All business logic is pure functions. **PASSED (21 tests)**

---

## Phase 2: Slug, Filename, and Validation

**Goal**: Implement filename generation and input validation (FR-007, FR-008, FR-009, NFR-001)

**Files Created**: `src/asantico_cli/domain/slug.py`, `src/asantico_cli/domain/validation.py`

**Tests Added**: `tests/unit/test_slug.py`, `tests/unit/test_validation.py`

### Implementation Tasks

- [x] T018 Implement `slugify_property_name(name: str) -> str` in `src/asantico_cli/domain/slug.py`
- [x] T019 Implement `build_pdf_filename(doc_type: str, property_name: str, date: date) -> str` in `src/asantico_cli/domain/slug.py`
- [x] T020 Implement `contains_em_dash(text: str) -> bool` in `src/asantico_cli/domain/validation.py`
- [x] T021 Implement `validate_line_item(item: LineItem) -> list[str]` in `src/asantico_cli/domain/validation.py`
- [x] T022 Implement `validate_property_name(name: str) -> list[str]` in `src/asantico_cli/domain/validation.py`

### Test Tasks

- [x] T023 [P] Write tests for `slugify_property_name` in `tests/unit/test_slug.py` (3 tests: basic, apostrophe, spaces)
- [x] T024 [P] Write tests for `build_pdf_filename` in `tests/unit/test_slug.py` (2 tests: invoice, estimate)
- [x] T025 [P] Write tests for `contains_em_dash` in `tests/unit/test_validation.py` (2 tests: has em dash, no em dash)
- [x] T026 [P] Write tests for `validate_line_item` in `tests/unit/test_validation.py` (4 tests: valid, negative qty, zero qty, em dash in description)
- [x] T027 [P] Write tests for `validate_property_name` in `tests/unit/test_validation.py` (2 tests: valid, em dash)

**Checkpoint**: Run `pytest tests/unit/` and verify 27 tests pass. Slug and validation are pure functions. **PASSED (43 tests)**

---

## Phase 3: Config Persistence Layer

**Goal**: Implement JSON config file management under ~/.asantico/ (FR-004, FR-010, FR-012, FR-013)

**Files Created**: `src/asantico_cli/infra/__init__.py`, `src/asantico_cli/infra/config.py`

**Tests Added**: `tests/integration/__init__.py`, `tests/integration/test_config.py`

### Implementation Tasks

- [x] T028 Create infra package: `src/asantico_cli/infra/__init__.py`
- [x] T029 [P] Create integration test package: `tests/integration/__init__.py`
- [x] T030 Implement `get_config_dir() -> Path` and `ensure_config_dir() -> None` in `src/asantico_cli/infra/config.py`
- [x] T031 Implement `load_properties() -> list[Property]` with default properties in `src/asantico_cli/infra/config.py`
- [x] T032 Implement `save_properties(properties: list[Property]) -> None` in `src/asantico_cli/infra/config.py`
- [x] T033 Implement `load_rates() -> dict[str, Decimal]` with defaults ($65 labor, $0 materials) in `src/asantico_cli/infra/config.py`
- [x] T034 Implement `save_rates(rates: dict[str, Decimal]) -> None` in `src/asantico_cli/infra/config.py`
- [x] T035 Implement `load_counters() -> dict[str, int]` in `src/asantico_cli/infra/config.py`
- [x] T036 Implement `increment_counter(doc_type: str) -> str` returning INV-0001/EST-0001 format in `src/asantico_cli/infra/config.py`

### Test Tasks

- [x] T037 Write test for `ensure_config_dir` creates directory in `tests/integration/test_config.py` using `tmp_path`
- [x] T038 Write tests for `load_properties` and `save_properties` in `tests/integration/test_config.py` (2 tests)
- [x] T039 Write tests for `load_rates` and `save_rates` in `tests/integration/test_config.py` (2 tests)
- [x] T040 Write tests for `load_counters` and `increment_counter` in `tests/integration/test_config.py` (2 tests)

**Checkpoint**: Run `pytest tests/` and verify 33 tests pass. Config uses `tmp_path` to avoid polluting real ~/.asantico/. **PASSED (54 tests)**

---

## Phase 4: PDF Renderer

**Goal**: Implement ReportLab PDF generation with Asantico styling (FR-002, FR-003, FR-017, NFR-002)

**Files Created**: `src/asantico_cli/infra/pdf.py`

**Tests Added**: `tests/integration/test_pdf.py`

### Implementation Tasks

- [x] T041 [US1] [US2] Create PDF renderer module structure in `src/asantico_cli/infra/pdf.py`
- [x] T042 [US1] [US2] Implement header rendering (Asantico, Seattle WA) in `src/asantico_cli/infra/pdf.py`
- [x] T043 [US1] [US2] Implement recipient block (Avenue One Residential, property) in `src/asantico_cli/infra/pdf.py`
- [x] T044 [US1] [US2] Implement document info section (number, date, type title) in `src/asantico_cli/infra/pdf.py`
- [x] T045 [US1] [US2] Implement line item table with gray header in `src/asantico_cli/infra/pdf.py`
- [x] T046 [US1] [US2] Implement summary section (subtotal, tax, total) in `src/asantico_cli/infra/pdf.py`
- [x] T047 [US1] Implement invoice footer (payment terms) in `src/asantico_cli/infra/pdf.py`
- [x] T048 [US2] Implement estimate footer (validity period) in `src/asantico_cli/infra/pdf.py`
- [x] T049 [US1] [US2] Implement `render_pdf(document: Document, output_dir: Path) -> Path` in `src/asantico_cli/infra/pdf.py`

### Test Tasks

- [x] T050 [P] Write test for invoice PDF creation in `tests/integration/test_pdf.py` using `tmp_path`
- [x] T051 [P] Write test for estimate PDF creation in `tests/integration/test_pdf.py`
- [x] T052 Write test for output directory auto-creation in `tests/integration/test_pdf.py`
- [x] T053 Write test for PDF contains required sections in `tests/integration/test_pdf.py`

**Checkpoint**: Run `pytest tests/` and verify 37 tests pass. PDF module is isolated and mockable. **PASSED (60 tests)**

---

## Phase 5: JSON Loader

**Goal**: Load line items from JSON file with schema validation (FR-005, FR-009)

**Files Created**: `src/asantico_cli/infra/loader.py`, `examples/sample_items.json`

**Tests Added**: `tests/integration/test_loader.py`

### Implementation Tasks

- [ ] T054 [US1] [US2] Implement `load_line_items(path: Path) -> list[LineItem]` in `src/asantico_cli/infra/loader.py`
- [ ] T055 [US1] [US2] Add JSON schema validation with Rich error messages in `src/asantico_cli/infra/loader.py`
- [ ] T056 Create sample `examples/sample_items.json` with realistic Avenue One line items

### Test Tasks

- [ ] T057 [P] Write test for loading valid JSON in `tests/integration/test_loader.py`
- [ ] T058 [P] Write test for missing file error in `tests/integration/test_loader.py`
- [ ] T059 [P] Write test for malformed JSON error in `tests/integration/test_loader.py`
- [ ] T060 Write test for invalid schema error in `tests/integration/test_loader.py`

**Checkpoint**: Run `pytest tests/` and verify 41 tests pass.

---

## Phase 6: CLI Entrypoint and Subcommands

**Goal**: Implement Typer CLI with all commands (FR-011 through FR-014, NFR-006)

**Files Created**: `src/asantico_cli/cli/__init__.py`, `src/asantico_cli/cli/app.py`, `src/asantico_cli/cli/invoice.py`, `src/asantico_cli/cli/estimate.py`, `src/asantico_cli/cli/properties.py`, `src/asantico_cli/cli/rates.py`

**Tests Added**: `tests/cli/__init__.py`, `tests/cli/test_app.py`, `tests/cli/test_invoice.py`, `tests/cli/test_estimate.py`, `tests/cli/test_properties.py`, `tests/cli/test_rates.py`

### Setup Tasks

- [ ] T061 Create CLI package: `src/asantico_cli/cli/__init__.py`
- [ ] T062 [P] Create CLI test package: `tests/cli/__init__.py`
- [ ] T063 Create `pyproject.toml` with entry point `asantico = "asantico_cli.cli.app:app"` and dependencies

### Implementation Tasks

- [ ] T064 [US6] Implement main Typer app with `--version` and `--help` in `src/asantico_cli/cli/app.py`
- [ ] T065 [US1] Implement `invoice new` command with `--from-file` and `--property` flags in `src/asantico_cli/cli/invoice.py`
- [ ] T066 [US2] Implement `estimate new` command with `--from-file` and `--property` flags in `src/asantico_cli/cli/estimate.py`
- [ ] T067 [US4] Implement `properties list` command in `src/asantico_cli/cli/properties.py`
- [ ] T068 [US4] Implement `properties add` command with `--address` flag in `src/asantico_cli/cli/properties.py`
- [ ] T069 [US4] Implement `properties remove` command in `src/asantico_cli/cli/properties.py`
- [ ] T070 [US5] Implement `rates list` command in `src/asantico_cli/cli/rates.py`
- [ ] T071 [US5] Implement `rates set` command in `src/asantico_cli/cli/rates.py`
- [ ] T072 Register all subcommands in `src/asantico_cli/cli/app.py`

### Test Tasks

- [ ] T073 [P] [US6] Write tests for `--help` and `--version` in `tests/cli/test_app.py` using CliRunner (3 tests)
- [ ] T074 [P] [US1] Write tests for `invoice new --from-file` in `tests/cli/test_invoice.py` (3 tests: success, missing property, invalid JSON)
- [ ] T075 [P] [US2] Write tests for `estimate new --from-file` in `tests/cli/test_estimate.py` (2 tests: success, correct title)
- [ ] T076 [P] [US4] Write tests for `properties` commands in `tests/cli/test_properties.py` (3 tests: list, add, remove)
- [ ] T077 [P] [US5] Write tests for `rates` commands in `tests/cli/test_rates.py` (2 tests: list, set)

**Checkpoint**: Run `pytest tests/` and verify 54 tests pass. CLI is installable via `pip install -e .`.

---

## Phase 7: Interactive Mode Prompts

**Goal**: Add Rich-based interactive prompts for document creation without flags (FR-015, FR-016)

**Files Created**: `src/asantico_cli/cli/interactive.py`

**Tests Added**: `tests/cli/test_interactive.py`

### Implementation Tasks

- [ ] T078 [US3] Implement `prompt_property_selection(properties: list[Property]) -> Property` in `src/asantico_cli/cli/interactive.py`
- [ ] T079 [US3] Implement `prompt_line_items() -> list[LineItem]` in `src/asantico_cli/cli/interactive.py`
- [ ] T080 [US3] Implement `prompt_confirmation(document: Document) -> bool` in `src/asantico_cli/cli/interactive.py`
- [ ] T081 [US3] Integrate interactive mode into `invoice new` when `--from-file` not provided in `src/asantico_cli/cli/invoice.py`
- [ ] T082 [US3] Integrate interactive mode into `estimate new` when `--from-file` not provided in `src/asantico_cli/cli/estimate.py`

### Test Tasks

- [ ] T083 [P] [US3] Write test for property selection prompt in `tests/cli/test_interactive.py`
- [ ] T084 [P] [US3] Write test for line item entry prompt in `tests/cli/test_interactive.py`
- [ ] T085 [US3] Write test for confirmation prompt in `tests/cli/test_interactive.py`

**Checkpoint**: Run `pytest tests/` and verify 57 tests pass. Interactive mode works without `--from-file`.

---

## Phase 8: Examples, README, and Polish

**Goal**: Finalize documentation, examples, and edge case handling (AC-001 through AC-005 verification)

**Files Updated**: `examples/sample_items.json`, `pyproject.toml`

### Documentation Tasks

- [ ] T086 [P] Update `examples/sample_items.json` with comprehensive Avenue One data (multiple properties, line item types)
- [ ] T087 [P] Verify `pyproject.toml` has correct metadata (name, version, author, description)
- [ ] T088 Add `.gitignore` entry for `output/` directory

### Verification Tasks

- [ ] T089 Run AC-001: `asantico invoice new --from-file examples/sample_items.json --property "The Meridian"` produces valid PDF
- [ ] T090 Run AC-002: `asantico estimate new --from-file examples/sample_items.json --property "Garden"` produces estimate PDF
- [ ] T091 Run AC-003: `pytest` passes with at least 15 tests (target: 57)
- [ ] T092 Run AC-004: `asantico` with no arguments prints help and exits 0
- [ ] T093 Run AC-005: Generated PDFs have correct styling (header, table, subtotal/tax/total, footer)

### Polish Tasks

- [ ] T094 [P] Add sample PDF outputs to `examples/` for reference
- [ ] T095 [P] Create `.claude/skills/asantico-invoice-formatter/SKILL.md` custom skill (per CLAUDE.md)
- [ ] T096 [P] Create `.claude/settings.json` with pre-commit hook running tests (per CLAUDE.md)

**Checkpoint**: All acceptance criteria verified. Sprint 1 complete.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Domain Models) ─┬─> Phase 2 (Slug/Validation) ─┬─> Phase 3 (Config) ─> Phase 4 (PDF) ─┐
                         │                              │                                       │
                         └──────────────────────────────┴───────────────────────────────────────┤
                                                                                                │
Phase 5 (Loader) <──────────────────────────────────────────────────────────────────────────────┤
                                                                                                │
Phase 6 (CLI) <─────────────────────────────────────────────────────────────────────────────────┤
                                                                                                │
Phase 7 (Interactive) <─────────────────────────────────────────────────────────────────────────┤
                                                                                                │
Phase 8 (Polish) <──────────────────────────────────────────────────────────────────────────────┘
```

- **Phase 1**: No dependencies, start immediately
- **Phase 2**: Depends on Phase 1 models (LineItem for validation)
- **Phase 3**: Depends on Phase 1 models (Property, Rate)
- **Phase 4**: Depends on Phase 1 models (Document) and Phase 2 (slug)
- **Phase 5**: Depends on Phase 1 models (LineItem) and Phase 2 (validation)
- **Phase 6**: Depends on Phases 1-5 (all domain and infra layers)
- **Phase 7**: Depends on Phase 6 (CLI structure)
- **Phase 8**: Depends on all phases

### User Story Dependencies

| User Story | Phase | Dependencies |
|------------|-------|--------------|
| US1 (Invoice from File) | 4, 5, 6 | Foundational phases 1-3 |
| US2 (Estimate from File) | 4, 5, 6 | Foundational phases 1-3 |
| US3 (Interactive Mode) | 7 | US1, US2 complete |
| US4 (Property Management) | 3, 6 | Phase 1 models |
| US5 (Rate Management) | 3, 6 | Phase 1 models |
| US6 (Help/Version) | 6 | Phase 1 package structure |

### Within Each Phase

- Tasks marked [P] can run in parallel
- Test tasks depend on corresponding implementation tasks
- Checkpoint must pass before moving to next phase

### Parallel Opportunities

**Phase 1 Parallel Groups:**
```bash
# Group A: Package structure (T001, T002, T003)
# Group B: Models (T004, T005, T006, T007, T008) - after T002
# Group C: Tax functions (T009, T010, T011) - after T004
# Group D: Tests (T012, T013, T014, T015, T016, T017) - after implementations
```

**Phase 6 Parallel Groups:**
```bash
# Group A: All CLI command files (T065, T066, T067, T068, T069, T070, T071) - after T064
# Group B: All CLI tests (T073, T074, T075, T076, T077) - after implementations
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2)

1. Complete Phase 1: Domain Models (T001-T017)
2. Complete Phase 2: Slug/Validation (T018-T027)
3. Complete Phase 3: Config (T028-T040)
4. Complete Phase 4: PDF (T041-T053)
5. Complete Phase 5: Loader (T054-T060)
6. Complete Phase 6: CLI commands for invoice/estimate (T061-T077)
7. **STOP and VALIDATE**: Run `asantico invoice new --from-file examples/sample_items.json --property "The Meridian"`
8. MVP delivered: File-based invoice and estimate generation

### Incremental Delivery

1. **MVP**: File-based invoice/estimate (US1, US2)
2. **+Property Management**: US4 (already in Phase 6)
3. **+Rate Management**: US5 (already in Phase 6)
4. **+Interactive Mode**: US3 (Phase 7)
5. **+Polish**: Phase 8

---

## Definition of Done (Sprint 1)

### Functional Requirements

- [ ] FR-001: Seattle sales tax (10.55%) calculated per line item
- [ ] FR-002: PDF layout with header, recipient, line items, totals, footer
- [ ] FR-003: Invoice has payment terms footer; estimate has validity footer
- [ ] FR-004: Document numbers auto-increment (INV-0001, EST-0001)
- [ ] FR-005: Line items with description, qty, unit, price, computed totals
- [ ] FR-006: Currency formatted as $1,234.56
- [ ] FR-007: PDF filename pattern `{type}_{slug}_{date}.pdf`
- [ ] FR-008: No em dashes in any generated content
- [ ] FR-009: Non-zero exit on validation errors with Rich messages
- [ ] FR-010: Config files in ~/.asantico/ created on first run
- [ ] FR-011: `invoice new` and `estimate new` commands work
- [ ] FR-012: `properties list/add/remove` commands work
- [ ] FR-013: `rates list/set` commands work
- [ ] FR-014: `--help` and `--version` flags work
- [ ] FR-015: Interactive property selection works
- [ ] FR-016: Interactive line item entry works
- [ ] FR-017: PDFs written to ./output/ (auto-created)

### Non-Functional Requirements

- [ ] NFR-001: All business logic in pure functions
- [ ] NFR-002: PDF rendering isolated in single module
- [ ] NFR-003: At least 15 tests (target: 57)
- [ ] NFR-004: Works on Python 3.13 with pip dependencies only
- [ ] NFR-005: Zero network calls (fully offline)
- [ ] NFR-006: Uses Typer, ReportLab, Rich

### Acceptance Criteria

- [ ] AC-001: `asantico invoice new --from-file examples/sample_items.json --property "The Meridian"` produces valid PDF
- [ ] AC-002: `asantico estimate new --from-file examples/sample_items.json --property "Garden"` produces estimate PDF
- [ ] AC-003: `pytest` passes with at least 15 tests
- [ ] AC-004: `asantico` with no args prints help and exits 0
- [ ] AC-005: PDFs visually match Asantico style

### Deliverables

- [ ] All source code in `src/asantico_cli/`
- [ ] All tests in `tests/`
- [ ] Sample JSON in `examples/sample_items.json`
- [ ] Sample PDFs in `examples/` (committed for reference)
- [ ] Custom skill in `.claude/skills/asantico-invoice-formatter/SKILL.md`
- [ ] Pre-commit hook in `.claude/settings.json`
- [ ] `pyproject.toml` with correct entry point and dependencies

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to user story for traceability
- Each phase has a checkpoint to validate before continuing
- Commit after each task or logical group
- Run `pytest` frequently to catch regressions
- Avoid: vague tasks, same file conflicts, skipping checkpoints
