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

cd "$(dirname "$(readlink -f "$0")")"

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

if [ "$CONFIRM" = 1 ]; then
  read -r -p "Commit, tag, push$([ "$PUBLISH" = 1 ] && echo ' and publish')? [y/N] " ans
  case "$ans" in y|Y) ;; *) git checkout -- pyproject.toml; echo "aborted (reverted bump)"; exit 1 ;; esac
fi

# --- commit / tag / push ----------------------------------------------------
git add -A
git commit -q -m "release $TAG"
git tag "$TAG"
git push origin main
git push origin "$TAG"
echo "==> pushed main + $TAG"

# --- publish ----------------------------------------------------------------
if [ "$PUBLISH" = 1 ]; then
  if ! python3 -c "import twine" 2>/dev/null; then
    [ -x .release-venv/bin/twine ] || { echo "==> setting up .release-venv (twine)"; python3 -m venv .release-venv && .release-venv/bin/pip install -q --upgrade pip twine; }
    TWINE=".release-venv/bin/twine"
  else
    TWINE="python3 -m twine"
  fi
  echo "==> build"
  rm -rf dist
  python3 -m build
  echo "==> upload to PyPI"
  $TWINE upload dist/*
  echo "==> published tuipet $NEXT — https://pypi.org/project/tuipet/$NEXT/"
else
  echo "==> done; watch the release workflow at https://github.com/joeltco/tuipet/actions"
fi
