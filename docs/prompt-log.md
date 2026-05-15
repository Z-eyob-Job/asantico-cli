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
