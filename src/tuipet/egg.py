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


# --- DVPet eggUnlock.csv-driven egg unlock (real data; see data.load_egg_unlock) ---
# Each egg gates on the same signals the device tracks (generation, album/history,
# X-Antibody, reached stage, maps cleared, tournament trophies, previous-generation
# attribute/element/field). Conditions met + price>0 -> licensable in the egg shop;
# price 0 + permanent -> auto-unlocked; price 0 + temporary -> available that
# generation only. persistence.get_progress() supplies the live state.
_WIN_EGGS = {46: 50, 47: 100}      # tuipet-only "???" eggs (not in eggUnlock.csv) -> lifetime wins


def _conditions_met(rule, prog):
    from . import data
    if rule["gen"] is not None and prog["max_gen"] < rule["gen"]:
        return False
    if rule["stage"] is not None:
        want = data.STAGE_ORDER.index(rule["stage"]) if rule["stage"] in data.STAGE_ORDER else 99
        if prog["max_stage"] < want:
            return False
    if rule["xanti"] and not (prog["last_xanti"] or prog["xanti_ever"]):
        return False
    if rule["tourney"] is not None and rule["tourney"] not in prog["tourneys"]:
        return False
    if rule["map"] is not None and rule["map"] not in prog["maps"]:
        return False
    if rule["history"] and not all(n in prog["album"] for n in rule["history"]):
        return False
    if rule["prev_field"] is not None and prog["last_field"] != rule["prev_field"]:
        return False
    if rule["prev_attr"] is not None and prog["last_attr"] != rule["prev_attr"]:
        return False
    if rule["prev_elem"] is not None and prog["last_elem"] != rule["prev_elem"]:
        return False
    if rule["obedience"] is not None and prog["last_obed"] < rule["obedience"]:
        return False
    if rule["mood"] is not None and prog["last_mood"] < rule["mood"]:
        return False
    # gates tuipet does not model -> egg stays locked (e.g. password, food/item used)
    if rule["password"] is not None:
        return False
    if rule["food"] is not None or rule["item"] is not None or rule["habitat"] is not None:
        return False
    if rule["zone"] is not None:
        return False
    return True


def _fallback_pool():
    """Tuipet-only eggs absent from eggUnlock.csv (excluding the win-eggs), in order."""
    from . import data
    rules = data.load_egg_unlock()
    return [i for i in range(count())
            if i not in rules and i not in _WIN_EGGS]


def egg_state(idx, prog, owned):
    """('owned'|'buyable'|'temp'|'locked', price) for one egg index."""
    from . import data
    rule = data.load_egg_unlock().get(idx)
    if rule is None:                                   # tuipet-only egg: simple fallback
        if idx in owned:
            return ("owned", 0)
        need = _WIN_EGGS.get(idx)
        if need is not None:
            return ("owned", 0) if prog["wins"] >= need else ("locked", 0)
        pool = _fallback_pool()
        rank = pool.index(idx) if idx in pool else 99
        return ("owned", 0) if len(prog["album"]) > rank else ("locked", 0)
    if rule["start"] or idx in owned:
        return ("owned", 0)
    if not _conditions_met(rule, prog):
        return ("locked", rule["price"])
    if rule["price"] > 0:
        return ("buyable", rule["price"])
    return ("owned", 0) if rule["can_perm"] else ("temp", 0)


def egg_states(prog, owned):
    return {i: egg_state(i, prog, owned) for i in range(count())}


def auto_owned(prog, owned):
    """Eggs that just became permanent (price-0 met, can_perm) -> caller persists them."""
    from . import data
    rules = data.load_egg_unlock()
    out = []
    for i in range(count()):
        if i in owned:
            continue
        rule = rules.get(i)
        if rule and not rule["start"] and rule["price"] == 0 and rule["can_perm"] \
                and _conditions_met(rule, prog):
            out.append(i)
    return out


def password_egg(code):
    """Egg index unlocked by a secret password (DVPet Copymon codes), or None.
    Case-insensitive; e.g. 'Accentier' -> Carimon."""
    from . import data
    code = (code or "").strip().lower()
    if not code:
        return None
    for idx, rule in data.load_egg_unlock().items():
        if rule.get("password") and rule["password"].lower() == code:
            return idx
    return None


def selectable_eggs(prog, owned):
    """Egg indices the player may pick or license now (owned + temp + buyable)."""
    st = egg_states(prog, owned)
    return sorted(i for i, (s, _) in st.items() if s != "locked")


def locked_hint(prog, owned):
    """Shortest 'what unlocks next' hint among locked eggs ('' if none)."""
    from . import data
    rules = data.load_egg_unlock()
    for i in range(count()):
        s, _ = egg_state(i, prog, owned)
        if s == "locked" and rules.get(i) and rules[i]["desc"]:
            return rules[i]["desc"]
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
