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

# Wayland native sprite-sheet frame order (include/graphics/sprite_sheet.h):
FRAME_NAMES = ["idle_1", "idle_2", "angry", "down", "happy", "eat_1", "sleep",
               "refuse", "sad", "lose_1", "eat_2", "lose_2", "attack_1",
               "movement_1", "movement_2", "attack_2"]

# Animation role -> wayland frame indices. Anchored on frames 0-8 (present in every
# multi-frame sheet); indices >=9 fall back to frame 0 on shorter sheets, and the 20
# dvpet-fallback mons (frame 0 only) render their idle pose for every role. This is the
# wayland-native rebuild of the old DVPet-ordered data.ROLES.
ROLES = {
    "idle":      [0, 1],   # idle_1 / idle_2 toggle (also the walk shuffle)
    "walk":      [0, 1],
    "angry":     [2],
    "tantrum":   [2],
    "down":      [3],
    "exhausted": [3],      # collapse / dying
    "poop":      [3],
    "happy":     [4],      # cheer / praise / win / evolve bounce (hop comes from yshift)
    "play":      [4],
    "eat":       [5, 10],  # eat_1 -> eat_2 chew (eat_2 falls back to idle on 9-frame sheets)
    "heal":      [5, 10],  # eat medicine = same chew
    "sleep":     [6],
    "wake":      [6, 0],   # sleep -> idle
    "refuse":    [7],
    "wash":      [0],
    "sad":       [8],
    "tired":     [8],
    "yawn":      [0, 6],   # idle -> sleep-ish
    "surprise":  [2, 4],
    "lose":      [9, 11],  # lose_1 / lose_2
    "attack":    [12, 15], # attack_1 / attack_2 (fall back to idle when absent)
}
MIRROR_ROLES = {"refuse"}

# Authentic mono-vpet growth order (Japanese vpet stage names, not the anime tiers).
STAGE_ORDER = ["Baby I", "Baby II", "Child", "Adult", "Perfect", "Ultimate", "Super Ultimate"]
STAGE_RANK = ["Egg"] + STAGE_ORDER

# Attribute triangle: Vaccine > Virus > Data > Vaccine; Free is neutral (no edge).
ATTRIBUTES = ["Vaccine", "Virus", "Data", "Free"]
_BEATS = {"Vaccine": "Virus", "Virus": "Data", "Data": "Vaccine"}


def attribute_edge(a, b):
    """+1 if attribute `a` beats `b`, -1 if it loses, 0 if neutral/even (Free or same)."""
    if _BEATS.get(a) == b:
        return 1
    if _BEATS.get(b) == a:
        return -1
    return 0


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
