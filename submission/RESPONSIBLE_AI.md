# Responsible AI: Risks and Mitigations

Author: Eyob Worku
Course: AI410 Midterm Practical
Project: Asantico Agent (work order intake to estimate)

This section identifies the concrete risks in an agent that reads tenant
maintenance requests, classifies them, drafts replies, and prices work. Each
risk names a mitigation that exists in the code, and each mitigation is tied to
a behavior verified by running the system, not only by passing tests.

## Risk 1: Tenant PII exposure to the model and to logs

Maintenance requests contain names, phone numbers, emails, and unit numbers.
Sending that to a model, or writing it to a persistent log, is an exposure.

Mitigation. All text is redacted before any model call (domain/redaction.py).
Name, phone, email, and unit are replaced with stable tokens (NAME_1, PHONE_1,
EMAIL_1, UNIT_1). The model and the audit log see tokens only; PII is restored
locally for the operator's display.

Verified. Running triage on the heavy-PII fixture (wo_09), the operator's table
shows the restored values (James O'Brien, the phone, the email, unit 417),
while the audit line written to ~/.asantico/triage_audit.jsonl contains only
tokens, with the property name "Clark Roadhouse" left in the clear because a
property name is not personal PII. The restore map that holds the original
values is never serialized to the log.

Honest limitation. Redaction is cue-based regex (names after a cue like Tenant
or Mr, units after unit or apt). It will miss a bare name with no cue or an
oddly phrased request. This is defense in depth, not a guarantee. The audit
log storing tokens only, and the human review gate, are the backstops.

## Risk 2: Restored PII leaking through the command pipeline

The triage-to-draft and triage-to-estimate handoffs pass a JSON record between
commands. That record carries restored PII (the tenant's real name and contact)
because draft-reply needs the name to address the tenant.

Verified. Running triage run --json on wo_01 emits the tenant contact in
plaintext on stdout, by design, so the next command can use it.

Mitigation and limitation. The persistent audit log stays tokenized; only the
transient pipe carries restored PII. The operator must not redirect that stream
to a file or a log. This is a documented operational constraint, not an
enforced one, and it is named here so it is a considered tradeoff rather than
an oversight.

## Risk 3: A missed emergency

A burst pipe or an electrical smell misclassified as routine could be ignored.
This is the highest-stakes failure in the domain.

Mitigation. Escalation is a structural rule, not a model judgment. should_
escalate returns true on any emergency or any field below the confidence
threshold, independent of how the rest of the pipeline behaves. Emergencies and
low-confidence cases are flagged HUMAN_REVIEW and do not auto-progress.

Verified. The eval harness reports 2/2 gold emergencies escalated, zero missed
(PASS, SPEC section 8). The invariant is checked by execution, not assumed. The
two ambiguous fixtures escalate on the low-confidence rule even though they are
not emergencies, so the system escalates on uncertainty as well as on severity.

Honest limitation. On the live path, cheap-first routing means Haiku classifies
first; if it labels a true emergency as routine, escalation to Opus does not
fire. The human review gate is the backstop. The structural invariant protects
against a model that is unsure (low confidence escalates) but not against a
model that is confidently wrong on the first pass.

## Risk 4: An unapproved message sent to a tenant

An agent that drafts tenant communications could send something wrong,
premature, or in the wrong voice.

Mitigation. draft-reply never sends. Output is a DRAFT until the operator
passes --approve, and even then no real message goes out; an approved draft is
only recorded locally in sent_log.jsonl. This is the Sprint 2 P7 lesson (never
take an unprompted action) built into the gate.

Verified. Without --approve, sent_log.jsonl does not exist after a draft (the
negative proven by absence). With --approve, it gains exactly one line. The
sent log records property, unit, issue, and a character count, but never the
tenant contact, applying data minimization to the record itself.

## Risk 5: A wrong price sent to a client

An auto-generated estimate with bad math or invented line items could be sent
to Avenue One as a real quote.

Mitigation. The triage-to-estimate path does not compute its own totals. It
maps the triaged work order into a line item and calls the existing, tested tax
engine unchanged, so the 10.55 percent Seattle rule (including labor-only
lines) is applied by proven code. The agent drafts a single labor line at the
configured rate; it does not invent materials costs. Final pricing is the
operator's job.

Verified. Estimate totals from the triage path match a direct call to the
deterministic engine to the cent (subtotal 65.00, tax 6.86, total 71.86). The
estimate is a starting draft priced at labor rate, not a final quote; the
operator refines it. This is an explicit human-in-the-loop choice.

## Cross-cutting: auditability

Every model call and classification appends one tokenized line to the audit
log (timestamp, model, prompt hash, urgency, trade, needs_review, redacted
text). This makes the agent's decisions reviewable after the fact without
storing PII. Note: the audit log writes to ~/.asantico/; in a restricted
environment where the home directory is not writable, that write can fail. A
production version would make the path configurable with a workspace-local
fallback.

## Summary

The responsible-AI posture rests on three guarantees that hold regardless of
model behavior: PII is tokenized before it reaches the model or any persistent
log, emergencies and uncertain cases escalate by a structural rule, and nothing
client-facing leaves the tool without explicit human approval. The limitations
(cue-based redaction recall, transient-pipe PII, cheap-first misclassification)
are named rather than hidden, with the human review gate as the consistent
backstop behind each.
