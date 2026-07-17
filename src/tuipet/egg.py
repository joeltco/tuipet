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
    fr = eggs[egg_type % len(eggs)]["frames"]        # real frames: idle / settle / crack
    f0 = fr[0]
    f1 = fr[1] if len(fr) > 1 else f0
    f2 = fr[2] if len(fr) > 2 else f1                 # the REAL crack frame (was discarded)
    return [f0, f1, f2]

ROLES = {"idle": [0, 1], "egg_idle": [0, 1], "hatch": [0, 1, 2]}  # frames: egg -> crack -> baby


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
# attribute/element/field). Condition met + price 0 -> auto-unlocked (free to hatch,
# or temp for this generation); condition met + price > 0 -> BUYABLE in the egg shop
# (shopscreen Eggs tab) and bought eggs are owned permanently. The egg SELECT shows
# only hatchable (owned/temp) eggs. persistence.get_progress() supplies the state.
_WIN_EGGS = {41: 50, 42: 100}      # tuipet-only "???" eggs (not in eggUnlock.csv) -> lifetime wins


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
    if rule["prev_elem"] is not None and prog["last_elem"] != rule["prev_elem"]:
        return False
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
    """('owned'|'buyable'|'temp'|'locked', price) for one egg index."""
    from . import data
    rule = data.load_egg_unlock().get(idx)
    if rule is None:                    # the "???" mystery eggs: lifetime-win gates
        if idx in owned:                # (the old album-size fallback pool is gone --
            return ("owned", 0)         # it was opaque, and every egg now has a rule)
        need = _WIN_EGGS.get(idx)
        if need is not None:
            return ("owned", 0) if prog["wins"] >= need else ("locked", 0)
        return ("locked", 0)
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


def win_eggs():
    """The tuipet-only mystery eggs and their lifetime-win gates ({idx: wins})."""
    return dict(_WIN_EGGS)


def unlock_progress(idx, prog):
    """A live 'how close am I' line for one LOCKED egg (LINES_SPEC §7) --
    countable gates show numbers ('lifetime wins 37/50'); the rest fall back
    to the rule's description.  '' when there is nothing useful to say."""
    from . import data
    rule = data.load_egg_unlock().get(idx)
    if rule is None:
        need = _WIN_EGGS.get(idx)
        if need is not None:
            return f"lifetime wins {min(prog['wins'], need)}/{need}"
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
        need = _WIN_EGGS.get(idx)
        return min(1.0, prog["wins"] / need) if need else None
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
    """Shortest 'what unlocks next' hint among locked eggs ('' if none)."""
    from . import data
    rules = data.load_egg_unlock()
    for i in range(count()):
        s, _ = egg_state(i, prog, owned)
        if s == "locked" and rules.get(i) and rules[i]["desc"]:
            return rules[i]["desc"]
    for i, need in sorted(_WIN_EGGS.items(), key=lambda kv: kv[1]):
        if egg_state(i, prog, owned)[0] == "locked":
            return f"a mystery egg at {need} lifetime wins ({prog['wins']}/{need})"
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


# --- themed TOWN egg shops: spread the buyable roster across the world by habitat ---


def _store_of(idx):
    """Which storefront sells this egg -- "home"/"town" both mean the home
    shop now (the towns left with the world layer; BASIC VPET 2026-07-16)."""
    from . import data
    return (data.load_egg_unlock().get(idx) or {}).get("store", "")


def _chaseable(rule):
    """A locked egg whose gate the player can actually work toward -- a real
    description, and nothing gated on a signal tuipet doesn't model."""
    return bool(rule and rule["desc"]
                and rule["food"] is None and rule["item"] is None
                and rule["habitat"] is None and rule["zone"] is None)


def home_eggs(prog, owned):
    """(idx, price) buyable eggs sold at the HOME shop -- the common storefront."""
    return [(i, p) for i, p in buyable_eggs(prog, owned)
            if _store_of(i) in ("home", "town")]



def locked_home_eggs(prog, owned, cap=6):
    """(idx, hint) for LOCKED home-shop eggs the player can chase -- the home
    egg tab's goal board."""
    from . import data
    rules = data.load_egg_unlock()
    out = []
    for i, (state, _) in sorted(egg_states(prog, owned).items()):
        if state == "locked" and _store_of(i) in ("home", "town") \
                and _chaseable(rules.get(i)):
            out.append((i, rules[i]["desc"]))
            if len(out) >= cap:
                break
    return out



def locked_shop_entry(idx, hint):
    """A shelf row for a locked egg: shows as ??? with its unlock hint."""
    return {"key": "eggl:%d" % idx, "name": "???", "price": 0,
            "egg_idx": idx, "locked": True, "hint": hint}
