# Asantico CLI

A spec-driven command-line tool that generates professional PDF invoices and estimates for Asantico, a Seattle property maintenance business. Built for Sprint 1 of AI410 using the GitHub Spec Kit workflow (/speckit-specify, /speckit-plan, /speckit-tasks, /speckit-implement) with a custom Claude skill and a pre-tool-use validation hook.
## Quick start

Prerequisites: Python 3.13 and pip. (uv is used for Spec Kit but is not required to run the CLI.)
From the repo root:
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
Verify the install:
asantico --version
asantico --help
## Generate a sample invoice

asantico invoice new --from-file examples/sample_items.json --property "The Meridian"
The PDF lands in ./output/ with the pattern invoice_<property-slug>_YYYY-MM-DD.pdf. Two reference PDFs are checked in at examples/ so you can see expected output without running the CLI.
## Generate a sample estimate

asantico estimate new --from-file examples/sample_items.json --property "Garden"
Same workflow, different document type. Estimates carry an EST-#### document number and a validity-period footer instead of payment terms.
## What the CLI does

Reads a JSON file of line items, applies Seattle sales tax at 10.55% per line (labor included), assembles a styled PDF with header, recipient block (Avenue One Residential), line-item table, subtotal, tax row, total, and a footer appropriate to invoice vs estimate, then writes it to ./output/. Config (properties, rates, counters) lives under ~/.asantico/ and is created on first run.
Commands
CommandDescriptionasantico --versionPrint versionasantico --helpShow all commandsasantico invoice new --from-file FILE --property NAMEGenerate an invoice PDFasantico estimate new --from-file FILE --property NAMEGenerate an estimate PDFasantico properties listList configured propertiesasantico properties add NAMEAdd a property to the registryasantico properties remove NAMERemove a propertyasantico rates listShow default labor and material ratesasantico rates set TYPE VALUEUpdate a default rate
## Project layout

asantico-cli/
├── SPEC.md                            # Authoritative spec for Sprint 1
├── CLAUDE.md                          # Project context for Claude Code
├── pyproject.toml                     # Packaging and dependencies
├── README.md                          # This file
├── src/asantico_cli/
│   ├── domain/                        # Pure logic: models, tax, slug, validation
│   ├── infra/                         # I/O: config, PDF rendering, JSON loader
│   └── cli/                           # Typer entrypoint and subcommands
├── tests/                             # 92 pytest tests
├── examples/                          # Sample JSON, sample invoice PDF, sample estimate PDF
├── output/                            # Generated PDFs (gitignored)
├── docs/
│   ├── prompt-log.md                  # /speckit workflow transcript
│   └── hook-execution-transcript.md   # Hook validation tests
├── specs/001-asantico-invoice-cli/    # Spec Kit artifacts
│   ├── spec.md                        # Feature spec (mirror of SPEC.md)
│   ├── plan.md                        # 8-phase implementation plan
│   ├── tasks.md                       # 96 actionable tasks
│   ├── research.md                    # Tech decisions
│   ├── data-model.md                  # Entity schemas
│   ├── contracts/cli.md               # Command input/output contract
│   └── quickstart.md                  # Spec Kit quickstart
└── .claude/
    ├── settings.json                  # Hook config (PreToolUse on Bash)
    ├── hooks/validate-before-destructive.sh
    └── skills/asantico-invoice-formatter/SKILL.md   # Custom skill
## Testing

.venv/bin/pytest -v
92 tests covering domain math, slug generation, filename construction, validation, config persistence, PDF rendering, JSON loading, and CLI command dispatch. Target was 15 per NFR-003.
Sprint 1 deliverables
Required artifactLocationSPEC.mdRepo root, mirrored from specs/001-asantico-invoice-cli/spec.mdCLAUDE.mdRepo rootCustom skill.claude/skills/asantico-invoice-formatter/SKILL.mdPre-tool-use hook.claude/settings.json plus .claude/hooks/validate-before-destructive.shPrompt log (/spec, /plan, /tasks)docs/prompt-log.mdRunnable CLIsrc/asantico_cli/, installable via pip install -e .Sample outputsexamples/invoice_the-meridian_2026-05-15.pdf, examples/estimate_garden_2026-05-15.pdf
## How this was built

Every artifact was produced by an explicit spec-driven step rather than ad-hoc prompting:

/speckit-specify generated SPEC.md with 17 FRs, 6 NFRs, 6 user stories, and a full requirement traceability matrix.
/speckit-plan generated an 8-phase implementation plan with research, data model, and a formal CLI contract.
/speckit-tasks broke the plan into 96 ordered, dependency-aware tasks with parallel markers.
/speckit-implement executed Phases 1 through 6 (MVP scope) one phase at a time, committing after each.
A pre-tool-use hook ran pytest and scanned for em dashes before every commit; a custom skill enforced Asantico formatting rules throughout. Both are checked in and active.

The full prompt history is in docs/prompt-log.md. The Git history (git log --oneline) shows the spec, plan, tasks, skill, hook, and each implementation phase as separate commits, in order.
## Known limitations and future work


Interactive mode (asantico invoice new with no flags) is Phase 7 and was not built in this sprint. The interactive prompts are specified in tasks.md for the next iteration.
The PDF currently has no top-of-page Asantico, Seattle WA business header above the document title. The bill-to and footer references are present; the masthead is the cleanest single tweak for visual polish.
Per-line tax is computed and displayed correctly but the totals row may differ from a hand-summed pen-and-paper number by one cent on some line counts, due to ROUND_HALF_UP per-line vs sum-then-round. This is consistent with the spec ("Tax is calculated per-line and summed") and within SC-003 tolerance.
No email integration (explicitly out of scope per spec).
