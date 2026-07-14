#!/usr/bin/env bash
# check.sh — run the local 4-way quality cocktail, mirroring .github/workflows/ci.yml:
#   ruff (lint) + mypy (types) + bandit (security) + pytest.
# Tools + deps live in a gitignored .venv-dev (created on first run).
set -uo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."

VENV=.venv-dev
if [ ! -x "$VENV/bin/ruff" ]; then
  echo "==> first run: setting up $VENV (pip install -e .[dev]) ..."
  [ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -e ".[dev]"
fi
BIN="$VENV/bin"

rc=0
run() { echo; echo "===== $1 ====="; shift; "$@" || rc=1; }
run "ruff (lint)"      "$BIN/ruff" check src tests server
run "mypy (types)"     "$BIN/mypy" src/tuipet
run "bandit (security)" "$BIN/bandit" -c pyproject.toml -r src server -q
run "pytest"           "$BIN/python" -m pytest -q

echo
if [ $rc -eq 0 ]; then echo "✅ all four passed"; else echo "❌ something failed (exit $rc)"; fi
exit $rc
