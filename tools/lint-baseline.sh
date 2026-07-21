#!/usr/bin/env bash
# lint-baseline.sh — re-record the .lint-baseline counts the gate ratchets on.
#
#   ./tools/lint-baseline.sh              all three tools
#   ./tools/lint-baseline.sh ruff mypy    just these
#
# Deliberately one-way: it LOWERS a baseline (you cleaned something up) but
# REFUSES to raise one, because a gate you can silently relax is not a gate.
# If a number must genuinely go up -- say CI's environment reports a type error
# your machine can't -- edit .lint-baseline by hand and say why in the commit.
set -uo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."

BASELINE_FILE=".lint-baseline"
TOOLS=("$@")
[ ${#TOOLS[@]} -gt 0 ] || TOOLS=(ruff mypy bandit)

bin() {
  if [ -x ".venv-dev/bin/$1" ]; then echo ".venv-dev/bin/$1"
  else command -v "$1" || true; fi
}

count() {
  local tool=$1 b; b=$(bin "$tool")
  [ -n "$b" ] || { echo "✗ $tool not found — run tools/check.sh once" >&2; return 1; }
  case "$tool" in
    ruff)   "$b" check src tests server --output-format json 2>/dev/null \
              | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" ;;
    mypy)   "$b" src/tuipet 2>/dev/null | grep -c ": error:" ;;
    bandit) "$b" -c pyproject.toml -r src server -q -f json 2>/dev/null \
              | python3 -c "import json,sys; print(len(json.load(sys.stdin)['results']))" ;;
    *) echo "✗ unknown tool '$tool'" >&2; return 1 ;;
  esac
}

rc=0
for tool in "${TOOLS[@]}"; do
  found=$(count "$tool") || { rc=1; continue; }
  base=$(awk -v t="$tool" '$1==t {print $2}' "$BASELINE_FILE" 2>/dev/null)
  base=${base:-999999}
  if [ "$found" -gt "$base" ]; then
    echo "✗ $tool: refusing to RAISE the baseline ($base -> $found)." >&2
    echo "  That would bless $((found - base)) new finding(s). Fix them instead." >&2
    rc=1; continue
  fi
  tmp=$(mktemp)
  awk -v t="$tool" '$1!=t' "$BASELINE_FILE" 2>/dev/null > "$tmp" || true
  echo "$tool $found" >> "$tmp"
  sort -o "$BASELINE_FILE" "$tmp"
  rm -f "$tmp"
  if [ "$base" = "999999" ]; then echo "✓ $tool: baseline recorded: $found"
  else echo "✓ $tool: baseline $base -> $found"; fi
done
exit $rc
