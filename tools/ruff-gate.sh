#!/usr/bin/env bash
# ruff-gate.sh — the RATCHET lint gate used by deploy.sh.
#
# Ruff has been red on main since 2026-07-02 (395 findings: 268 F405 from the
# pet*.py `import *` module split, 116 F401, plus a few E401/F811/F841/W291).
# A plain `ruff check` in the release path would block every release until all
# of that is cleaned up; doing nothing lets the pile keep growing. So the gate
# compares against a COMMITTED baseline instead:
#
#   findings <= baseline  -> pass (and tell you when it dropped, so the
#                            baseline can ratchet down)
#   findings >  baseline  -> fail, with the NEW findings printed
#
# It can only ever tighten: re-record with tools/ruff-baseline.sh, which
# REFUSES to raise the number.
#
#   ./tools/ruff-gate.sh          check against the baseline
set -uo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."

BASELINE_FILE=".ruff-baseline"
VENV=.venv-dev
RUFF="$VENV/bin/ruff"
[ -x "$RUFF" ] || RUFF=$(command -v ruff || true)
if [ -z "$RUFF" ] || [ ! -x "$RUFF" ]; then
  echo "✗ ruff not found — run tools/check.sh once to build $VENV" >&2
  exit 1
fi

count() { "$RUFF" check src tests server --output-format json 2>/dev/null \
            | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"; }

FOUND=$(count)
[ -n "$FOUND" ] || { echo "✗ could not read ruff output" >&2; exit 1; }
BASE=$(cat "$BASELINE_FILE" 2>/dev/null || echo 0)

if [ "$FOUND" -gt "$BASE" ]; then
  echo "  found $FOUND, baseline $BASE"
  echo "✗ $((FOUND - BASE)) NEW ruff error(s) — the release gate is a RATCHET:" >&2
  echo "  it never blocks the pre-existing pile, only additions to it." >&2
  echo >&2
  # Point at the files you actually touched rather than tailing 395 findings
  # most of which predate you -- the baseline counts, so it cannot tell you
  # WHICH finding is new, but "uncommitted files with findings" is nearly
  # always the answer.
  TOUCHED=$( { git diff --name-only; git diff --cached --name-only; \
               git ls-files --others --exclude-standard; } 2>/dev/null | sort -u)
  ALL=$("$RUFF" check src tests server --output-format concise 2>/dev/null)
  HITS=""
  if [ -n "$TOUCHED" ]; then
    HITS=$(echo "$ALL" | grep -F -f <(echo "$TOUCHED") 2>/dev/null || true)
  fi
  if [ -n "$HITS" ]; then
    echo "  in files you changed:" >&2
    echo "$HITS" | head -20 >&2
  else
    echo "  (none in your changed files — most recent findings:)" >&2
    echo "$ALL" | grep -vE "^(Found|\[\*\])" | tail -15 >&2
  fi
  echo >&2
  echo "  Fix them, or re-record with tools/ruff-baseline.sh if you truly" >&2
  echo "  intend the new count." >&2
  exit 1
fi

if [ "$FOUND" -lt "$BASE" ]; then
  echo "  found $FOUND, baseline $BASE — ✅ $((BASE - FOUND)) fewer!"
  echo "  ratchet it down:  echo $FOUND > $BASELINE_FILE"
else
  echo "  found $FOUND, baseline $BASE -> OK"
fi
exit 0
