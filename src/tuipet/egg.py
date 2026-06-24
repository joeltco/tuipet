"""Egg sprites for the hatch sequence.

Uses the real DVPet egg sprites (extracted from armorEggs.png into
data/eggs.json.gz), animated only by a horizontal shake — no drawn art. Each egg
has a single frame in armorEggs, so hatching is a shake, not a carved crack.
"""
from __future__ import annotations
import gzip
import random
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
    """A Fresh creature (DigimonNum) this egg hatches into -- chosen at random among
    the egg's targets, so generic "mystery" eggs surprise you (DVPet behaviour)."""
    eggs = _real_eggs()
    if not eggs:
        return None
    return random.choice(eggs[egg_type % len(eggs)]["hatch"])


def hatch_targets(egg_type=0):
    """All DigimonNums this egg can hatch into (to preview its habitat)."""
    eggs = _real_eggs()
    return list(eggs[egg_type % len(eggs)]["hatch"]) if eggs else []


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


# --- DM20-style egg unlock (tuipet adaptation; see memory digimon-vpet-dm20) ---
BASE_EGGS = (1, 2, 3, 4, 5)        # always unlocked: Botamon/Punimon/Poyomon/Yuramon/Zurumon (DM20 Ver.1-5)
WIN_EGGS = ((50, 46), (100, 47))   # mystery "???" eggs unlocked by lifetime battle wins
ALBUM_PER_EGG = 1                  # each new distinct Digimon registered opens the next egg


def _album_pool():
    """Egg indices that unlock progressively via the album, in order."""
    n = count()
    base = {i for i in BASE_EGGS if i < n}
    win_idx = {idx for _, idx in WIN_EGGS}
    return [i for i in range(n) if i not in base and i not in win_idx]


def unlocked_eggs(album_count, wins):
    """Egg indices available given album size (distinct Digimon raised) + lifetime wins."""
    n = count()
    unlocked = {i for i in BASE_EGGS if i < n}
    for need, idx in WIN_EGGS:
        if wins >= need and idx < n:
            unlocked.add(idx)
    pool = _album_pool()
    unlocked.update(pool[:max(0, album_count // ALBUM_PER_EGG)])
    return unlocked


def next_unlock_hint(album_count, wins):
    """Short hint for opening the next locked egg ('' if all unlocked)."""
    pool = _album_pool()
    got = max(0, album_count // ALBUM_PER_EGG)
    if got < len(pool):
        need = (got + 1) * ALBUM_PER_EGG - album_count
        return "%d more Digimon → egg" % need
    for win_need, idx in WIN_EGGS:
        if idx < count() and wins < win_need:
            return "%d more wins → egg" % (win_need - wins)
    return ""


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
