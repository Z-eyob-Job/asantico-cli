# SPEC.md: Asantico Agent (Work Order Intake to Estimate)

Author: Eyob Worku
Course: AI410 Midterm Practical

## 1. Problem framing and context

Asantico handles maintenance across 50-plus Avenue One rental properties. Requests arrive as free text from tenants and property contacts. Triage, routing, and estimate prep are currently manual. The deterministic core already exists in asantico-cli: invoice and estimate generation, the 10.55 percent Seattle tax engine, navy and gold branding, INV/EST numbering, slug-based filenames, and workorder CSV normalization.

The gap is the judgment layer between a raw request and a structured, priced, routed work order. This build adds an agentic layer on top of the existing deterministic core without replacing it.

## 2. Goals

- Classify an incoming request by urgency and trade using an LLM.
- Extract structured fields (property, unit, tenant contact, issue summary) with per-field confidence.
- Route emergencies and ambiguous cases to human review automatically.
- Draft a tenant acknowledgment for human approval, never auto-sent.
- Convert an approved work order into a line-item estimate using the existing tax engine.
- Control cost through urgency-based model routing.

## 3. Non-goals (out of scope for the timed build)

- No real outbound email or SMS. Drafts only; sending is logged locally as a stub.
- No live calendar or scheduling writes.
- No web UI, no multi-tenant auth.
- No redesign of the existing invoice PDF layout beyond what estimate reuse needs.
- Photo-attach with EXIF/GPS stripping is net-new (not in repo) and deferred to stretch.

## 4. Users

- Operator (Stark): runs the CLI, approves drafts, owns final pricing.
- Indirect: tenants receive drafted communications; Avenue One contacts are escalation targets. Neither is a direct CLI user.

## 5. Functional requirements

- FR1 Triage: triage <file|-> reads a raw request and returns urgency {emergency, urgent, routine}, trade {plumbing, electrical, hvac, appliance, general}, and extracted fields as JSON, with a confidence score per field.
- FR2 Escalation: any emergency, or any field below the confidence threshold, is flagged HUMAN_REVIEW and does not auto-progress.
- FR3 PII handling: tenant PII (name, phone, email, unit) is detected and redacted before any LLM call, then restored locally for display only.
- FR4 Reply draft: draft-reply produces a tenant acknowledgment from a triaged record, marked DRAFT. Marking it sent requires an explicit --approve flag and writes only to a local log in this build.
- FR5 Estimate: estimate --from-triage builds a line-item estimate, applies 10.55 percent Seattle tax to all lines including labor-only, uses navy and gold branding, and names the company "Asantico".
- FR6 Model routing: routine cases route to Haiku 4.5; emergency or ambiguous cases escalate to Opus 4.7. Routing is configurable.
- FR7 Audit log: every LLM call, classification, and state transition is logged with timestamp, model, prompt hash, and the decision made. Redacted text only, never raw PII.

## 6. Non-functional requirements

- Reproducible for grading from recorded fixtures with no live API keys required, mirroring the Sprint 2 approach.
- Python 3.13, Typer CLI, plus existing dependencies (ReportLab, Rich).
- The deterministic core stays deterministic. Only triage and draft-reply call the LLM.
- The pre-existing 92 tests must still pass (no regression).

## 7. Constraints

- Asantico conventions are non-negotiable: 10.55 percent tax always (including labor-only), navy and gold branding, no em dashes anywhere, company name "Asantico" and never "Asantico LLC".
- No unprompted file writes outside the repo workspace.
- No client-facing artifact leaves the tool without explicit human approval.

## 8. Success criteria

- Triage agreement at or above target on a labeled fixture set.
- 100 percent of emergencies and below-threshold cases routed to human review, zero silent auto-progression.
- 100 percent of outbound drafts require explicit approval before being marked sent.
- Estimate totals match the existing deterministic engine to the cent.
- Full traceability: SPEC to TASKS to commits to prompt log to RAI.

## 9. Confirmed current state (from read-only inventory)

- Three layers intact: domain/ (models, tax, slug, validation), infra/ (config, loader, pdf), cli/ (app, invoice, estimate, properties, rates).
- tax.compute_line_tax and compute_totals apply 10.55 percent uniformly to all units including labor.
- infra/pdf.render_pdf(document, output_dir) renders a Document.
- Subcommands registered via add_typer on a root Typer app.
- No photo/EXIF/GPS handling exists. Confirmed net-new.
