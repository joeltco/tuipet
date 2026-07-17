"""The DSprite background catalog, wired to the eggs (BASIC VPET 2026-07-16).

Habitats are gone (Joel: "remove the habitats. wire in the dsprite
backgrounds") -- the scene behind the mon is decided by the EGG it hatched
from and stands for the pet's whole life, exactly like the real device's
per-version backgrounds (the old egg0Back..egg11Back sheets this system
replaces).  The art is the DSprite rebuild's rip set (Joel-approved source
2026-07-15), one look per scene: no time-of-day sheets -- day/night lives
on in the clock, the HUD sky glyph and the arena's own 5-frame sheet.

The egg->scene wiring is derived, not invented: each egg's hatch line maps
through its members' natural habitats (digimon.csv Habitat, the same table
the habitat system read) onto the DSprite rebuild's own biome->scene map;
lines with no habitat data fall back to their dominant FIELD.  A handful of
flavor overrides are marked inline.
"""

DEFAULT = "greenhills"          # the DM20 background rip; also the fallback

# key -> display name (the clone catalog + the off-catalog data scenes)
NAMES = {
    "greenhills":   "Green Hills",
    "desert":       "Desert",
    "lakeside":     "Lakeside",
    "mountains":    "Mountains",
    "cove":         "Cove",
    "forestgate":   "Forest Gate",
    "flowerfield":  "Flower Field",
    "blossom":      "Blossom Field",
    "goldenwood":   "Golden Wood",
    "tealhollow":   "Teal Hollow",
    "moonmeadow":   "Moonlit Meadow",
    "underwater":   "Underwater",
    "volcano":      "Volcano",
    "baybridge":    "Bay Bridge",
    "bridgenight":  "Bridge Night",
    "datatunnel":   "Data Tunnel",
    "frozenpeak":   "Frozen Peak",
    "city": "City", "cityday": "White City", "citysunset": "City Sunset",
    "boulevard": "Boulevard", "boulevardusk": "Boulevard Dusk",
    "factory": "Factory", "factorynight": "Factory Night",
    "fileisland": "Lone Island", "islandsea": "Island Sea",
    "islandnight": "Island Night", "jungle": "Jungle",
    "seafloor": "Seafloor", "sunsetshore": "Sunset Shore",
    "tourneyBack": "Arena",
}

# egg index -> scene.  Derivation key: (h) = the line's natural habitat via
# the rebuild's biome map, (f) = dominant-field fallback, (*) = flavor
# override, reasoned inline.
EGG_BG = {
    0: "greenhills",     # Botamon / ver1 (h: Plains)
    1: "mountains",      # Punimon / ver2 (h: Canyon)
    2: "forestgate",     # Poyomon / ver3 (h: Forest)
    3: "cove",           # Yuramon / ver4 (h: Cliffside)
    4: "islandsea",      # Zurumon / ver5 (h: Ocean)
    5: "datatunnel",     # Kuramon (h: Hard Disk -- the Diablomon net)
    6: "greenhills",     # Chibickmon (h: Plains)
    7: "islandsea",      # Tsubumon (h: Ocean)
    8: "flowerfield",    # Pururumon (h: Field)
    9: "lakeside",      # Dodomon / verX (h: Lake)
    10: "frozenpeak",    # Puttimon (h: Sky -- the cloud sea)
    11: "factorynight",  # Kiimon (h: Evil Castle -- dark iron)
    12: "datatunnel",    # Dokimon (h: Hard Disk)
    13: "underwater",    # Chibomon (f: DeepSaver / Water)
    14: "cove",          # Ketomon (h: Cliffside)
    15: "forestgate",    # Leafmon (h: Forest)
    16: "volcano",       # Petitmon (f: DragonsRoar / Fire)
    17: "city",          # Sakumon (h: City)
    18: "underwater",    # Zerimon (f: DeepSaver / Water)
    19: "moonmeadow",    # Cocomon (f: NightmareSoldier)
    20: "frozenpeak",    # Fufumon (h: Sky)
    21: "city",          # Cotsucomon (h: City)
    22: "datatunnel",    # Algomon I (f: DarkArea; * the net algae lives IN the net)
    23: "greenhills",    # Nature Spirits Egg (f: NatureSpirit)
    24: "underwater",    # Deep Savers Egg (h: Underwater)
    25: "moonmeadow",    # Nightmare Soldiers Egg (f: NightmareSoldier)
    26: "flowerfield",   # Wind Guardians Egg (h: Field)
    27: "factory",       # Metal Empire Egg (* the Empire lives in the factory;
                         #   freed when its old wearer left with the fake-egg cut)
    28: "goldenwood",    # Virus Busters Egg (f: VirusBuster / Light)
    29: "volcano",       # Corona Egg (* the sun egg burns, whatever the csv says)
    30: "moonmeadow",    # Luna Egg (* the moon egg gets the moonlit meadow)
    31: "city",          # Zuba Egg (h: City)
    32: "city",          # Hack Egg (h: City)
    33: "blossom",       # Meicoo Egg / verE (f: NatureSpirit / Light)
    34: "lakeside",      # DORU Egg (h: Lake)
    35: "volcano",       # Slayerdra Egg (f: DragonsRoar / Fire)
    36: "mountains",     # Breakdra Egg (f: DragonsRoar / Earth -- the drill)
    37: "frozenpeak",    # Ryuda Egg (h: Sky)
    38: "volcano",       # Draco Egg (f: DragonsRoar / Fire)
    39: "flowerfield",   # Lalamon Egg (h: Field)
    40: "baybridge",     # Terrier Egg (* Willis's twin: the movie's Golden Gate)
    41: "bridgenight",   # Lop Egg (* the dark twin gets the bridge at night)
    42: "frozenpeak",    # V Egg (f: WindGuardian -- the cloud sea)
    43: "greenhills",    # Virus Busters Ver. 20th Egg (h: Plains)
    44: "cityday",       # Digitama X3 (* the Royal Knights' white city)
    45: "datatunnel",    # Kera Digitama (h: Hard Disk)
}


# the E picker's shelf (restored 2026-07-17: "add the e action back"): every
# named scene except the arena is a FREE pick, the clone's final ruling
# ("get rid of the price walls" -- Joel 2026-07-16).  The egg still decides
# the DEFAULT scene; a pick merely overrides it (pet.bg_pick).
PICKS = tuple(sorted((k for k in NAMES if k != "tourneyBack"),
                     key=lambda k: NAMES[k]))


def scene_for_egg(egg_type):
    """The scene an egg wires its whole line to (unknown egg -> DEFAULT)."""
    try:
        return EGG_BG.get(int(egg_type), DEFAULT)
    except (TypeError, ValueError):
        return DEFAULT


def name(key):
    return NAMES.get(key, key)
