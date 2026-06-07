# Triage Agent (Work Order Intake to Estimate)

This is the agentic layer that sits on top of the deterministic Asantico core.
It classifies a raw maintenance request, redacts tenant PII before any model
call, routes emergencies and ambiguous cases to human review, drafts a tenant
acknowledgment behind an approval gate, and can hand a triaged work order
straight into the existing estimate engine. The 10.55 percent Seattle tax,
navy and gold branding, and the company name "Asantico" are unchanged.

Everything runs offline by default against a recorded fixtures cache, so no API
key is required. The live model path is gated behind a flag.

## Commands

### triage run

Classify a request and print a result table. Input is a file path or `-` for
stdin. A work order JSON file with a `raw_text` field is detected and its
`raw_text` is used automatically; plain text files and stdin are used as is.

```bash
# From a work order JSON fixture
asantico triage run tests/fixtures/workorders/wo_03_routine_appliance.json

# From stdin
echo "The dishwasher in unit 204 at Garden is not draining." | asantico triage run -

# Tune the confidence threshold for human review (default 0.7)
asantico triage run request.txt --threshold 0.8

# Use the live model instead of the offline recorded cache
asantico triage run request.txt --live

# Emit JSON to stdout for command handoff (human messaging goes to stderr)
asantico triage run request.txt --json
```

If the case is an emergency or any field confidence is below the threshold, the
result is flagged for human review and the command does not progress.

### draft-reply new

Produce a tenant acknowledgment from a triage record (the shape emitted by
`triage run --json`). Input is a file path or `-` for stdin. The output is a
DRAFT by default and nothing is sent.

```bash
# Draft only, nothing is recorded
asantico draft-reply new triage.json

# Read the triage JSON from stdin
asantico draft-reply new -

# Mark the draft sent. This appends one line to a local sent_log.jsonl only.
# No real email or SMS is sent in this build.
asantico draft-reply new triage.json --approve
```

Without `--approve`, no entry is written to `sent_log.jsonl`. The local sent
log records location and issue only, never tenant contact details.

### estimate new --from-triage

Build an estimate PDF directly from a triaged work order, reusing the existing
tax engine and PDF renderer. Input is a file path or `-` for stdin.

```bash
# From a saved triage record
asantico estimate new --from-triage triage.json

# From stdin
asantico estimate new --from-triage -

# Override the property if the record has none
asantico estimate new --from-triage triage.json --property "The Meridian"
```

The triaged work order maps to a labor line priced at the configured labor
rate. The 10.55 percent Seattle tax is applied by the existing engine,
including this labor-only line, and the totals are printed after the PDF path.

## Pipelines

Triage and draft a reply in one line:

```bash
asantico triage run request.txt --json | asantico draft-reply new -
```

Triage and build an estimate in one line:

```bash
asantico triage run request.txt --json | asantico estimate new --from-triage -
```

## Responsible AI notes

- PII (tenant name, phone, email, unit number) is redacted to stable tokens
  before any model call or cache lookup, then restored locally for display.
- Every triage call appends one audit line to `~/.asantico/triage_audit.jsonl`
  with timestamp, model, prompt hash, urgency, trade, and the review flag. The
  audit log stores redacted text only; the PII restore map is never written.
- Model routing controls cost: routine confident cases use the cheaper model,
  emergencies and ambiguous cases escalate to the stronger model.
- No client facing artifact leaves the tool without explicit human approval.

## Evaluation

Score offline triage against the labeled fixtures and check that every
emergency escalates:

```bash
python eval/triage_eval.py
```
