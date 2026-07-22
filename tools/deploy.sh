#!/usr/bin/env bash
# deploy.sh — release tuipet end to end: bump version, test, commit, tag, push,
# and publish to PyPI.  Run from anywhere; it cd's to the repo root.
#
#   ./deploy.sh                 patch bump (0.1.0 -> 0.1.1) + publish
#   ./deploy.sh minor           0.1.0 -> 0.2.0
#   ./deploy.sh major           0.1.0 -> 1.0.0
#   ./deploy.sh 0.3.2           explicit version
#   ./deploy.sh patch -y        skip the confirmation prompt
#   ./deploy.sh patch --no-publish   commit + tag + push only; let GitHub
#                                    Actions (release.yml) publish the tag
#
# PyPI auth comes from ~/.pypirc (token).  twine is installed on demand into a
# local, gitignored .release-venv.  tests + build use the system python.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/.."

BUMP=""
CONFIRM=1
PUBLISH=1
for a in "$@"; do
  case "$a" in
    -y|--yes)      CONFIRM=0 ;;
    --no-publish)  PUBLISH=0 ;;
    -h|--help)     sed -n '2,18p' "$0"; exit 0 ;;
    -*)            echo "✗ unknown flag: $a" >&2; exit 1 ;;
    *)             BUMP="$a" ;;
  esac
done
BUMP="${BUMP:-patch}"

# --- preflight --------------------------------------------------------------
BRANCH=$(git rev-parse --abbrev-ref HEAD)
[ "$BRANCH" = "main" ] || { echo "✗ not on main (on '$BRANCH')" >&2; exit 1; }

CUR=$(python3 -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
NEXT=$(python3 - "$CUR" "$BUMP" <<'PY'
import sys
cur, bump = sys.argv[1], sys.argv[2]
if bump not in ("patch", "minor", "major"):
    assert all(p.isdigit() for p in bump.split(".")) and bump.count(".") == 2, f"bad version '{bump}'"
    print(bump); sys.exit()
maj, mn, pa = (list(map(int, cur.split("."))) + [0, 0, 0])[:3]
if   bump == "patch": pa += 1
elif bump == "minor": mn, pa = mn + 1, 0
elif bump == "major": maj, mn, pa = maj + 1, 0, 0
print(f"{maj}.{mn}.{pa}")
PY
)
TAG="v$NEXT"

git rev-parse "$TAG" >/dev/null 2>&1 && { echo "✗ tag $TAG already exists" >&2; exit 1; }

echo "tuipet release:  $CUR  ->  $NEXT   (tag $TAG)"
if [ "$PUBLISH" = 1 ]; then echo "  → will publish to PyPI from this machine"
else                        echo "  → git only; GitHub Actions publishes the tag"; fi

# --- gate on the "WHAT'S NEW" line ------------------------------------------
# The title-screen news (app.py WHATS_NEW) is hand-maintained and shipped stale
# on 0.2.374/0.2.375 — nothing forced an update.  Refuse to release unless the
# working tree's WHATS_NEW differs from the last release tag's.  (No prior tag
# = first release, nothing to compare, so it passes.)
LASTTAG=$(git describe --tags --abbrev=0 --match 'v*' 2>/dev/null || true)
if [ -n "$LASTTAG" ]; then
  python3 - "$LASTTAG" <<'PY' || exit 1
import ast, subprocess, sys
def whats_new(src):
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "WHATS_NEW" for t in node.targets):
            return ast.literal_eval(node.value)
    return None
path = "src/tuipet/app.py"
old = whats_new(subprocess.check_output(["git", "show", f"{sys.argv[1]}:{path}"], text=True))
new = whats_new(open(path).read())
if new is None:
    sys.exit("✗ WHATS_NEW not found in app.py")
if old == new:
    sys.exit(f"✗ WHATS_NEW is unchanged since {sys.argv[1]} — update the title-screen "
             f"news in app.py before releasing (or it ships stale like 0.2.374/375 did).")
print("✓ WHATS_NEW updated since", sys.argv[1])
PY
fi

# --- gate on lint (ratchet) -------------------------------------------------
# Ruff has been red on main since 2026-07-02 and CI's lint job with it, so a
# strict `ruff check` here would block every release until ~400 pre-existing
# findings are cleaned up.  Instead the gate RATCHETS: it fails only when the
# count rises above .ruff-baseline, so new lint debt can't ride out in a
# release while the old pile gets fixed at its own pace (2026-07-21).
echo "==> ruff (gate)"
./tools/lint-gate.sh ruff

# --- gate on tests ----------------------------------------------------------
echo "==> tests"
python3 -m pytest -q

# --- bump pyproject ---------------------------------------------------------
python3 - "$NEXT" <<'PY'
import re, sys
v = sys.argv[1]; p = "pyproject.toml"; s = open(p).read()
s2 = re.sub(r'(?m)^version\s*=\s*".*"$', f'version = "{v}"', s, count=1)
assert s != s2, "version line not found in pyproject.toml"
open(p, "w").write(s2)
PY

# only prompt on a real terminal -- a headless run (ssh/CI) is implicitly
# confirmed, never a hang-then-abort under set -e (deploy audit 2026-07-09)
if [ "$CONFIRM" = 1 ] && [ -t 0 ]; then
  read -r -p "Commit, tag, push$([ "$PUBLISH" = 1 ] && echo ' and publish')? [y/N] " ans
  case "$ans" in y|Y) ;; *) git checkout -- pyproject.toml; echo "aborted (reverted bump)"; exit 1 ;; esac
fi

# --- changelog: the release writes its own entry ----------------------------
# CHANGELOG.md drifted 19 releases behind (doc audit 2026-07-22) because a
# human had to remember it.  The deploy already parses WHATS_NEW for the
# gate; append it as the entry, verbatim -- the doc's stated contract is
# "the same line each version shows on its title screen".
python3 - "$NEXT" <<'PY'
import ast, datetime, re, sys
v = sys.argv[1]
src = open("src/tuipet/app.py").read()
w = next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(src))
         if isinstance(n, ast.Assign) and any(
             isinstance(t, ast.Name) and t.id == "WHATS_NEW" for t in n.targets))
m = re.match(r"^([A-Z0-9 ,'\u2019\-\u2014:.!?&]+?)[:\u2014]\s", w)
title = (m.group(1).strip() if m else w.split(":")[0])[:60]
d = datetime.date.today().isoformat()
entry = f"## {v} \u2014 {title} ({d})\n\n{' '.join(w.split())}\n\n"
p = "CHANGELOG.md"
s = open(p).read()
i = s.index("## ")
open(p, "w").write(s[:i] + entry + s[i:])
print(f"==> changelog: {v} \u2014 {title}")
PY

# --- commit / tag / push ----------------------------------------------------
git add -A
git commit -q -m "release $TAG"
git tag "$TAG"
git push origin main
git push origin "$TAG"
echo "==> pushed main + $TAG"

# --- publish ----------------------------------------------------------------
if [ "$PUBLISH" = 1 ]; then
  # build + twine from a self-contained venv (system python lacks the pypa build
  # CLI and twine); created once, reused after.
  if [ ! -x .release-venv/bin/twine ] || [ ! -x .release-venv/bin/python ]; then
    echo "==> setting up .release-venv (build + twine)"
    python3 -m venv .release-venv
    .release-venv/bin/pip install -q --upgrade pip build twine
  fi
  echo "==> build"
  rm -rf dist
  .release-venv/bin/python -m build
  echo "==> upload to PyPI"
  .release-venv/bin/twine upload dist/*
  echo "==> published tuipet $NEXT — https://pypi.org/project/tuipet/$NEXT/"

  # --- verify it's actually INSTALLABLE ---------------------------------------
  # twine returning does NOT mean the release is live: PyPI's install index lags
  # the upload by up to a couple minutes, and in that window a fresh `pip install
  # -U tuipet` (and the in-game updater) still gets the OLD version or 404s -- so
  # a release that "succeeded" looks broken.  Poll the REAL signal (pip resolving
  # the exact version off the index, cache bypassed -- the JSON API propagates on
  # its own, faster schedule and is NOT a reliable proxy) until it lands, so a
  # release only reports done once pip can genuinely install it.
  echo "==> verifying $NEXT is installable (waiting out PyPI index propagation)…"
  for i in $(seq 1 30); do
    if .release-venv/bin/pip install --dry-run --no-deps --no-cache-dir \
         "tuipet==$NEXT" >/dev/null 2>&1; then
      echo "==> confirmed live — pip can install tuipet $NEXT"
      break
    fi
    if [ "$i" -eq 30 ]; then
      echo "⚠ tuipet $NEXT uploaded but still not pip-installable after ~5min." >&2
      echo "  It should appear shortly; PyPI is just slow. Verify at:" >&2
      echo "  https://pypi.org/project/tuipet/$NEXT/" >&2
    else
      sleep 10
    fi
  done
else
  echo "==> done; watch the release workflow at https://github.com/joeltco/tuipet/actions"
fi
