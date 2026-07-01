"""Load game data. Roster / sprites / stages / evolution graph now come from the
authentic DM20 corpus via `species` + `data/dm20_sprites.json.gz` (DVPet 16x16 art in
native DVPet frame order). The remaining DVPet CSVs (foods/enemies/care) are still read here until those
subsystems are rebuilt."""
from __future__ import annotations
import csv
import gzip
import json
import os
import re
from functools import lru_cache
from . import species

_HERE = os.path.dirname(__file__)
_DATA = os.path.join(_HERE, "data")
_RAW = _DATA  # bundled CSVs (foods/enemies/care) live alongside sprites
_ATLAS = os.path.join(_DATA, "dm20_sprites.json.gz")

# Animation roles + growth order now come from the authentic DM20 atlas (DVPet-native
# frame order). See species.ROLES / species.STAGE_ORDER.
ROLES = species.ROLES
MIRROR_ROLES = species.MIRROR_ROLES
STAGE_ORDER = species.STAGE_ORDER        # Baby I .. Super Ultimate (authentic, not anime tiers)
STAGE_RANK = species.STAGE_RANK          # ["Egg"] + STAGE_ORDER


def stage_rank(stage):
    return species.stage_rank(stage)


def pretty_field(name):
    """Display form of a CamelCase Field value (the data keeps it joined for
    matching): 'NightmareSoldier' -> 'Nightmare Soldier'. 'None'/single words
    are unchanged."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name or "")


PLACEHOLDER_NUMS: set[int] = set()


@lru_cache(maxsize=1)
def load_sprites():
    """The authentic DM20 sprite atlas (DVPet 16x16 art, native frame order), keyed by species num."""
    from . import placeholder
    with gzip.open(_ATLAS, "rt", encoding="utf-8") as fh:
        data = json.load(fh)["sprites"]
    for rec in data:
        frames = rec["frames"]
        first = next((f for f in frames if f), None)
        if first is None:                       # no sprite extracted (the 6 unsourceable mons)
            PLACEHOLDER_NUMS.add(rec["num"])
            rec["frames"], rec["w"], rec["h"] = placeholder.FRAMES, placeholder.W, placeholder.H
            rec["_placeholder"] = True
        else:
            # fill any empty role frame with the first real one so nothing renders blank
            rec["frames"] = [f if f else first for f in frames]
    by_num = {d["num"]: d for d in data}
    return data, by_num


def is_placeholder(num):
    load_sprites()
    return num in PLACEHOLDER_NUMS


@lru_cache(maxsize=1)
def load_evolutions():
    """num -> list of target nums it can evolve into (from the species evolution graph)."""
    by_id = {r["id"]: r["num"] for r in species.roster()}
    evo = {}
    for r in species.roster():
        targets = [by_id[e["to_id"]] for e in r["evolves_to"]
                   if e.get("to_id") in by_id]
        if targets:
            evo[r["num"]] = targets
    return evo


@lru_cache(maxsize=1)
def load_foods():
    """DM20's two foods: Meat (fills a hunger heart) and Protein (fills a strength
    heart, adds weight, restores DP). No taste/nutrient columns (all DVPet)."""
    path = os.path.join(_RAW, "foods.csv")
    foods = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            try:
                foods.append({
                    "name": row["Name"],
                    "hunger": int(row.get("Hunger") or 0),
                    "strength": int(row.get("Strength") or 0),
                    "weight": int(row.get("Weight") or 0),
                })
            except (KeyError, ValueError):
                continue
    return foods


def next_stage(stage):
    try:
        i = STAGE_ORDER.index(stage)
    except ValueError:
        return None
    return STAGE_ORDER[i + 1] if i + 1 < len(STAGE_ORDER) else None


@lru_cache(maxsize=1)
def load_requirements():
    """Per-mon evolution/physiology gates were DVPet digimon.csv data (keyed by DVPet
    nums, absent for the authentic species roster). The engine now reads everything
    from `species` + the corpus, so this is an empty map — every `.get(num, {})` caller
    falls back to its sensible default. (digimon.csv is gone.)"""
    return {}


@lru_cache(maxsize=1)
def load_backgrounds():
    """Background scenes (per time-of-day frame: day/night) keyed by file name."""
    path = os.path.join(_DATA, "backgrounds.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


@lru_cache(maxsize=1)
def load_effects():
    """Auxiliary effect overlays (poop/zzz/frozen/wash/emotes) keyed by name."""
    path = os.path.join(_DATA, "effects.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


@lru_cache(maxsize=1)
def load_icons():
    """Food/item icons (frame 0) keyed f:<id> / i:<id>, or empty if not extracted."""
    path = os.path.join(_DATA, "icons.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}



