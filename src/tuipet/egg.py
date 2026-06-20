"""Egg sprites for the hatch sequence.

Uses the real DVPet egg sprites (extracted from armorEggs.png into
data/eggs.json.gz) — an idle wobble plus a crack/hatch animation derived from the
egg bitmap. Falls back to a procedurally drawn egg if the asset isn't present
(e.g. a fresh checkout before tools/setup_assets.sh has run).
"""
from __future__ import annotations
import gzip
import json
import os
from functools import lru_cache

_DATA = os.path.join(os.path.dirname(__file__), "data")


@lru_cache(maxsize=1)
def _real_eggs():
    path = os.path.join(_DATA, "eggs.json.gz")
    if not os.path.exists(path):
        return None
    try:
        with gzip.open(path, "rt") as fh:
            return [e for e in json.load(fh) if e]
    except (OSError, ValueError):
        return None


def _shift(rows, dx):
    """Shift a bitmap horizontally (for the idle wobble)."""
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, "0") for r in rows]
    if dx > 0:
        return ["0" * dx + r[:-dx] for r in rows]
    if dx < 0:
        return [r[-dx:] + "0" * -dx for r in rows]
    return list(rows)


_JAG = [0, 1, -1, 1, 0, -1, 1, -1, 0, 1, -1, 0, 1, -1, 1, 0, -1, 1, 0, -1]


def _crack(rows, depth):
    """Carve a jagged vertical crack from the top, growing with depth (0..1)."""
    rows = [list(r) for r in rows]
    h = len(rows)
    w = max(len(r) for r in rows)
    rows = [r + ["0"] * (w - len(r)) for r in rows]
    cx = w // 2
    n = int(depth * (h - 2))
    for y in range(1, 1 + n):
        x = cx + _JAG[y % len(_JAG)]
        for xx in (x, x + (1 if y % 2 else -1)):
            if 0 <= xx < w and 0 <= y < h and rows[y][xx] == "1":
                rows[y][xx] = "0"
    return ["".join(r) for r in rows]


# ---- procedural fallback egg (used only if the real asset is missing) -------
_FW, _FH = 16, 20


def _ellipse(squash=0):
    cx, cy = (_FW - 1) / 2, (_FH - 1) / 2
    rx, ry = _FW / 2 - 0.5, _FH / 2 - 0.5 - squash
    out = []
    for y in range(_FH):
        row = []
        for x in range(_FW):
            nx, ny = (x - cx) / rx, (y - cy) / ry
            row.append("1" if nx * nx + ny * ny <= 1.0 else "0")
        out.append("".join(row))
    return out


def _fallback_frames():
    base = _ellipse(0)
    return [base, _ellipse(1), _crack(base, 0.4), _crack(base, 0.7), _crack(base, 1.0)]


def frames(egg_type=0):
    eggs = _real_eggs()
    if eggs:
        base = eggs[egg_type % len(eggs)]
        idle2 = _shift(base, 1)                      # gentle wobble
        return [base, idle2, _crack(base, 0.4), _crack(base, 0.7), _crack(base, 1.0)]
    return _fallback_frames()


ROLES = {"idle": [0, 1], "egg_idle": [0, 1], "hatch": [2, 3, 4]}


def record(egg_type=0):
    fr = frames(egg_type)
    w = max(len(r) for r in fr[0])
    return {"num": -1, "name": "Digitama", "stage": "Egg",
            "attribute": "None", "field": "None", "element": "None",
            "spriteSet": 0, "spriteNum": 0, "w": w, "h": len(fr[0]),
            "frames": fr}


# back-compat: some callers referenced egg.FRAMES / egg.W / egg.H
FRAMES = frames(0)
W = max(len(r) for r in FRAMES[0])
H = len(FRAMES[0])


if __name__ == "__main__":
    import sys
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    for i, f in enumerate(frames(idx)):
        print(f"frame {i}")
        for r in f:
            print(r.replace("0", " ").replace("1", "#"))
        print()
