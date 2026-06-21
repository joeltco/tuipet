"""Egg sprites for the hatch sequence.

Uses the real DVPet egg sprites (extracted from armorEggs.png into
data/eggs.json.gz), animated only by a horizontal shake — no drawn art. Each egg
has a single frame in armorEggs, so hatching is a shake, not a carved crack.
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


def frames(egg_type=0):
    """Real Digitama egg (spritesEgg0.png, the Egg-stage creature sheet). Each egg
    has its own animation frames; the hatch role adds a shake. No drawn art."""
    eggs = _real_eggs()
    if not eggs:
        return [["0"]]                               # only before setup_assets.sh
    fr = eggs[egg_type % len(eggs)]["frames"]        # the egg's real animation frames
    f0 = fr[0]
    f1 = fr[1] if len(fr) > 1 else f0
    return [f0, f1, _shift(f0, -1), f0, _shift(f0, 1)]

ROLES = {"idle": [0, 1], "egg_idle": [0, 1], "hatch": [2, 3, 4]}


def hatch_target(egg_type=0):
    """The Fresh creature (DigimonNum) this egg hatches into, or None."""
    eggs = _real_eggs()
    return eggs[egg_type % len(eggs)]["hatch"] if eggs else None


def hatch_name(egg_type=0):
    eggs = _real_eggs()
    return eggs[egg_type % len(eggs)]["hatch_name"] if eggs else "?"


def count():
    eggs = _real_eggs()
    return len(eggs) if eggs else 1


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
