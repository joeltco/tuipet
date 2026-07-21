#!/usr/bin/env bash
# lint-gate.sh — the RATCHET quality gate, shared by deploy.sh and CI.
#
#   ./tools/lint-gate.sh ruff        check one tool against its baseline
#   ./tools/lint-gate.sh mypy
#   ./tools/lint-gate.sh bandit
#
# Why a ratchet and not a plain `ruff check`: CI's lint/typecheck/security jobs
# have been red since 2026-07-02 (ruff 395 — mostly F405 from the pet*.py
# `import *` split — mypy 25, bandit 2).  A strict gate would block every
# release until all of it is cleared; no gate at all is how three weeks of debt
# accumulated unnoticed behind a permanently-red build.  So:
#
#   findings <= baseline  -> pass (and say so when it drops, to ratchet down)
#   findings >  baseline  -> fail, pointing at the files you changed
#
# It can only tighten: re-record with tools/lint-baseline.sh, which REFUSES to
# raise a number.  Baselines live in .lint-baseline ("<tool> <count>" a line).
set -uo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."

TOOL="${1:-}"
case "$TOOL" in
  ruff|mypy|bandit) ;;
  *) echo "usage: $0 <ruff|mypy|bandit>" >&2; exit 2 ;;
esac

BASELINE_FILE=".lint-baseline"

# Prefer the local dev venv; fall back to PATH (CI installs into the job's env).
bin() {
  if [ -x ".venv-dev/bin/$1" ]; then echo ".venv-dev/bin/$1"
  else command -v "$1" || true; fi
}
BIN=$(bin "$TOOL")
if [ -z "$BIN" ]; then
  echo "✗ $TOOL not found — run tools/check.sh once to build .venv-dev" >&2
  exit 1
fi

# Each tool's finding count, machine-read (never scraped from a summary line:
# ruff's concise output appends two trailing lines and `wc -l` counts them).
count() {
  case "$TOOL" in
    ruff)   "$BIN" check src tests server --output-format json 2>/dev/null \
              | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" ;;
    mypy)   "$BIN" src/tuipet 2>/dev/null | grep -c ": error:" ;;
    bandit) "$BIN" -c pyproject.toml -r src server -q -f json 2>/dev/null \
              | python3 -c "import json,sys; print(len(json.load(sys.stdin)['results']))" ;;
  esac
}

# The human-readable findings, for the failure report.
listing() {
  case "$TOOL" in
    ruff)   "$BIN" check src tests server --output-format concise 2>/dev/null \
              | grep -vE "^(Found|\[\*\])" ;;
    mypy)   "$BIN" src/tuipet 2>/dev/null | grep ": error:" ;;
    bandit) "$BIN" -c pyproject.toml -r src server -q 2>/dev/null | grep -E "^>> Issue|   Location" ;;
  esac
}

FOUND=$(count)
[ -n "$FOUND" ] || { echo "✗ could not read $TOOL output" >&2; exit 1; }
BASE=$(awk -v t="$TOOL" '$1==t {print $2}' "$BASELINE_FILE" 2>/dev/null)
[ -n "$BASE" ] || { echo "✗ no baseline for '$TOOL' in $BASELINE_FILE" >&2; exit 1; }

if [ "$FOUND" -gt "$BASE" ]; then
  echo "  $TOOL: found $FOUND, baseline $BASE"
  echo "✗ $((FOUND - BASE)) NEW $TOOL finding(s) — this gate is a RATCHET:" >&2
  echo "  it never blocks the pre-existing pile, only additions to it." >&2
  echo >&2
  # A count can't say WHICH finding is new, but "a file you just touched" is
  # nearly always the answer -- so scope the report to the working diff, and
  # fall back to the tail when nothing is uncommitted (e.g. a CI run).
  TOUCHED=$( { git diff --name-only; git diff --cached --name-only; \
               git ls-files --others --exclude-standard; \
               git diff --name-only origin/main...HEAD; } 2>/dev/null | sort -u | grep -E '\.py$')
  ALL=$(listing)
  HITS=""
  [ -n "$TOUCHED" ] && HITS=$(echo "$ALL" | grep -F -f <(echo "$TOUCHED") 2>/dev/null || true)
  if [ -n "$HITS" ]; then
    echo "  in files you changed:" >&2
    echo "$HITS" | head -20 >&2
  else
    echo "  (none in your changed files — most recent findings:)" >&2
    echo "$ALL" | tail -15 >&2
  fi
  echo >&2
  echo "  Fix them, or re-record with tools/lint-baseline.sh if you truly" >&2
  echo "  intend the new count." >&2
  exit 1
fi

if [ "$FOUND" -lt "$BASE" ]; then
  echo "  $TOOL: found $FOUND, baseline $BASE — ✅ $((BASE - FOUND)) fewer!"
  echo "  ratchet it down:  ./tools/lint-baseline.sh $TOOL"
else
  echo "  $TOOL: found $FOUND, baseline $BASE -> OK"
fi
exit 0
