# Hook Execution Transcript (Lab 2.3 evidence)

The pre-commit hook at `.claude/hooks/validate-before-destructive.sh` is registered in `.claude/settings.json` as a `PreToolUse` hook for any `Bash` tool call. It blocks `git commit`, `git push`, `rm -rf`, `git reset --hard`, and `find ... -delete` if the project state is invalid.

Validation checks:
1. `pytest` must pass (skipped while there are no test files).
2. No em dashes (U+2014) in staged content.

The hook reads the Claude Code event JSON from stdin and inspects `tool_input.command`. It exits 0 to allow, exits 2 to block.

---

## Test 1: benign command, no validation needed

Command sent to hook:

    {"tool_input":{"command":"ls -la"}}

Output: (none)

Exit code: 0

Interpretation: the hook did not match the high-impact pattern, exited silently, allowed the command.

---

## Test 2: high-impact command, no em dashes staged

Command sent to hook:

    {"tool_input":{"command":"git commit -m test"}}

Output (stderr):

    [asantico-hook] High-impact command detected: validating project state...
    [asantico-hook] Command: git commit -m test
    [asantico-hook] No test files yet, skipping pytest check.
    [asantico-hook] Validation passed. Allowing command.

Exit code: 0

Interpretation: hook matched `git commit`, ran the validation pipeline, found no problems, allowed the commit to proceed.

---

## Test 3: high-impact command, em dash present in staged content

Setup: appended `Test em dash , here` (literal em dash) to `README.md`, then `git add README.md` before invoking the hook.

Command sent to hook:

    {"tool_input":{"command":"git commit -m test"}}

Output (stderr):

    [asantico-hook] High-impact command detected: validating project state...
    [asantico-hook] Command: git commit -m test
    [asantico-hook] No test files yet, skipping pytest check.
    [asantico-hook] BLOCKED: 1 em dash(es) found in staged changes.
    [asantico-hook] Project rule: no em dashes anywhere. Replace with commas, semicolons, or periods.

Exit code: 2

Interpretation: hook caught the violation and blocked the commit with a clear actionable message. The staged em dash was rolled back after the test.

---

## How the hook will fire during real implementation

When Claude Code attempts to run any `Bash` tool call (e.g., during the implementation phase when it executes `git commit` after finishing a task), this hook fires first. The hook:

1. Receives the event JSON via stdin.
2. Extracts the proposed command.
3. Skips out (exit 0) for non-destructive commands.
4. For destructive commands: runs pytest (once tests exist) and scans staged diffs for em dashes.
5. Exits 2 with a clear message if either check fails, blocking the command.

This satisfies Lab 2.3: "Add a hook that validates project state before high-impact actions (commit, push, delete, deploy)."
