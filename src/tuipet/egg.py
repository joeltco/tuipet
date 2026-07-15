"""Egg sprites + the hatch table (the colour-atlas era, 2026-07-15).

Every egg is a real Digitama entry in the mon atlas: two idle shells and a
crack frame, colour, 16x16.  The old unlock economy (license gates, egg
shops, town shelves) is retired -- the full digitama shelf is open; the
hatch table says what each shell births.  The side-to-side shake stays an
xshift at render time.  No drawn art.
"""
from __future__ import annotations
from functools import lru_cache


@lru_cache(maxsize=1)
def _eggs():
    """[(egg_path, egg_record, baby_path)] in stable sorted-path order --
    egg_type is an index into THIS list."""
    from . import data
    hatch = data.load_hatch()
    _, by_num = data.load_sprites()
    byp = data.num_by_path()
    out = []
    for egg_path in sorted(hatch):
        rec = by_num.get(byp.get(egg_path))
        if rec is not None:
            out.append((egg_path, rec, hatch[egg_path]))
    return out


def frames(egg_type=0):
    """[idle shell, settle shell, cracked-open] for one egg -- straight from
    the atlas' egg/hatch anims (colour rows)."""
    eggs = _eggs()
    if not eggs:
        return [["0"]]
    from . import data
    rec = data.record_for(eggs[egg_type % len(eggs)][1]["num"])
    anims, pal = rec["anims"], rec["pal"]
    egg = anims.get("egg") or []
    hatch = anims.get("hatch") or []
    fr = [data._decode_frame(f, pal) for f in (egg + hatch)]
    if not fr:
        return [["0"]]
    while len(fr) < 3:
        fr.append(fr[-1])
    return fr[:3]


ROLES = {"idle": [0, 1], "egg_idle": [0, 1], "hatch": [0, 1, 2]}  # egg -> crack -> baby


def egg_name(egg_type=0):
    eggs = _eggs()
    return eggs[egg_type % len(eggs)][1]["name"] if eggs else "?"


def hatch_target(egg_type=0):
    """The Baby I num this egg hatches into (the hatch table is 1:1)."""
    from . import data
    eggs = _eggs()
    if not eggs:
        return None
    return data.num_by_path().get(eggs[egg_type % len(eggs)][2])


def hatch_targets(egg_type=0):
    t = hatch_target(egg_type)
    return [t] if t is not None else []


def hatch_name(egg_type=0):
    from . import data
    t = hatch_target(egg_type)
    return data.record_for(t)["name"] if t is not None else "?"


def count():
    return len(_eggs()) or 1


def record(egg_type=0):
    fr = frames(egg_type)
    w = max(len(r) for r in fr[0])
    return {"num": -1, "name": egg_name(egg_type), "stage": "Egg",
            "attribute": "Free", "w": w, "h": len(fr[0]), "frames": fr}


# --- the retired unlock economy: the whole shelf is open now.  The API
# survives so the egg screens keep their shape (audit: eggselect/shop/town
# all read through these). ---

def egg_state(idx, prog, owned):
    return ("owned", 0)


def egg_states(prog, owned):
    return {i: ("owned", 0) for i in range(count())}


def auto_owned(prog, owned):
    return []


def selectable_eggs(prog, owned):
    return list(range(count()))


def hatchable_eggs(prog, owned):
    return list(range(count()))


def buyable_eggs(prog, owned):
    return []


def shop_egg_entry(idx, price):
    return {"key": "egg:%d" % idx, "name": hatch_name(idx), "price": int(price),
            "egg_idx": idx}


def win_eggs():
    return {}


def unlock_progress(idx, prog):
    return ""


def unlock_ratio(idx, prog):
    return None


def locked_hint(prog, owned):
    return ""


def home_eggs(prog, owned):
    return []


def eggs_for_town(town_id, prog, owned):
    return []


def locked_home_eggs(prog, owned, cap=6):
    return []


def locked_town_eggs(town_id, prog, owned, cap=6):
    return []


def locked_shop_entry(idx, hint):
    return {"key": "eggl:%d" % idx, "name": "???", "price": 0,
            "egg_idx": idx, "locked": True, "hint": hint}


def __getattr__(name):
    # back-compat: a few callers read egg.FRAMES / egg.W / egg.H at import
    # time; computing them eagerly would decode the atlas on import
    if name == "FRAMES":
        return frames(0)
    if name == "W":
        return max(len(r) for r in frames(0)[0])
    if name == "H":
        return len(frames(0)[0])
    raise AttributeError(name)
