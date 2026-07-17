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
    5: "lakeside",       # Babumon (h: Lake)
    6: "datatunnel",     # Kuramon (h: Hard Disk -- the Diablomon net)
    7: "greenhills",     # Chibickmon (h: Plains)
    8: "islandsea",      # Tsubumon (h: Ocean)
    9: "flowerfield",    # Pururumon (h: Field)
    10: "greenhills",    # Jyarimon (h: Plains)
    11: "lakeside",      # Dodomon / verX (h: Lake)
    12: "frozenpeak",    # Puttimon (h: Sky -- the cloud sea)
    13: "factorynight",  # Kiimon (h: Evil Castle -- dark iron)
    14: "datatunnel",    # Dokimon (h: Hard Disk)
    15: "underwater",    # Chibomon (f: DeepSaver / Water)
    16: "factory",       # Datirimon (f: MetalEmpire)
    17: "forestgate",    # ChibiKiwimon (h: Forest)
    18: "cove",          # Ketomon (h: Cliffside)
    19: "forestgate",    # Leafmon (h: Forest)
    20: "frozenpeak",    # Pafumon (h: Sky)
    21: "datatunnel",    # Paomon (h: Hard Disk)
    22: "volcano",       # Petitmon (f: DragonsRoar / Fire)
    23: "lakeside",      # Popomon (h: Lake)
    24: "flowerfield",   # Pupumon (h: Field)
    25: "factorynight",  # Bommon (h: Evil Castle)
    26: "lakeside",      # Pusumon (h: Lake)
    27: "forestgate",    # Puwamon (h: Forest)
    28: "moonmeadow",    # Relemon (f: NightmareSoldier)
    29: "city",          # Sakumon (h: City)
    30: "underwater",    # Zerimon (f: DeepSaver / Water)
    31: "moonmeadow",    # Cocomon (f: NightmareSoldier)
    32: "frozenpeak",    # Fufumon (h: Sky)
    33: "city",          # Cotsucomon (h: City)
    34: "datatunnel",    # Algomon I (f: DarkArea; * the net algae lives IN the net)
    35: "city",          # Bombmon (h: City)
    36: "goldenwood",    # Carimon (f: VirusBuster / Light)
    37: "desert",        # Sunamon (* suna = sand: the sand egg gets the desert,
                         #   whatever the csv's Canyon says -- and the DM20
                         #   desert rip deserves a wearer)
    38: "mountains",     # Curimon (h: Canyon)
    39: "forestgate",    # Pyonmon (h: Forest)
    40: "underwater",    # Puyomon (h: Underwater)
    41: "datatunnel",    # ??? (* the mystery egg keeps digital static)
    42: "city",          # ??? / hack (h: City)
    43: "frozenpeak",    # Fusamon (h: Tundra)
    44: "greenhills",    # Nature Spirits Egg (f: NatureSpirit)
    45: "underwater",    # Deep Savers Egg (h: Underwater)
    46: "moonmeadow",    # Nightmare Soldiers Egg (f: NightmareSoldier)
    47: "flowerfield",   # Wind Guardians Egg (h: Field)
    48: "city",          # Metal Empire Egg (h: City)
    49: "goldenwood",    # Virus Busters Egg (f: VirusBuster / Light)
    50: "volcano",       # Corona Egg (* the sun egg burns, whatever the csv says)
    51: "moonmeadow",    # Luna Egg (* the moon egg gets the moonlit meadow)
    52: "city",          # Zuba Egg (h: City)
    53: "city",          # Hack Egg (h: City)
    54: "blossom",       # Meicoo Egg / verE (f: NatureSpirit / Light)
    55: "lakeside",      # DORU Egg (h: Lake)
    56: "volcano",       # Slayerdra Egg (f: DragonsRoar / Fire)
    57: "mountains",     # Breakdra Egg (f: DragonsRoar / Earth -- the drill)
    58: "frozenpeak",    # Ryuda Egg (h: Sky)
    59: "volcano",       # Draco Egg (f: DragonsRoar / Fire)
    60: "flowerfield",   # Lalamon Egg (h: Field)
    61: "tealhollow",    # Meicoomon Egg (* the teal cat gets the teal hollow)
    62: "baybridge",     # Terrier Egg (* Willis's twin: the movie's Golden Gate)
    63: "bridgenight",   # Lop Egg (* the dark twin gets the bridge at night)
    64: "frozenpeak",    # V Egg (f: WindGuardian -- the cloud sea)
    65: "greenhills",    # Virus Busters Ver. 20th Egg (h: Plains)
    66: "cityday",       # Digitama X3 (* the Royal Knights' white city)
    67: "datatunnel",    # Kera Digitama (h: Hard Disk)
}


def scene_for_egg(egg_type):
    """The scene an egg wires its whole line to (unknown egg -> DEFAULT)."""
    try:
        return EGG_BG.get(int(egg_type), DEFAULT)
    except (TypeError, ValueError):
        return DEFAULT


def name(key):
    return NAMES.get(key, key)
