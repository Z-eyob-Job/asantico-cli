# Prompt Log: Key Steps and Decisions

Author: Eyob Worku
Course: AI410 Midterm Practical
Project: Asantico Agent (work order intake to estimate)

This log records the decision checkpoints during the build. The workflow used
three tools in defined lanes: Claude Code read the existing codebase, Cursor
implemented phase by phase from TASKS_midterm.md, and a review pass verified
each phase against the spec. Each phase ended with its own tests; the
deterministic core was never modified.

## 1. Read before writing
A read-only inventory confirmed the three-layer structure and real signatures,
and surfaced that photo-attach GPS stripping was not in the repo. Decision: cut
photo handling to stretch, keep text PII redaction as the responsible-AI
surface. Spec and tasks updated to match reality.

## 2. Keep the domain layer pure
All LLM work confined to infra/llm.py; triage model and redaction stay pure in
domain/. Kept routing, escalation, and redaction unit-testable without mocking
a network.

## 3. Offline cache for no-key grading
triage_request reads recorded responses from a fixture cache keyed by a hash of
the redacted text when offline, so the system runs and grades with no API key.

## 4. The cache-key drift bug
Triage on a real fixture missed the cache even though tests passed. Cause: tests
built the key from the same in-memory string they stored, agreeing with each
other but not the real CLI path; stdin keeps a trailing newline, so the hash
diverged. Decision: one canonical hash function shared by builder and runtime,
plus a regression test on the real CLI path. Lesson: green tests can hide a bug
when both sides share the same shortcut.

## 5. Inspect existing commands before restructuring
A flag-parsing bug tempted a patch (allow_interspersed_args). Inspecting the
original four commands showed a noun-verb pattern (invoice new, rates set). The
new commands had faked a direct command with a callback. Restructuring to
triage run and draft-reply new removed the hack at the root and matched the
convention. Looking at the real code changed the decision from patch to align.

## 6. stdout and stderr discipline
triage run --json prints pure JSON to stdout, human messages to stderr, so the
pipe stays clean and triage run --json | draft-reply new - works.

## 7. The agent drafts, the human decides
estimate --from-triage produces one labor line at the configured rate, not a
finished quote. draft-reply drafts for review cases rather than refusing; the
approval gate is the checkpoint.

## 8. Live output is messier than the offline cache
A real API key surfaced three bugs, same lesson: authored cache is cleaner than
real model output, and the live call is not exercised offline. Fixes: a pure
extract_json_object helper for fenced/prose-wrapped JSON; coercion of string
fields at the model boundary with a defensive restore; offline tests for each.

## 9. Connecting the API key safely
Added .env to .gitignore, verified with git check-ignore, stored the key only in
the local .env, loaded at runtime. No secret enters the repo. Verified the live
path works and the audit log stayed tokenized on a real call (NAME_1, PHONE_1).

## Outcome
Nine phases, 165 passing tests (92 pre-existing core plus 73 new), the
deterministic core untouched, and three invariants proven by execution: every
emergency escalates, no draft is recorded without approval, and triage-fed
estimate totals match the engine to the cent.
