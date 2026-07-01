"""Egg sprites for the hatch sequence.

Uses the real DVPet egg sprites (extracted from armorEggs.png into
data/eggs.json.gz). Each egg has 3 real DVPet frames (idle, settle, cracked-open),
so hatching plays a real carved crack before the baby. The side-to-side shake is an
xshift at render time, not baked into extra frames. No drawn art.

Egg SELECTION is a free version-starter pick (DM20 lets you choose any of its
versions), so every baby is always hatchable — there is no unlock/economy gating.
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
    """Real Digitama egg (spritesEgg0.png, the Egg-stage creature sheet): the 3 real
    DVPet frames -- [0] idle egg, [1] settle/bulge, [2] cracked-open (shell breaks,
    baby emerges). The hatch role (ROLES["hatch"]=[0,1,2]) plays all three; the
    side-to-side shake is applied as an xshift at render time, not baked into extra
    frames. No drawn art -- the crack frame comes straight from DVPet's sheet."""
    eggs = _real_eggs()
    if not eggs:
        return [["0"]]                               # only before setup_assets.sh
    fr = eggs[egg_type % len(eggs)]["frames"]        # real frames: idle / settle / crack
    f0 = fr[0]
    f1 = fr[1] if len(fr) > 1 else f0
    f2 = fr[2] if len(fr) > 2 else f1                 # the REAL crack frame (was discarded)
    return [f0, f1, f2]

ROLES = {"idle": [0, 1], "egg_idle": [0, 1], "hatch": [0, 1, 2]}  # frames: egg -> crack -> baby


def _babies():
    from . import species
    return species.babies()


def hatch_target(egg_type=0):
    """The Baby I species num this egg hatches into (authentic DM20 roster)."""
    babies = _babies()
    return babies[egg_type % len(babies)]["num"] if babies else None


def hatch_name(egg_type=0):
    babies = _babies()
    return babies[egg_type % len(babies)]["name"] if babies else "?"


def count():
    return len(_babies()) or 1


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
