# Model Selection Rationale

Author: Eyob Worku
Course: AI410 Midterm Practical
Project: Asantico Agent (work order intake to estimate)

## 1. The decision

The triage layer does not pick one model. It routes by urgency: routine
requests go to Claude Haiku 4.5, and emergency or ambiguous requests escalate
to Claude Opus 4.7. The routing function is pure and lives in
infra/llm.py (route_model), so the decision is testable and visible:

    opus  if urgency == "emergency" or ambiguous
    haiku otherwise

The live path runs two passes. The first pass classifies on Haiku. If that
result is an emergency or comes back ambiguous, the request is re-run on Opus
for the harder judgment. Routine requests never touch the expensive model.

## 2. Why routing instead of one model

Maintenance requests are bimodal. Most are routine and high volume (a dryer
that will not heat, a slow drain). A few are rare and high stakes (a burst
pipe, an electrical smell). Paying for the strongest model on every routine
request wastes money; using a cheap model on a true emergency risks a missed
escalation. Routing matches model cost to the cost of being wrong.

## 3. Evidence: published benchmarks (from Sprint 2)

The Sprint 2 multi-model comparison established the cohort ordering on
published benchmarks (SWE-bench Verified, SWE-bench Pro, GPQA Diamond) and an
eight-prompt hands-on suite scored against a decision matrix with weights
declared before scoring. The relevant findings carried forward here:

- Opus 4.7 led the cohort on reasoning and on ambiguous, underspecified
  prompts. It was the only model that asked clarifying questions on the
  ambiguous P7 rate-limiter prompt rather than guessing.
- The cheaper, faster models traded judgment for latency and cost. One model
  silently modified files on P7 instead of surfacing the ambiguity.

The design lesson from P7 maps directly onto triage: on an ambiguous request,
the desired behavior is to surface uncertainty, not to act confidently. That
is exactly what the escalation rule does, and it is why ambiguous cases route
to the stronger model.

## 4. Evidence: hands-on triage eval (this build)

The offline eval harness (eval/triage_eval.py) runs all eleven labeled
fixtures through the triage path and reports:

- Urgency accuracy: 100 percent (11/11)
- Trade accuracy: 100 percent (11/11)
- Emergencies escalated: 2/2, zero missed (PASS, SPEC section 8)

Honest reading of these numbers: the 100 percent accuracy reflects the offline
recorded cache, which holds authored responses, not live model variance. It is
not a claim that any model classifies perfectly. On live runs, accuracy
depends on the model. What the eval proves is different and stronger: the
escalation safety property is enforced structurally by should_escalate, not by
model accuracy. Every gold emergency escalated, and the two ambiguous cases
(wo_07, wo_08) escalated on the low-confidence rule even though they are not
emergencies. wo_07 is the clearest case: the system agreed the request was
routine yet still flagged it for review because confidence was low. The system
is uncertain rather than confidently wrong.

## 5. Tradeoffs accepted

- Cheap-first risk: if Haiku misclassifies a true emergency as routine on the
  first pass, the live path does not escalate to Opus. This is the known
  weakness of cheap-first routing. It is accepted here because the human review
  gate downstream catches it, and because routine output is never auto-sent.
- Cost vs recall: routing optimizes cost on the common case at the price of a
  second model call on the rare case. For a property maintenance workload that
  is the correct trade.
- Offline reproducibility: grading runs against the recorded cache with no API
  key. This guarantees reproducibility at the cost of not exercising the live
  models during grading. The cache builder (scripts/build_triage_cache.py) uses
  the same canonical hashing as the runtime path, so the offline path is a
  faithful stand-in for the live path's parsing and routing logic.

## 6. Summary

Routing is the defensible choice because the decision is explicit and tested,
the cost model fits the workload, and the safety property does not depend on
the model being right. Sprint 2 established which model to trust for hard
judgment; this build uses that model only where judgment is needed.
