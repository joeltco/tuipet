"""The adventure world's identity — region / zone / town names + biome theming.

tuipet is its own game now (2026-07-09): the DVPet engine drove a mechanically
rich but ANONYMOUS world — the player saw "Map 1-1", "TOWN 5", "Continent 2".
This layer gives every region, zone and town a real NAME and a biome IDENTITY.

Everything here is DERIVED from the terrain the game already renders, never
invented: each place's biome is read straight from zones.csv BackgroundsAndRange
(the same per-step scenery the backdrop fades through) × towns.csv TownRange ×
habitats.csv.  The NAMES below are authored to match each place's real dominant
biome (see tools/analyze — Cliffside/Ocean/Lake starter = the Coastlands, the
City-dominated second continent = the Ironlands, and so on); the THEMING
(greeting, "known for", specialty stock) is computed at runtime from that
biome's habitats.csv CompatibleField / CompatibleElement.  Nothing is guessed:
change the data and the biomes (and their themes) follow.
"""
from __future__ import annotations
import csv
import os
from functools import lru_cache

_DATA = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# Authored names (biome-derived — each matches its place's real dominant terrain)
# ---------------------------------------------------------------------------
# region per real MapNum: the map's signature biome spread
REGIONS = {
    1: "The Coastlands",   # Cliffside/Ocean/Lake/Underwater — the water-rich starter
    2: "The Ironlands",    # City (MetalEmpire) dominant — the second continent
    3: "The Highlands",    # Canyon/Plains/Sky — high and open
    4: "The Shadowlands",  # Evil Castle/Canyon — dark and fireswept
    5: "The Wildlands",    # every biome in turn — the untamed endgame
}

# zone per (MapNum, ZoneNum): its dominant / entry biome
ZONES = {
    (1, 1): "Cliffside Approach", (1, 2): "Sunken Gorge", (1, 3): "Harbor City",
    (1, 4): "The Tide Deep", (1, 5): "Seabound Forest", (1, 6): "Dock Ward",
    (1, 7): "The Drowned Keep",
    (2, 1): "Rust Plains", (2, 2): "Coldiron Flats", (2, 3): "Foundry Lake",
    (2, 4): "Gearwood", (2, 5): "Voltage Row", (2, 6): "Scrap Bluffs",
    (2, 7): "The Iron Spire",
    (3, 1): "Windmere Plains", (3, 2): "Redrock Gorge", (3, 3): "Skyfall Pass",
    (4, 1): "Ashen Canyon", (4, 2): "The Black Keep",
    (5, 1): "Verdant Field", (5, 2): "Sunscorch Dunes", (5, 3): "Mirrormere",
    (5, 4): "Tanglewood", (5, 5): "Frostreach", (5, 6): "Gloomwood",
    (5, 7): "Nightmare's End",
}

# town per TownID: its biome + a distinguishing epithet
TOWNS = {
    0: "Gloamgate", 1: "Emberfall", 2: "Steelport", 3: "Coral Deep",
    4: "Greenhollow", 5: "Voltway", 6: "Dusk Hold", 7: "Windmere",
    8: "Stillwater", 9: "Mirror Bay", 10: "Mossford", 11: "Gearworks",
    12: "Circuit Row", 13: "Neon Junction", 14: "Grassreach", 15: "Redrock",
    16: "Cloudpost", 17: "Cinderpass", 18: "Nightmarket", 19: "Meadowgate",
    20: "Dunehaven", 21: "Reedhaven", 22: "Fernwood", 23: "Frostmere",
    24: "Magmarest", 25: "Shadowspire",
}

# ---------------------------------------------------------------------------
# Biome derivation — the terrain of the zone AROUND each town (towns carry
# TownBackgroundID 13/"Town" in their own record, so their identifying biome is
# the zone habitat at their step; the exact derivation the themed egg shop uses)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _habitats():
    out = {}
    for r in csv.DictReader(open(os.path.join(_DATA, "habitats.csv"))):
        try:
            hid = int(r["ID"])
        except (KeyError, ValueError):
            continue
        out[hid] = {
            "name": (r.get("Name") or "?").strip(),
            "field": (r.get("CompatibleField") or "").split(";")[0].strip(),
            "elem": (r.get("CompatibleElement") or "").split(";")[0].strip(),
        }
    return out


@lru_cache(maxsize=1)
def _town_biome():
    """TownID -> habitat id, read from the zone habitat band at the town's step."""
    span = {}
    for r in csv.DictReader(open(os.path.join(_DATA, "towns.csv"))):
        rng = (r.get("TownRange") or "").split("t")
        if len(rng) == 2 and rng[0].strip().isdigit() and rng[1].strip().isdigit():
            try:
                span[int(r["TownID"])] = (int(rng[0]), int(rng[1]))
            except (KeyError, ValueError):
                pass
    out = {}
    for z in csv.DictReader(open(os.path.join(_DATA, "zones.csv"))):
        tid = (z.get("TownID;") or z.get("TownID") or "").strip()
        if not tid.isdigit():
            continue
        tid = int(tid)
        bands = []
        for seg in (z.get("BackgroundsAndRange") or "").split(";"):
            rng, _, hid = seg.partition(":")
            a, _, b = rng.partition("t")
            if a.strip().isdigit() and b.strip().isdigit() and hid.strip().isdigit():
                bands.append((int(a), int(b), int(hid)))
        sp = span.get(tid)
        if not (sp and bands):
            continue
        mid = (sp[0] + sp[1]) // 2
        hid = next((h for a, b, h in bands if a <= mid <= b),
                   max(bands, key=lambda s: s[1] - s[0])[2])
        out[tid] = hid
    return out


def town_biome_name(tid: int) -> str:
    """The habitat name that identifies this town (e.g. 'Desert', 'City')."""
    return _habitats().get(_town_biome().get(tid), {}).get("name", "Town")


# ---------------------------------------------------------------------------
# Biome theming — greeting, "known for", and specialty shop stock per biome.
# Keyed by habitat NAME; stock lists are GENERAL consumables (foods.csv/items.csv
# ids), deliberately NOT evolution/spirit items, so a themed shelf never warps
# the evolution economy.  {field}/{element} words come from the habitat row.
# ---------------------------------------------------------------------------
BIOME = {
    "Evil Castle": {
        "greet": "Lantern-light gutters over {name}'s grim stalls.",
        "foods": [30, 4, 19], "items": [80, 2],
    },
    "Canyon": {
        "greet": "Heat shimmers off the red rock around {name}.",
        "foods": [37, 8, 0], "items": [7, 3],
    },
    "Volcano": {
        "greet": "Ash drifts through the forge-town of {name}.",
        "foods": [37, 8, 0], "items": [7],
    },
    "City": {
        "greet": "Neon and gear-hum fill the streets of {name}.",
        "foods": [6, 7, 54], "items": [8, 9, 10, 11],
    },
    "Underwater": {
        "greet": "{name} glimmers in the light filtering down through the water.",
        "foods": [1, 14, 53], "items": [3],
    },
    "Ocean": {
        "greet": "Salt wind and gulls sweep the docks of {name}.",
        "foods": [1, 14, 53], "items": [3],
    },
    "Lake": {
        "greet": "Still water mirrors the sky beside {name}.",
        "foods": [1, 14, 47], "items": [3],
    },
    "Forest": {
        "greet": "Dappled light falls through the leaves over {name}.",
        "foods": [45, 13, 2], "items": [4],
    },
    "Plains": {
        "greet": "Open sky stretches wide above {name}.",
        "foods": [3, 29, 46], "items": [3],
    },
    "Field": {
        "greet": "Wildflowers ring the little market of {name}.",
        "foods": [3, 50, 42], "items": [3],
    },
    "Sky": {
        "greet": "Wind and cloud stream past high {name}.",
        "foods": [9, 2, 31], "items": [12, 6],
    },
    "Cliffside": {
        "greet": "Sea-spray and wind buffet the bluffs of {name}.",
        "foods": [1, 9, 2], "items": [6],
    },
    "Desert": {
        "greet": "The sun beats down hard on {name}'s market.",
        "foods": [39, 42, 50], "items": [4],
    },
    "Tundra": {
        "greet": "Frost rimes the shuttered stalls of {name}.",
        "foods": [39, 31, 40], "items": [4],
    },
}

# field -> the short "known for" tag (matches the biome's evolution flavor)
_FIELD_WORD = {
    "NightmareSoldier": "shadow", "DarkArea": "dark", "DragonsRoar": "fire",
    "MetalEmpire": "metal", "DeepSaver": "water", "DeepSavers": "water",
    "JungleTrooper": "wood", "NatureSpirit": "earth", "WindGuardian": "wind",
    "VirusBuster": "light",
}


def _biome_theme(tid: int):
    return BIOME.get(town_biome_name(tid), BIOME["Plains"])


def region_name(map_num: int) -> str:
    return REGIONS.get(map_num, f"Region {map_num}")


def zone_name(map_num: int, zone_num: int) -> str:
    return ZONES.get((map_num, zone_num), f"Zone {zone_num}")


def town_name(tid: int) -> str:
    return TOWNS.get(tid, f"Town {tid}")


def town_greeting(tid: int) -> str:
    """The town's own welcome line, flavored by its biome."""
    return _biome_theme(tid)["greet"].format(name=town_name(tid))


def town_known_for(tid: int) -> str:
    """A one-line 'the town is known for…' tag: its biome + signature eggs."""
    hid = _town_biome().get(tid)
    h = _habitats().get(hid, {})
    field = _FIELD_WORD.get(h.get("field", ""), (h.get("elem") or "wild").lower())
    return f"{h.get('name', 'Town')} town — {field}-field goods & eggs"


def town_field(tid: int) -> str:
    """The town biome's signature CompatibleField (e.g. 'DeepSaver') -- the
    field whose championship the town hosts and whose mons pack its cups."""
    return _habitats().get(_town_biome().get(tid), {}).get("field", "")


def biome_specialty_keys(tid: int, is_food: bool):
    """The town's signature local stock as consumable keys ('f:39' / 'i:8') —
    biome-fitting GENERAL goods it always carries.  Deduped, order preserved."""
    ids = _biome_theme(tid)["foods" if is_food else "items"]
    pre = "f:" if is_food else "i:"
    seen, out = set(), []
    for i in ids:
        k = f"{pre}{i}"
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out
