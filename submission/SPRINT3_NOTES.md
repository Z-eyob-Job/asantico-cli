# Sprint 3 Team Formation and Kickoff Notes

Author: Eyob Worku
Course: AI410 Midterm
Status: solo project (instructor approved)

## Roster and role mapping

This is a solo Sprint 3, approved by the instructor. The four roles from the
Sprint 3 brief are carried by one person, treated as distinct responsibilities
rather than separate people, so each concern still gets explicit attention.

| Role | Owner | Responsibility |
|---|---|---|
| Engineering lead | Eyob Worku | Architecture, core agent loop, code review |
| Data/retrieval lead | Eyob Worku | Source inventory, retrieval, document handling |
| Evaluation/safety lead | Eyob Worku | Eval harness, responsible-AI gates, red-teaming |
| Integration lead | Eyob Worku | MCP and external tool wiring, end-to-end pipeline |

Working solo, the practical effect is sequencing rather than parallel work: each
role's tasks are scheduled in phases (the same phase-by-phase discipline used in
the midterm build) so safety and evaluation are not deferred to the end.

## Draft project concept statement

Property maintenance operators handle a stream of unstructured requests across
many units and must triage, route, schedule, and price work while keeping
tenant data safe. Sprint 3 extends the midterm triage agent into a fuller
property-operations assistant: it ingests requests from real channels,
retrieves the relevant property and vendor context, drafts tenant and vendor
communications behind human approval, and schedules visits, with every
external-facing action gated by a human checkpoint and every record stripped of
tenant PII. The midterm build proves the core triage-to-estimate spine; Sprint
3 adds retrieval, real intake, scheduling, and a richer evaluation suite.

## Initial data and source inventory

- Work order requests: free-text intake. Midterm used 11 labeled fixtures;
  Sprint 3 adds a larger labeled set and, optionally, a live read channel.
- Property and unit records: address, unit, access notes (drives routing and
  the property field in estimates).
- Vendor and trade directory: which contractor handles which trade and area,
  for routing beyond classification.
- Rate card: labor and materials rates feeding the existing estimate engine.
- Historical estimates and invoices: prior pricing as retrieval context for
  more realistic draft estimates.
- Candidate external sources via MCP: a calendar (scheduling), email (intake
  and drafted replies, approval-gated), and a document store (property files).
  Used read-first, with writes behind approval.

## Early SPEC.md skeleton for the final project

1. Problem framing and context
2. Goals and non-goals
3. Users and stakeholders (operator, tenants, vendors, property owner)
4. Functional requirements
   - Intake from a real channel
   - Retrieval of property, vendor, and pricing context
   - Triage and routing (extends the midterm classifier)
   - Scheduling with a human-approved calendar write
   - Draft tenant and vendor communications, approval-gated
   - Estimate generation from retrieved pricing context
5. Non-functional requirements (reproducible eval, offline path, latency)
6. Constraints (Asantico conventions, PII handling, no unprompted actions)
7. Responsible-AI requirements (redaction, escalation invariant, approval
   gates, auditability)
8. Success criteria and evaluation plan
9. Assumptions

## Planning questions

- What real user problem are you solving? Operators lose time on manual triage,
  routing, and pricing, and risk mishandling tenant data. The agent compresses
  intake-to-action while keeping a human in control.
- What external tools or MCP integrations will likely be required? Calendar for
  scheduling, email for intake and approval-gated replies, a document or drive
  store for property files. All read-first, writes behind approval.
- Where will the human-in-the-loop checkpoints be? Emergency and low-confidence
  escalation (already built), draft approval before any send, calendar write
  approval, and estimate approval before it reaches a client.
- How will retrieval and reasoning quality be evaluated? Extend the offline
  eval harness: triage accuracy and the escalation invariant (already in
  place), plus retrieval precision on property/vendor lookup and a check that
  drafted estimates use retrieved rates rather than invented numbers.

## Scope note for solo work

Because this is solo, Sprint 3 scope is deliberately bounded: one real intake
channel, one retrieval source, and one approval-gated write (calendar), rather
than all integrations at once. Depth on the safety and evaluation story is
prioritized over breadth of integrations.
