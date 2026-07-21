#!/usr/bin/env bash
# ruff-baseline.sh — re-record the .ruff-baseline the release gate ratchets on.
#
# Deliberately one-way: it will LOWER the baseline (you cleaned something up)
# but REFUSES to raise it, because a gate you can silently relax is not a gate.
# If you genuinely need to raise it, edit .ruff-baseline by hand and say why in
# the commit message.
set -uo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."

BASELINE_FILE=".ruff-baseline"
RUFF=.venv-dev/bin/ruff
[ -x "$RUFF" ] || RUFF=$(command -v ruff || true)
[ -n "$RUFF" ] && [ -x "$RUFF" ] || { echo "✗ ruff not found — run tools/check.sh once" >&2; exit 1; }

FOUND=$("$RUFF" check src tests server --output-format json 2>/dev/null \
          | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
BASE=$(cat "$BASELINE_FILE" 2>/dev/null || echo 999999)

if [ "$FOUND" -gt "$BASE" ]; then
  echo "✗ refusing to RAISE the baseline ($BASE -> $FOUND)." >&2
  echo "  That would bless $((FOUND - BASE)) new lint error(s). Fix them instead." >&2
  exit 1
fi

echo "$FOUND" > "$BASELINE_FILE"
echo "✓ baseline recorded: $FOUND (was $BASE)"
