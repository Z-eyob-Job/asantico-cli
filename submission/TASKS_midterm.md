# TASKS.md: Asantico Agent (Work Order Intake to Estimate)

Author: Eyob Worku
Course: AI410 Midterm Practical
Builds from: SPEC_midterm.md
Repo: asantico-cli (Python 3.13, Typer, ReportLab, Rich)

## Ground rules for every task

- Touch only the files named in each task. Do not modify the deterministic core (domain/tax.py, domain/models.py, infra/pdf.py) except where a task says so.
- Domain layer stays pure: no I/O, no network, no LLM calls. All LLM work lives in infra/llm.py.
- No em dashes in any output or generated text. Company name is "Asantico", never "Asantico LLC". Tax stays 10.55 percent on all lines including labor.
- Every task ends with its own test. Do not move to the next task until the current one passes.
- No unprompted writes outside the repo workspace. No client-facing artifact leaves the tool without explicit approval.

## Phase 0: Setup (10 min)

- T0.1 Create a feature branch: 002-asantico-triage-agent.
- T0.2 Add fixtures dir tests/fixtures/workorders/ with 8 to 12 labeled raw requests as JSON: each has raw_text and a gold block (urgency, trade). Include at least 2 emergencies, 2 ambiguous, and 1 with heavy PII.
- T0.3 No new runtime deps required for the offline path. Live LLM path uses the existing environment, gated behind a flag.

## Phase 1: Domain, triage model (pure) (30 min)

- T1.1 Create domain/triage.py. Define Urgency = Literal["emergency","urgent","routine"] and Trade = Literal["plumbing","electrical","hvac","appliance","general"].
- T1.2 Add dataclass TriageResult: urgency, trade, property_name, unit, tenant_contact, issue_summary, and confidence: dict[str, float] per field. Add needs_review: bool.
- T1.3 Add pure function should_escalate(result, threshold) -> bool: True if urgency == "emergency" or any confidence value < threshold.
- T1.4 Tests in tests/test_triage_model.py: escalation fires on emergency, fires on low confidence, stays False on a clean routine case.

## Phase 2: Domain, PII redaction (pure) (30 min)

- T2.1 Create domain/redaction.py. redact(text) -> tuple[str, dict]: replaces tenant name, phone, email, unit number with stable tokens (NAME_1, PHONE_1), returns redacted text plus restore map.
- T2.2 restore(text, mapping) -> str: reverses the tokens for local display only.
- T2.3 Tests in tests/test_redaction.py: phone and email patterns caught, restore is exact round-trip, redacted text contains no original PII.

## Phase 3: Infra, LLM client and routing (40 min)

- T3.1 Create infra/llm.py. route_model(urgency, ambiguous) -> str: "haiku" for routine, "opus" for emergency or ambiguous. Pure and unit-testable.
- T3.2 triage_request(raw_text, *, live, threshold) -> TriageResult. When live is False, read a recorded response from a fixtures cache keyed by a hash of the redacted text (grade with no API key, like Sprint 2). When live is True, redact first, call the routed model, parse JSON into TriageResult.
- T3.3 Audit log: append one JSON line per call to ~/.asantico/triage_audit.jsonl with timestamp, model, prompt hash, urgency, trade, needs_review. Log redacted text only.
- T3.4 Tests in tests/test_llm_routing.py: routing table correct for all three urgencies; offline triage returns a valid TriageResult from a fixture; audit line written and contains no PII.

## Phase 4: CLI, triage command (25 min)

- T4.1 Create cli/triage.py exposing app = typer.Typer(). Command triage <file|-> reads raw text, runs triage_request offline by default, --live to call the model, --threshold default 0.7.
- T4.2 Print a Rich table of the result. If needs_review, print a clear HUMAN REVIEW banner and exit without progressing.
- T4.3 Register in cli/app.py via add_typer(triage.app, name="triage"), matching the existing pattern.
- T4.4 Test in tests/test_cli_triage.py with CliRunner: routine case prints result and exits 0; emergency case prints the review banner.

## Phase 5: CLI, draft-reply with approval gate (25 min)

- T5.1 Create cli/draft_reply.py. Command draft-reply <triage-json> produces a tenant acknowledgment as DRAFT. No em dashes, brief, professional, first person.
- T5.2 Require --approve to mark the draft sent. Without it, output is labeled DRAFT and nothing recorded as sent. With it, append to a local sent_log.jsonl only (no real send).
- T5.3 Register via add_typer(draft_reply.app, name="draft-reply").
- T5.4 Test in tests/test_cli_draft.py: without --approve output is marked DRAFT and sent_log untouched; with --approve a sent entry is written.

## Phase 6: Estimate from work order (20 min)

- T6.1 In cli/estimate.py, add option --from-triage <triage-json> that maps a triaged work order into LineItem objects and calls the existing estimate path. Reuse compute_totals and render_pdf unchanged.
- T6.2 Test in tests/test_estimate_from_triage.py: totals match a direct call to the existing engine to the cent; tax present on a labor-only line.

## Phase 7: Eval harness (20 min)

- T7.1 Create eval/triage_eval.py: runs all fixtures through offline triage, compares to gold, prints urgency accuracy, trade accuracy, and whether every emergency escalated.
- T7.2 Record the numbers. These feed the model selection rationale (hands-on layer) and SPEC section 8 success criteria.

## Phase 8: Verify and package (15 min)

- T8.1 Full pytest run, all green. Confirm the pre-existing 92 tests still pass (no regression in the deterministic core).
- T8.2 Grep the repo for em dashes in any generated output path. Confirm none.
- T8.3 Confirm: every emergency escalated, no draft sent without --approve, estimate totals match to the cent.
- T8.4 Commit per phase with clear messages (the commit history doubles as part of the prompt log trail).

## What stays out (deferred, not in the timed build)

- Photo-attach with EXIF/GPS stripping. Confirmed not present in the repo, so net-new. Moved to stretch. Text PII redaction (Phase 2) covers the responsible AI surface.
- Real outbound email or SMS. Drafts only.
- Live Gmail or Calendar MCP integration.

## Traceability map (for the grader)

- SPEC FR1, FR2 to Phases 1 and 4.
- SPEC FR3 (PII) to Phase 2.
- SPEC FR4 (draft, approval) to Phase 5.
- SPEC FR5 (estimate, tax) to Phase 6.
- SPEC FR6 (routing) to Phase 3 (T3.1).
- SPEC FR7 (audit log) to Phase 3 (T3.3).
- SPEC section 8 success criteria to Phases 7 and 8.
