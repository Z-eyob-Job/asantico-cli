# Midterm Artifact Bundle: Submission Index

Author: Eyob Worku
Course: AI410 Midterm Practical
Project: Asantico Agent (work order intake to estimate)
Repo: github.com/Z-eyob-Job/asantico-cli (branch: 002-asantico-triage-agent)

## What this is

An agentic layer added to asantico-cli that takes a free-text maintenance
request and moves it through triage, escalation, a drafted tenant reply, and a
priced estimate, with a human approving anything client-facing. Built
spec-driven, phase by phase, on top of an untouched deterministic core.

## Required artifacts and where they are

| Required output | File |
|---|---|
| SPEC.md (requirements, constraints) | submission/SPEC_midterm.md |
| TASKS.md (executable plan) | submission/TASKS_midterm.md |
| Model selection rationale | submission/MODEL_SELECTION.md |
| Responsible AI risk and mitigation | submission/RESPONSIBLE_AI.md |
| Prompt log (key steps and decisions) | submission/PROMPT_LOG.md |
| Sprint 3 team formation notes | submission/SPRINT3_NOTES.md |
| Command documentation | docs/triage-agent.md |

## How the rubric maps to evidence

Completeness: all six required artifacts are present (table above).

Defensibility of technical decisions: MODEL_SELECTION.md (urgency-based
routing, Sprint 2 benchmark evidence, the two-pass escalation) and PROMPT_LOG.md
(nine decision checkpoints, including the cache-key bug and the noun-verb
restructure).

Spec-driven discipline: per-phase commit history on the branch, the
traceability map at the bottom of TASKS_midterm.md, and the deterministic core
(domain/tax.py, domain/models.py, infra/pdf.py) left unchanged. The original 92
core tests still pass inside the full suite.

Depth of responsible-AI reasoning: RESPONSIBLE_AI.md, five risks each with a
mitigation in code and a behavior verified by execution, plus named limitations
with the human-review gate as the backstop.

## Verify it yourself (offline, no API key)

    cd asantico-cli
    python -m venv .venv && source .venv/bin/activate
    pip install -e ".[dev]"
    python -m pytest -q                 # full suite, 168 passed

Run the three end-state invariants:

    # 1. Every emergency escalates to human review
    python eval/triage_eval.py          # PASS, 2/2 emergencies escalated

    # 2. Triage to drafted reply (offline fixture)
    asantico triage run tests/fixtures/workorders/wo_03_routine_appliance.json --json | asantico draft-reply new -

    # 3. Triage to priced estimate, totals match the engine to the cent
    asantico triage run tests/fixtures/workorders/wo_03_routine_appliance.json --json | asantico estimate new --from-triage -

Emergency gate (must flag HUMAN REVIEW and not progress):

    asantico triage run tests/fixtures/workorders/wo_01_emergency_plumbing.json

PII safety (the audit log must contain tokens only, never real PII):

    asantico triage run tests/fixtures/workorders/wo_09_heavy_pii_appliance.json
    tail -1 ~/.asantico/triage_audit.jsonl

## Live path (optional, needs an API key)

The live path classifies novel free-text input via the Anthropic API. It is not
required for grading; the offline path above is fully reproducible. To try it,
set ANTHROPIC_API_KEY in the environment and add --live to a triage run command.

## Test summary

168 tests pass: the 92 pre-existing deterministic-core tests plus 76 new tests
across the triage model, PII redaction, LLM routing and JSON handling, both CLI
commands, estimate-from-triage, and the eval harness. No regression at any
phase; the deterministic core was never modified.
