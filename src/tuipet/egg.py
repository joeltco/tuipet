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


def frames(egg_type=0):
    """Real Digitama egg (spritesEgg0.png, the Egg-stage creature sheet): the 3 real
    DVPet frames -- [0] idle egg, [1] settle/bulge, [2] cracked-open (shell breaks,
    baby emerges). The hatch role (ROLES["hatch"]=[0,1,2]) plays all three; the
    side-to-side shake is applied as an xshift at render time, not baked into extra
    frames. No drawn art -- the crack frame comes straight from DVPet's sheet."""
    eggs = _real_eggs()
    if not eggs:
        return [["0"]]                               # only before setup_assets.sh
    fr = eggs[_idx(egg_type, len(eggs))]["frames"]   # real frames: idle / settle / crack
    f0 = fr[0]
    f1 = fr[1] if len(fr) > 1 else f0
    f2 = fr[2] if len(fr) > 2 else f1                 # the REAL crack frame (was discarded)
    return [f0, f1, f2]

ROLES = {"idle": [0, 1], "egg_idle": [0, 1], "hatch": [0, 1, 2]}  # frames: egg -> crack -> baby


def _idx(egg_type, n):
    """A SAFE bank index whatever the caller holds -- the 'guide' incident
    (2026-07-18) proved a sentinel string can reach the renderer through a
    poisoned save; the display must never crash over it."""
    try:
        return int(egg_type) % n
    except (TypeError, ValueError):
        return 0


def hatch_target(egg_type=0):
    """A Fresh creature (DigimonNum) this egg hatches into -- chosen at random among
    the egg's targets, so generic "mystery" eggs surprise you (DVPet behaviour)."""
    eggs = _real_eggs()
    if not eggs:
        return None
    return random.choice(eggs[_idx(egg_type, len(eggs))]["hatch"])


def hatch_targets(egg_type=0):
    """All DigimonNums this egg can hatch into (the hatch preview)."""
    eggs = _real_eggs()
    return list(eggs[_idx(egg_type, len(eggs))]["hatch"]) if eggs else []


def hatch_name(egg_type=0):
    eggs = _real_eggs()
    return eggs[_idx(egg_type, len(eggs))]["hatch_name"] if eggs else "?"


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


# --- eggUnlock.csv-driven egg unlock (see data.load_egg_unlock) --------------------
# Each egg gates on the signals the device tracks (generation, album/history,
# X-Antibody, reached stage, felled raids, tournament trophies, previous-generation
# attribute/field, wins, links).  Condition met -> unlocked, period: permanent when
# the row allows (can_perm, via auto_owned), temp for this generation otherwise --
# exactly how the real devices behave.  The licence/price economy was cut 2026-07-17
# ("i never wanted egg licenses"): devices never sold eggs.  The egg SELECT shows
# only hatchable (owned/temp) eggs. persistence.get_progress() supplies the state.


def _conditions_met(rule, prog):
    from . import data
    if rule["gen"] is not None and prog["max_gen"] < rule["gen"]:
        return False
    # tuipet achievement gates (LINES_SPEC §7): the unlock tells the egg's story
    if rule.get("wins") is not None and prog["wins"] < rule["wins"]:
        return False
    if rule.get("album_n") is not None and len(prog["album"]) < rule["album_n"]:
        return False
    if rule.get("mega") is not None and prog.get("mega_kills", 0) < rule["mega"]:
        return False
    # DM20 connection-battle unlocks (Corona/Luna/Meicoo/DORU): distinct
    # tamers linked via a completed lobby bout or jogress
    if rule.get("connections") is not None and prog.get("connections", 0) < rule["connections"]:
        return False
    if rule["stage"] is not None:
        want = data.STAGE_ORDER.index(rule["stage"]) if rule["stage"] in data.STAGE_ORDER else 99
        if prog["max_stage"] < want:
            return False
    if rule["xanti"] and not (prog["last_xanti"] or prog["xanti_ever"]):
        return False
    if rule["tourney"] is not None and rule["tourney"] not in prog["tourneys"]:
        return False
    # MapComplete rows re-gated (BASIC VPET 2026-07-16): adventure left with
    # the world layer, so a row's map index becomes a felled-raid milestone --
    # a map-N row opens after N+1 broken raid bosses (the CSV ran maps 0..4)
    if rule["map"] is not None and prog.get("raids", 0) <= rule["map"]:
        return False
    if rule["history"] and not all(data.canonical_num(n) in prog["album"]
                                   for n in rule["history"]):
        # name-canonical both sides (album/dex audit 2026-07-06): raising
        # ChibiKiwimon as its 1432 hatch-twin satisfies a 944 history gate,
        # exactly like canon's checkNaturalUnlocked name sync
        return False
    if rule["prev_field"] is not None and prog["last_field"] != rule["prev_field"]:
        return False
    if rule["prev_attr"] is not None and prog["last_attr"] != rule["prev_attr"]:
        return False
    # (the prev_elem gate left with the element system (ELEMENT SYSTEM REMOVED 2026-07-18)
    # -- one eggUnlock row carried it; its other gates still judge)
    if rule["obedience"] is not None and prog["last_obed"] < rule["obedience"]:
        return False
    if rule["mood"] is not None and prog["last_mood"] < rule["mood"]:
        return False
    # gates tuipet does not model -> egg stays locked (food/item/habitat used, or
    # the fine-grained per-zone boss slot -- region-boss clears use rule["map"])
    if rule["food"] is not None or rule["item"] is not None or rule["habitat"] is not None:
        return False
    if rule["zone"] is not None:
        return False
    return True


def egg_state(idx, prog, owned):
    """'owned' | 'temp' | 'locked' for one egg index."""
    from . import data
    rule = data.load_egg_unlock().get(idx)
    if rule is None:                    # a bank egg with no rule row: owned-only
        return "owned" if idx in owned else "locked"
    if rule["start"] or idx in owned:
        return "owned"
    if not _conditions_met(rule, prog):
        return "locked"
    return "owned" if rule["can_perm"] else "temp"


def egg_states(prog, owned):
    return {i: egg_state(i, prog, owned) for i in range(count())}


def auto_owned(prog, owned):
    """Eggs that just became permanent (condition met, can_perm) -> caller
    persists them (the device behaviour: an earned egg is earned forever)."""
    from . import data
    rules = data.load_egg_unlock()
    out = []
    for i in range(count()):
        if i in owned:
            continue
        rule = rules.get(i)
        if rule and not rule["start"] and rule["can_perm"] \
                and _conditions_met(rule, prog):
            out.append(i)
    return out


def hatchable_eggs(prog, owned):
    """Eggs ready to hatch right now (owned + temp) -- what the egg select shows."""
    st = egg_states(prog, owned)
    return sorted(i for i, s in st.items() if s in ("owned", "temp"))


def wins_thresholds():
    """Every lifetime-wins gate in the table ({wins_needed}) -- record_battle
    flashes the nursery note the moment a total crosses one."""
    from . import data
    return {r["wins"] for r in data.load_egg_unlock().values()
            if r.get("wins") is not None}


def unlock_progress(idx, prog):
    """A live 'how close am I' line for one LOCKED egg (LINES_SPEC §7) --
    countable gates show numbers ('lifetime wins 37/50'); the rest fall back
    to the rule's description.  '' when there is nothing useful to say."""
    from . import data
    rule = data.load_egg_unlock().get(idx)
    if rule is None:
        return ""
    if rule.get("wins") is not None:
        return f"lifetime wins {min(prog['wins'], rule['wins'])}/{rule['wins']}"
    if rule.get("album_n") is not None:
        # SPECIES, not pets: the album records one entry per STAGE a pet passes,
        # so a single lifetime lodges six of them (egg audit 2026-07-14)
        return f"species recorded {min(len(prog['album']), rule['album_n'])}/{rule['album_n']}"
    if rule.get("mega") is not None:
        return f"Mega-class felled {min(prog.get('mega_kills', 0), rule['mega'])}/{rule['mega']}"
    if rule.get("map") is not None:
        need = rule["map"] + 1                # the raid re-gate (2026-07-16)
        return f"raid bosses felled {min(prog.get('raids', 0), need)}/{need}"
    if rule["gen"] is not None:
        return f"generation {min(prog['max_gen'], rule['gen'])}/{rule['gen']}"
    return rule.get("desc", "")


def unlock_ratio(idx, prog):
    """0..1 progress toward a COUNTABLE gate (wins/album/mega/generation), or
    None when the egg's gate isn't a counter.  Drives the 'next goals' picks."""
    from . import data
    rule = data.load_egg_unlock().get(idx)
    if rule is None:
        return None
    if rule.get("wins") is not None:
        return min(1.0, prog["wins"] / max(1, rule["wins"]))
    if rule.get("album_n") is not None:
        return min(1.0, len(prog["album"]) / max(1, rule["album_n"]))
    if rule.get("mega") is not None:
        return min(1.0, prog.get("mega_kills", 0) / max(1, rule["mega"]))
    if rule.get("map") is not None:
        return min(1.0, prog.get("raids", 0) / (rule["map"] + 1))
    if rule["gen"] is not None:
        return min(1.0, prog["max_gen"] / max(1, rule["gen"]))
    return None


def locked_hint(prog, owned):
    """Shortest 'what unlocks next' hint among locked eggs ('' if none) --
    prefers the gate the player is CLOSEST to (unlock_ratio), so the tease
    is always the next achievable egg, not csv order."""
    from . import data
    rules = data.load_egg_unlock()
    best, best_r = "", -1.0
    for i in range(count()):
        if egg_state(i, prog, owned) != "locked":
            continue
        rule = rules.get(i)
        if not (rule and rule["desc"]):
            continue
        r = unlock_ratio(i, prog)
        r = -0.5 if r is None else r          # counters outrank yes/no gates
        if r > best_r:
            best, best_r = rule["desc"], r
    return best


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
