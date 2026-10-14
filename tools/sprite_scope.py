"""Scope lock for sprite edits: run BEFORE showing Joel any sprite change.

Lists every monster/frame that differs from the base, fails if anything
changed outside the ones Joel named, and fails on any pixel that is not
black (1) or transparent (0) -- mono only.  Born 2026-10-14 after edits to
sprites he never named (Little Godzilla, "I ONLY SHOWED YOU ONE").

  sprite_scope.py --allow 1624,1625            working sprites.json.gz vs git HEAD
  sprite_scope.py --base old.json --new approved.json --allow babygodzilla
      (godzilla-line style {name: [frames]} files; or sprites.json.gz lists)
"""
import argparse
import gzip
import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SPRITES = "src/tuipet/data/sprites.json.gz"


def _parse(raw):
    d = json.loads(raw)
    if isinstance(d, list):                       # tuipet sprites.json.gz rows
        return {str(e["num"]): e["frames"] for e in d}
    return {str(k): v for k, v in d.items()}      # {name: [frames]}


def _load(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return _parse(raw.decode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow", default="", help="comma list of monsters Joel named")
    ap.add_argument("--base", help="base file (default: sprites.json.gz at git HEAD)")
    ap.add_argument("--new", help="new file (default: working sprites.json.gz)")
    a = ap.parse_args()
    allow = {x.strip() for x in a.allow.split(",") if x.strip()}

    if a.base:
        base = _load(a.base)
    else:
        raw = subprocess.check_output(["git", "-C", ROOT, "show", f"HEAD:{SPRITES}"])
        base = _parse(gzip.decompress(raw).decode("utf-8"))
    new = _load(a.new or os.path.join(ROOT, SPRITES))

    bad = 0
    for k in sorted(set(base) | set(new), key=lambda s: (len(s), s)):
        b, n = base.get(k), new.get(k)
        if b == n:
            continue
        frames = ([i for i in range(max(len(b or []), len(n or [])))
                   if (b or [None] * 99)[i:i + 1] != (n or [None] * 99)[i:i + 1]])
        ok = k in allow
        bad += not ok
        print(f"{'ok     ' if ok else 'OUTSIDE'} {k}: frames {frames}")
    for k, fr in new.items():
        for i, f in enumerate(fr):
            stray = {c for row in f for c in row} - {"0", "1"}
            if stray:
                bad += 1
                print(f"COLOUR  {k} frame {i}: {sorted(stray)} (mono only: 0/1)")
    print("SCOPE OK" if not bad else f"SCOPE FAIL: {bad} problem(s) -- revert them first")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
