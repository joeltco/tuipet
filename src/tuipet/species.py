"""Authentic DM20 species database — the canon roster the game is rebuilt on.

Loads the bundled corpus DB (`data/dm20.json.gz`, mined from humulos per-version
guides) and exposes the roster, stage order, real-time stage timers, the attribute
triangle, and per-mon evolution conditions. This REPLACES DVPet's `digimon.csv` /
`evolutions.csv` (see AUTHENTIC_REBUILD.md). One record per Digimon:

    {id, num, name, stage, level, attribute, alt_attribute, sleep, power,
     sprite, sprite_source, evolves_to: [{to, to_id, raw, parsed}]}

`num` is a stable index assigned here (roster order) so the rest of the engine can
keep keying pets by an int while the data underneath is authentic.
"""
from __future__ import annotations
import gzip
import json
import os
from functools import lru_cache

_HERE = os.path.dirname(__file__)
_DB = os.path.join(_HERE, "data", "dm20.json.gz")

DEVICE = "dm20"

# Backgrounds go by DEVICE (and, for the Pendulum line, by FIELD) — like a real unit's
# fixed faceplate, not a switchable habitat. Keys index data/backgrounds.json.gz.
DEVICE_BG = {
    "dm20": "egg1Back",      # Plains — the original line has no field themes
}
# Pen20 (and other field devices): the backdrop follows the field/version you hatched —
# the Pendulum's six fields. Ready for the Pen20 build; unused by DM20.
FIELD_BG = {
    "NatureSpirit":    "egg3Back",   # Forest
    "DeepSaver":       "egg5Back",   # Ocean
    "NightmareSoldier": "egg8Back",  # Evil Castle
    "WindGuardian":    "egg0Back",   # Sky
    "MetalEmpire":     "egg10Back",  # City
    "VirusBuster":     "egg9Back",   # Field
}


def background_key(field=None):
    """The background-file key for the current device — by field for Pendulum-line
    devices, else the device's fixed backdrop (DM20 = Plains)."""
    if field and field in FIELD_BG:
        return FIELD_BG[field]
    return DEVICE_BG.get(DEVICE, "egg1Back")

# DVPet native sprite-strip frame order (11 frames, index 0-10), VERIFIED against
# DVPet View/SpriteAnim drawNum() args. The art atlas, anim.py, and the pose constants
# all index this order:
#   0 idle/neutral     6 attack / cheer-up
#   1 idle-B / walk-B  7 eat-chew / cheer-down(big) / wake-end
#   2 sleep            8 eat-swallow
#   3 stretch / yawn   9 dejected / fail / disliked
#   4 cheer-down       10 collapse / dying / exhausted
#   5 excited / cheer-up(big)
FRAME_NAMES = ["idle", "idle_b", "sleep", "stretch", "cheer_down", "excited",
               "attack", "eat_chew", "eat_swallow", "dejected", "collapse"]

# Animation role -> DVPet frame indices, taken from the real DVPet animations:
#   Cheering=5,7  Jeering=9,10  Eating=8,7  attackDefault=6,0  Cleaning=0,4  Bounce=1,5  Dying=10.
ROLES = {
    "idle":   [0, 1],      # Idling / Discovering walk
    "walk":   [0, 1],
    "sleep":  [2, 3],      # idleSleep
    "happy":  [5, 7],      # Cheering up=5 down=7 — praise / win / evolve bounce
    "angry":  [9, 10],     # Jeering up=9 down=10 (scold)
    "eat":    [8, 7],      # eat(): open-mouth 8 -> chew 7
    "refuse": [4],         # refuse(): frame 4 shaken by the mirror toggle
    "attack": [6, 0],      # attackDefault: strike 6 -> reset 0
    "tantrum": [9, 10],    # unhappy-idle -> jeer poses
    "poop":   [4, 5],      # poop(): squat 4 -> sit 5
    "play":   [1, 5],      # Bounce/Jump toy interact: 1 -> 5
    "wash":   [0, 4],      # Cleaning/Bathe: scrub 0 -> refreshed 4
    "heal":   [7, 8],      # recover(): eat-medicine, same as eat
    "sad":    [9],         # dejected/fail pose
    "tired":  [9],         # disliked/weary pose
    "exhausted": [10],     # collapse pose (Dying)
    "yawn":   [0, 8],      # yawning(): idle 0 -> open-mouth 8
    "wake":   [2, 3, 1],   # wakeUp(): groggy 2/3 -> settle 1
    "surprise": [1, 5],    # startle beats 1,5
}
MIRROR_ROLES = {"refuse"}

# Authentic mono-vpet growth order (Japanese vpet stage names, not the anime tiers).
STAGE_ORDER = ["Baby I", "Baby II", "Child", "Adult", "Perfect", "Ultimate", "Super Ultimate"]
STAGE_RANK = ["Egg"] + STAGE_ORDER

# Attribute triangle: Vaccine > Virus > Data > Vaccine; Free is neutral (no edge).
ATTRIBUTES = ["Vaccine", "Virus", "Data", "Free"]
_BEATS = {"Vaccine": "Virus", "Virus": "Data", "Data": "Vaccine"}


def _timer_seconds(s):
    """'10 min' / '6 h' / '36 h' -> seconds. None/unknown -> None."""
    if not s:
        return None
    parts = s.split()
    try:
        n = float(parts[0])
    except (ValueError, IndexError):
        return None
    unit = parts[1].lower() if len(parts) > 1 else "s"
    return int(n * {"min": 60, "m": 60, "h": 3600, "hr": 3600, "hour": 3600,
                    "hours": 3600, "s": 1, "sec": 1}.get(unit, 1))


@lru_cache(maxsize=1)
def _load():
    with gzip.open(_DB, "rt", encoding="utf-8") as fh:
        raw = json.load(fh)
    meta = raw["_meta"]
    timers = {st: _timer_seconds(t) for st, t in meta.get("stage_timers", {}).items()}
    recs = []
    for i, r in enumerate(raw["digimon"]):
        dev = (r.get("devices", {}) or {}).get(DEVICE, {}) or {}
        recs.append({
            "id": r["id"],
            "num": i,
            "name": r["name"],
            "stage": r["stage"],
            "level": r.get("level"),
            "attribute": r.get("attribute"),
            "alt_attribute": r.get("alt_attribute"),
            "sleep": r.get("sleep"),
            "power": int(r["power"]) if str(r.get("power") or "").isdigit() else None,
            "sprite": r.get("sprite"),
            "sprite_source": r.get("sprite_source"),
            "versions": dev.get("versions") or [],
            "evolves_to": dev.get("evolves_to") or [],
            "stage_time": timers.get(r["stage"]),
        })
    by_num = {r["num"]: r for r in recs}
    by_id = {r["id"]: r for r in recs}
    by_name = {r["name"].lower(): r for r in recs}
    return {"records": recs, "by_num": by_num, "by_id": by_id,
            "by_name": by_name, "timers": timers, "meta": meta}


def roster():
    return _load()["records"]


def get(num):
    return _load()["by_num"].get(num)


def by_id(mon_id):
    return _load()["by_id"].get(mon_id)


def by_name(name):
    return _load()["by_name"].get((name or "").lower())


def stage_time(stage):
    """Real-time seconds a Digimon spends in `stage` before it can evolve."""
    return _load()["timers"].get(stage)


def stage_rank(stage):
    try:
        return STAGE_RANK.index(stage)
    except ValueError:
        return len(STAGE_RANK)


def evolutions(num):
    """List of {to, to_id, raw, parsed} evolution edges for a Digimon (by num)."""
    r = get(num)
    return r["evolves_to"] if r else []


def babies():
    """Baby I roster (hatch candidates) in roster order."""
    return [r for r in roster() if r["stage"] == "Baby I"]
