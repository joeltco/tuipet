"""Egg sprites for the hatch sequence.

Uses the real DVPet egg sprites (extracted from armorEggs.png into
data/eggs.json.gz). Each egg has 3 real DVPet frames (idle, settle, cracked-open),
so hatching plays a real carved crack before the baby. The side-to-side shake is an
xshift at render time, not baked into extra frames. No drawn art.
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


def hatch_targets(egg_type=0):
    """All species nums this egg can hatch into (one Baby I per egg here)."""
    t = hatch_target(egg_type)
    return [t] if t is not None else []


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


# --- DVPet eggUnlock.csv-driven egg unlock (real data; see data.load_egg_unlock) ---
# Each egg gates on the same signals the device tracks (generation, album/history,
# X-Antibody, reached stage, maps cleared, tournament trophies, previous-generation
# attribute/element/field). Condition met + price 0 -> auto-unlocked (free to hatch,
# or temp for this generation); condition met + price > 0 -> BUYABLE in the egg shop
# (shopscreen Eggs tab) and bought eggs are owned permanently. The egg SELECT shows
# only hatchable (owned/temp) eggs. persistence.get_progress() supplies the state.
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
        return ("buyable", rule["price"])      # condition met but priced -> buy in the egg shop
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


def hatchable_eggs(prog, owned):
    """Eggs ready to hatch right now (owned + temp) -- what the egg select shows."""
    st = egg_states(prog, owned)
    return sorted(i for i, (s, _) in st.items() if s in ("owned", "temp"))


def buyable_eggs(prog, owned):
    """(idx, price) for eggs whose condition is met but that cost bits -- the egg shop."""
    st = egg_states(prog, owned)
    return [(i, p) for i, (s, p) in sorted(st.items()) if s == "buyable"]


def shop_egg_entry(idx, price):
    """A shop-row dict for a buyable egg (compatible with shopscreen rendering)."""
    return {"key": "egg:%d" % idx, "name": hatch_name(idx), "price": int(price),
            "egg_idx": idx}


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
