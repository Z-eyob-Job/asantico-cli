#!/usr/bin/env bash
# Pre-tool-use validator for the Asantico CLI project.
# Reads the JSON event Claude Code sends on stdin, inspects the proposed Bash
# command, and blocks high-impact operations if the project is not in a valid
# state. Validation = pytest must pass and no em dashes in staged content.

set -euo pipefail

# Read the JSON event from stdin
event=$(cat)

# Extract the proposed command (jq if available, fallback to grep)
if command -v jq >/dev/null 2>&1; then
  cmd=$(echo "$event" | jq -r '.tool_input.command // empty')
else
  cmd=$(echo "$event" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/')
fi

# High-impact patterns we want to validate before
high_impact_pattern='git commit|git push|rm -rf|find .* -delete|git reset --hard'

if ! echo "$cmd" | grep -Eq "$high_impact_pattern"; then
  # Not a high-impact command, allow through silently
  exit 0
fi

echo "[asantico-hook] High-impact command detected: validating project state..." >&2
echo "[asantico-hook] Command: $cmd" >&2

# Repo root
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

# Check 1: pytest passes (only if tests directory has any test files)
if compgen -G "tests/**/test_*.py" >/dev/null 2>&1 || compgen -G "tests/test_*.py" >/dev/null 2>&1; then
  echo "[asantico-hook] Running pytest..." >&2
  if ! .venv/bin/pytest --quiet --no-header 2>&1 | tee /tmp/asantico-hook-pytest.log >&2; then
    echo "" >&2
    echo "[asantico-hook] BLOCKED: pytest failed. Fix tests before the command runs." >&2
    exit 2
  fi
  echo "[asantico-hook] pytest passed." >&2
else
  echo "[asantico-hook] No test files yet, skipping pytest check." >&2
fi

# Check 2: no em dashes (U+2014) in staged or tracked source content
if git diff --cached --name-only 2>/dev/null | grep -qE '\.(py|md|json)$'; then
  staged_em_dashes=$(git diff --cached -U0 | grep -c $'\xe2\x80\x94' || true)
  if [ "$staged_em_dashes" -gt 0 ]; then
    echo "[asantico-hook] BLOCKED: $staged_em_dashes em dash(es) found in staged changes." >&2
    echo "[asantico-hook] Project rule: no em dashes anywhere. Replace with commas, semicolons, or periods." >&2
    exit 2
  fi
fi

echo "[asantico-hook] Validation passed. Allowing command." >&2
exit 0
