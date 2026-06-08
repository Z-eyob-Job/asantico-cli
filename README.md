# Asantico CLI and Triage Agent

A spec-driven command-line tool for Asantico, a Seattle property maintenance
business. It started as a PDF invoice and estimate generator (Sprint 1) and was
extended with an agentic triage layer (AI410 midterm) that takes a free-text
maintenance request and moves it through classification, escalation, a drafted
tenant reply, and a priced estimate, with a human approving anything
client-facing.

Built with Python 3.13, Typer, ReportLab, and Rich, on a layered architecture
(pure domain logic, infra for I/O, Typer CLI). The deterministic invoice and
estimate engine is unchanged by the agent; the agent feeds it.

## Midterm submission

All midterm artifacts live in the `submission/` folder. Start with
`submission/SUBMISSION_INDEX.md`, which maps each rubric item to its file and
lists the exact commands to verify every behavior.

| Required output | File |
|---|---|
| SPEC.md (requirements, constraints) | submission/SPEC_midterm.md |
| TASKS.md (executable plan) | submission/TASKS_midterm.md |
| Model selection rationale | submission/MODEL_SELECTION.md |
| Responsible AI risk and mitigation | submission/RESPONSIBLE_AI.md |
| Prompt log (key steps and decisions) | submission/PROMPT_LOG.md |
| Sprint 3 team formation notes | submission/SPRINT3_NOTES.md |
| Command documentation | docs/triage-agent.md |

## Setup

Prerequisites: Python 3.13 and pip. From the repo root:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"

Verify the install:

    asantico --version
    asantico --help

Note: every new terminal session needs `source .venv/bin/activate` first, or
the `asantico` command will not be found.

## How to test it

The full suite runs offline with no API key:

    source .venv/bin/activate
    python -m pytest -q

Expected: 168 passed. This includes the 92 original deterministic-core tests
plus 76 new tests for the triage agent, with no regression in the core.

### Verify the three safety invariants (offline, no key)

Every emergency escalates to human review:

    python eval/triage_eval.py
    # Expected: PASS, 2/2 emergencies escalated

Triage to a drafted reply (the full agent pipeline):

    asantico triage run tests/fixtures/workorders/wo_03_routine_appliance.json --json | asantico draft-reply new -

Triage to a priced estimate, totals match the engine to the cent:

    asantico triage run tests/fixtures/workorders/wo_03_routine_appliance.json --json | asantico estimate new --from-triage -

The emergency gate fires and refuses to auto-progress:

    asantico triage run tests/fixtures/workorders/wo_01_emergency_plumbing.json
    # Expected: HUMAN REVIEW REQUIRED panel

PII safety: the audit log stores tokens only, never real data:

    asantico triage run tests/fixtures/workorders/wo_09_heavy_pii_appliance.json
    tail -1 ~/.asantico/triage_audit.jsonl
    # The logged line shows NAME_1, PHONE_1, UNIT_1, never the real values

The eleven labeled fixtures in `tests/fixtures/workorders/` cover routine,
urgent, emergency, ambiguous, and heavy-PII cases, all runnable offline.

## What the triage agent does

Given a free-text maintenance request it:

- Classifies urgency (emergency, urgent, routine) and trade (plumbing,
  electrical, hvac, appliance, general), and extracts the property, unit,
  tenant contact, and a summary, each with a confidence score.
- Escalates to human review on any emergency or any low-confidence field, and
  does not auto-progress flagged cases.
- Redacts tenant PII (name, phone, email, unit) before any model call or log
  write, restoring it only for the operator's local display.
- Routes by cost: routine requests use Claude Haiku 4.5; emergency or ambiguous
  requests escalate to Claude Opus 4.7.
- Drafts a tenant reply that stays a DRAFT until explicitly approved (never
  auto-sends), and produces an estimate using the existing 10.55 percent tax
  engine.

### Triage agent commands

    asantico triage run FILE|-              Classify a request (offline by default)
    asantico triage run FILE|- --json       Emit the result as JSON for piping
    asantico triage run FILE|- --live       Use the live model instead of the cache
    asantico draft-reply new FILE|-         Draft a tenant reply (DRAFT until --approve)
    asantico draft-reply new FILE|- --approve   Approve and record locally (no real send)
    asantico estimate new --from-triage FILE|-  Build an estimate from a triaged request

### Live mode (optional, needs an API key)

The offline path above is fully reproducible and is what grading uses. To run
the agent on novel free-text input, set an Anthropic API key in the environment
and add `--live`:

    export ANTHROPIC_API_KEY=sk-ant-...        # never commit this; .env is gitignored
    echo "Refrigerator stopped cooling in unit 22, food spoiling." | asantico triage run - --live

## Original invoice and estimate CLI (Sprint 1)

    asantico invoice new --from-file examples/sample_items.json --property "The Meridian"
    asantico estimate new --from-file examples/sample_items.json --property "Garden"

These read a JSON file of line items, apply Seattle sales tax at 10.55 percent
per line (labor included), and write a styled PDF to `./output/`. Reference
PDFs are checked in under `examples/`.

    asantico properties list | add NAME | remove NAME
    asantico rates list | set TYPE VALUE

## Project layout

    asantico-cli/
    ├── submission/                 # Midterm artifact bundle (start at SUBMISSIOX.md)
    ├── src/asantico_cli/
    │   ├── domain/                 # Pure logic: models, tax, slug, validation, triage, redaction
    │   ├── infra/                  # I/O: config, PDF rendering, JSON loader, llm (routing, audit)
    │   └── cli/                    # Typer entrypoint: invoice, estimate, properties, rates, triage, draft_reply
    ├── tests/                      # 168 pytest tests, plus fixtures/ (work orders and offline triage cache)
    ├── eval/                       # Offline triage eval harness
    ├── scripts/                    # Offline cache builder
    ├── docs/                       # triage-agent.md and Sprint 1 transcripts
    ├── examples/                   # Sample JSON and reference PDFs
    └── specs/001-asantico-invoice-cli/   # Sprint 1 Spec Kit artifacts

## Responsible AI summary

Three guarantees hold regardless of model behavior: PII is tokenized before it
reaches the model or any persistent log, emergeng client-facing leaves the tool
without explicit human approval. Full analysis with named limitations is in
`submission/RESPONSIBLE_AI.md`.
