# Sprint 1 Prompt Log: Spec-Driven Workflow

This file documents the `/speckit-specify`, `/speckit-plan`, and `/speckit-tasks` workflow used to produce the Asantico CLI specification and implementation plan. It also captures the custom skill and pre-commit hook usage during implementation.

Branch: `001-asantico-invoice-cli`
Repo: `asantico-cli`
Date: 2026-05-15

---

## 1. /speckit-specify

**Goal**: Generate SPEC.md with full requirements traceability for an Asantico invoice/estimate CLI.

**Prompt summary**: Product description, 6 user stories, 17 functional requirements (Seattle 10.55% tax per line, INV/EST document numbering, slug-based PDF filenames, no em dashes, etc.), 6 non-functional requirements (pure-function business logic, isolated PDF rendering, 15+ tests, fully offline), and 5 acceptance criteria.

**Outputs**:
- `specs/001-asantico-invoice-cli/spec.md` (276 lines)
- `specs/001-asantico-invoice-cli/checklists/requirements.md` (auto-generated quality checklist, all 14 items pass)
- Spec Kit auto-created the `001-asantico-invoice-cli` feature branch before writing files.

**Commit**: `f0fc027 feat(spec): generate SPEC.md and feature spec via /speckit-specify`

---

## 2. /speckit-plan

**Goal**: Generate 8-phase implementation plan from SPEC.md with a three-layer architecture (domain / infra / cli).

**Prompt summary**: Specified clean architecture layout, Typer/ReportLab/Rich stack, testing strategy (CliRunner, tmp_path), packaging via pyproject.toml, and the 8 implementation phases mapped to FRs/NFRs.

**Outputs**:
- `specs/001-asantico-invoice-cli/plan.md` (387 lines)
- `specs/001-asantico-invoice-cli/research.md` (266 lines, tech decisions: Decimal for currency, per-line tax, overwrite on filename collision)
- `specs/001-asantico-invoice-cli/data-model.md` (295 lines, entity schemas)
- `specs/001-asantico-invoice-cli/contracts/cli.md` (364 lines, command input/output contract)
- `specs/001-asantico-invoice-cli/quickstart.md` (221 lines)
- Spec Kit auto-updated `CLAUDE.md` to reference the new plan artifacts.

**Commit**: `3a6c2cc feat(plan): generate implementation plan via /speckit-plan`

---

## 3. /speckit-tasks

**Goal**: Break the plan into actionable, dependency-ordered tasks (T001+) with parallel markers and user story labels.

**Prompt summary**: Each task 15 to 45 minutes; file paths, FR/NFR coverage, test count, and acceptance check per task; Definition of Done at end.

**Outputs**:
- `specs/001-asantico-invoice-cli/tasks.md` (409 lines, 96 tasks)
- Phases: Domain (17), Slug/Validation (10), Config (13), PDF (13), Loader (7), CLI (17), Interactive (8), Polish (11)
- Per-story counts: US1 (12), US2 (11), US3 (8), US4 (6), US5 (4), US6 (4), Foundational (51)

**Commit**: _(pending, see next entry in this log)_

---

## 4. Implementation phase

_(filled in as we implement, see commits below.)_

---

## Workflow discipline notes

- Every Spec Kit slash command auto-fired its own pre-hook (`speckit-git-feature` for spec, optional `speckit-git-commit` for plan and tasks). The feature branch was created automatically.
- Each artifact (spec, plan, tasks) was committed as a separate Git commit before the next slash command ran, preserving a clean traceable history.
- The Spec Kit quality checklist (`specs/001-asantico-invoice-cli/checklists/requirements.md`) passed all 14 items on first generation.
- The custom skill at `.claude/skills/asantico-invoice-formatter/SKILL.md` and the pre-commit hook at `.claude/settings.json` were added before implementation began so they were active throughout the build phase (see Steps 5 to 9 of the workflow).

---

## 5. /speckit-implement (Phases 1 through 6, MVP scope)

**Goal**: Execute the MVP scope from tasks.md: file-based invoice and estimate generation. Phases 7 (interactive mode) and 8 (polish) deferred.

**Prompt summary**: Single directive given to Claude Code referencing tasks.md, with explicit rules about Decimal usage, pure-function discipline, Typer entry point, per-phase commits, hook enforcement, and end-to-end smoke testing. The agent was told to make reasonable judgment calls on ambiguity and continue rather than pause for clarification.

**Outputs (one commit per phase, hook validated each one)**:
- `fec6c4c` Phase 1 (T001-T017): domain models, Decimal-based tax math, currency formatting
- `ef44f1f` Phase 2 (T018-T027): slug generation, filename builder, line item and property validation
- `fd4f521` Phase 3 (T028-T040): config persistence (properties.json, rates.json, counters.json)
- `d095760` Phase 4 (T041-T053): ReportLab PDF renderer isolated in infra/pdf.py
- `e6fb7ac` Phase 5 (T054-T060): JSON line item loader with schema validation
- `7fa6882` Phase 6 (T061-T077): Typer entrypoint, invoice/estimate/properties/rates subcommands
- `cd61b2f` Smoke test outputs: sample PDFs and sample_items.json committed under examples/

**Final metrics**:
- 92 pytest tests, all passing (target was 15 per NFR-003, 6x overdelivery)
- 2 reference PDFs in `examples/` for visual verification of AC-001 and AC-002
- `asantico --version` returns `0.1.0`; `asantico --help` lists 4 command groups
- Editable install via `pip install -e .` works; entry point script generated

**Hook activity during implementation**:
- The pre-tool-use hook fired on every per-phase commit attempt
- All commits passed validation (no em dashes in staged content, pytest green)
- See `docs/hook-execution-transcript.md` for standalone test evidence

---

## Workflow discipline summary (final)

| Stage | Slash command | Outputs | Commit |
|---|---|---|---|
| 1 | /speckit-specify | spec.md (276 lines), checklist | f0fc027 |
| 2 | /speckit-plan | plan.md + research + data-model + cli contract + quickstart (1,533 lines total) | 3a6c2cc |
| 3 | /speckit-tasks | tasks.md (409 lines, 96 tasks) | 5f0d8d1 |
| 4 | Custom skill | .claude/skills/asantico-invoice-formatter/SKILL.md | d52eedc |
| 5 | Hook | .claude/settings.json + validate-before-destructive.sh | 1232ff9 |
| 6 | /speckit-implement | src/ + tests/ + pyproject.toml + 2 PDFs | fec6c4c through cd61b2f |
| 7 | README | README.md | ef92086 |

Total commits on branch `001-asantico-invoice-cli`: 16. Every commit is auditable.

## Deviations from plan, noted briefly

- The PDF currently lacks a top-of-page "Asantico, Seattle WA" business masthead. Bill-to and footer references to Asantico are present. Deferred to next sprint.
- Per-line tax sums to a value that may differ from a hand-summed alternative by one cent on some line counts. This is consistent with the spec text ("Tax is calculated per-line and summed") and within SC-003 tolerance.
- Phases 7 and 8 (interactive mode, polish) deferred to the next sprint. Tasks remain in tasks.md.

