"""The DSprite background catalog, wired to the eggs (BASIC VPET 2026-07-16).

Habitats are gone (Joel: "remove the habitats. wire in the dsprite
backgrounds") -- the scene behind the mon is decided by the EGG it hatched
from and stands for the pet's whole life, exactly like the real device's
per-version backgrounds (the old egg0Back..egg11Back sheets this system
replaces).  The art is the DSprite rebuild's rip set (Joel-approved source
2026-07-15).  Several scenes ship as time-of-day / recolour FAMILIES of one
composition -- verified by structural correlation of the actual pixels, not
filenames (scene-name audit 2026-07-20): the island at sunset/day/night, the
flower field day/sunset, the seafloor day/deep/sunset, the city towers and
the bay bridge and the factory day/night, the tree path green/golden.  They
are grouped and named as such in NAMES below.

The egg->scene wiring is derived, not invented: each egg's hatch line maps
through its members' natural habitats (digimon.csv Habitat, the same table
the habitat system read) onto the DSprite rebuild's own biome->scene map;
lines with no habitat data fall back to their dominant FIELD.  A handful of
flavor overrides are marked inline.
"""

DEFAULT = "greenhills"          # the DM20 background rip; also the fallback

# key -> display name (the clone catalog + the off-catalog data scenes).
# DISPLAY names only -- the KEYS are wired (EGG_BG, pet.bg_pick in saves) and
# never change.  THE FAMILY LAW (scene-name audit 2026-07-20, done by LOOKING
# at the pixels + structural correlation, Joel: "you keep guessing instead of
# looking at the actual pictures... duplicates with time differences"): a
# scene shipped as several time-of-day / recolour sheets shares a family word,
# and each member says its time.  Corrections this pass:
#   * cove is a BEACH (sand foreground, water beyond) -- it was mislabelled
#     "Sandy Seafloor" and grouped with the seafloors, but it has ZERO
#     structural correlation with them.  It is its own shore.
#   * the real seafloor is ONE undersea scene at three lightings:
#     underwater=Seafloor (day), seafloor=Seafloor Deep, sunsetshore=Seafloor
#     Sunset.  (The old catalog counted the beach as the third seafloor and
#     left the actual sunset seafloor named like a "shore" -- backwards.)
#   * tealhollow is a SEPARATE teal-underwater V, not the green/golden path
#     recolour (corr 0.40, not 1.00) -- kept apart from the tree-path pair.
# Grouped by verified family:
NAMES = {
    # grasslands & meadows
    "greenhills":   "Green Hills",
    "moonmeadow":   "Moonlit Meadow",   # a daytime cool-toned meadow (name kept)
    "lakeside":     "Lakeside",
    # flower field -- one scene, day + sunset
    "flowerfield":  "Flower Field",
    "blossom":      "Flower Field Sunset",
    # tree-lined path -- one composition, green + golden recolour (corr 1.00)
    "forestgate":   "Green Hollow",
    "goldenwood":   "Golden Hollow",
    # mountains, ice, desert
    "mountains":    "Mountains",
    "frozenpeak":   "Frozen Peak",
    "desert":       "Desert",
    # island mountain -- one scene, sunset + day + night
    "fileisland":   "Island Sunset",
    "islandsea":    "Island Day",
    "islandnight":  "Island Night",
    # water -- the beach (a shore), the seafloor trio (one undersea scene,
    # day + deep + sunset), and the separate teal-underwater V
    "cove":         "Beach",
    # the seafloor trio names its LIGHTING second ("Seafloor Deep/Sunset")
    # like every other multi-lit scene here (City Sunset, Island Night) so
    # the picker's A-Z-by-name sort keeps all three adjacent -- the old
    # "Deep Seafloor"/"Sunset Seafloor" alphabetised under D and S, orphaning
    # the deep one 17 rows from its siblings (picker grouping 2026-07-24,
    # Joel "why is the deep sea background not with the other sea backgrounds").
    "underwater":   "Seafloor",
    "seafloor":     "Seafloor Deep",
    "sunsetshore":  "Seafloor Sunset",
    "tealhollow":   "Teal Hollow",
    # fire & jungle
    "volcano":      "Volcano",
    "jungle":       "Jungle",
    # city -- towers (day+dusk), boulevard (day+dusk), bay bridge (day+night),
    # factory (day+night), the white waterfront skyline, the data tunnel
    "city":         "City",
    "citysunset":   "City Sunset",
    "boulevard":    "Boulevard",
    "boulevardusk": "Boulevard Dusk",
    "baybridge":    "Bay Bridge",
    "bridgenight":  "Bay Bridge Night",
    "factory":      "Factory",
    "factorynight": "Factory Night",
    "cityday":      "White City",
    "datatunnel":   "Data Tunnel",
    # arena
    "tourneyBack":  "Arena",
}

# egg index -> scene.  Derivation key: (h) = the line's natural habitat via
# the rebuild's biome map, (f) = dominant-field fallback, (*) = flavor
# override, reasoned inline.
EGG_BG = {
    0: "greenhills",     # Botamon / ver1 (h: Plains)
    1: "mountains",      # Punimon / ver2 (h: Canyon)
    2: "forestgate",     # Poyomon / ver3 (h: Forest)
    3: "forestgate",     # Yuramon / ver4 (Palmon PLANT line -- a forest fits the
                         #   creature.  Long re-home saga (cove/sunsetshore were
                         #   seabed, then islandsea for an h:Cliffside reading);
                         #   settled 2026-07-20: a plant belongs in the wood, not
                         #   on a sea coast)
    4: "islandsea",      # Zurumon / ver5 (h: Ocean)
    5: "datatunnel",     # Kuramon (h: Hard Disk -- the Diablomon net)
    6: "greenhills",     # Chibickmon (h: Plains)
    7: "islandsea",      # Tsubumon (h: Ocean)
    8: "flowerfield",    # Pururumon (h: Field)
    9: "lakeside",      # Dodomon / verX (h: Lake)
    10: "mountains",     # Puttimon (h: Sky -- big open sky.  Sky habitat is warm
                         #   & windy, NOT the icy Frozen Peak=Tundra it used to
                         #   sit on; Sky->Mountains, 2026-07-20)
    11: "factorynight",  # Kiimon (h: Evil Castle -- dark iron)
    12: "datatunnel",    # Dokimon (h: Hard Disk)
    13: "underwater",    # Chibomon (f: DeepSaver / Water)
    14: "islandsea",     # Ketomon (h: Cliffside -- the island's rock over open
                         #   sea, the one true coast in the set)
    15: "forestgate",    # Leafmon (h: Forest)
    16: "volcano",       # Petitmon (f: DragonsRoar / Fire)
    17: "city",          # Sakumon (h: City)
    18: "underwater",    # Zerimon (f: DeepSaver / Water)
    19: "moonmeadow",    # Cocomon (f: NightmareSoldier)
    20: "mountains",     # Fufumon (h: Sky -- warm/windy, Sky->Mountains 2026-07-20)
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
    37: "mountains",     # Ryuda Egg (h: Sky; Ryudamon is a ground samurai-dragon
                         #   -- rugged mountains, not ice.  Sky->Mountains 2026-07-20)
    38: "volcano",       # Draco Egg (f: DragonsRoar / Fire)
    39: "flowerfield",   # Lalamon Egg (h: Field)
    40: "baybridge",     # Terrier Egg (* Willis's twin: the movie's Golden Gate)
    41: "bridgenight",   # Lop Egg (* the dark twin gets the bridge at night)
    42: "greenhills",    # V Egg (f: WindGuardian -- Veemon is a warm dragon
                         #   warrior; open green hills beat an ice peak, 2026-07-20)
    43: "greenhills",    # Virus Busters Ver. 20th Egg (h: Plains)
    44: "cityday",       # Digitama X3 (* the Royal Knights' white city)
    45: "datatunnel",    # Kera Digitama (h: Hard Disk)
    46: "city",          # Godzilla Egg (* the kaiju come ashore at the city --
                         #   the device's G-Cell scenes end "Inside City")
    47: "volcano",       # Volcanic Beat Egg (VB DIM card; its egg unlocks on the Volcano road)
    48: "seafloor",      # Infinite Tide Egg (VB DIM card; unlocks on the Seafloor Deep road)
    49: "factory",       # Nu Metal Empire Egg (VB DIM card; unlocks on the Factory road)
    50: "frozenpeak",    # Blizzard Fang Egg (VB DIM card; the genuinely cold line Frozen Peak waited for)
    51: "jungle",        # Hermit in the Jungle Egg (VB DIM card; unlocks on the Jungle road)
    52: "tealhollow",    # Mad Black Roar Egg (VB DIM card; unlocks on the Teal Hollow road)
    53: "moonmeadow",    # True Shadow Howl Egg (VB DIM card; wolves howl on the Moonlit Meadow road)
    54: "citysunset",    # Impulse City Egg (VB DIM card; unlocks on the City Sunset road)
    55: "mountains",     # Gammamon Egg (VB DIM card; unlocks on the Mountains road, Wingdramon's)
    56: "flowerfield", # Fairimon EX Egg (VB DIM card; unlocks on the Flower Field road)
    57: "forestgate",  # Angoramon Egg (VB DIM card; unlocks on the Green Hollow road)
    58: "underwater",  # Jellymon Egg (VB DIM card; unlocks on the Seafloor road)
    59: "cityday",     # Agumon EX Egg (VB DIM card; unlocks on the White City road)
    60: "lakeside",    # Gabumon EX Egg (VB DIM card; unlocks on the Lakeside road)
    61: "cove",        # Dinosaur Roar Egg (VB DIM card; unlocks on the Beach road)
    62: "boulevardusk", # Guilmon GP Egg (VB DIM card; unlocks on the Boulevard Dusk road)
    63: "islandsea",   # Guilmon EX Egg (VB DIM card; unlocks on the Island Day road)
    64: "goldenwood",  # Ryudamon Egg (VB DIM card; unlocks on the Golden Hollow road)
    65: "factorynight", # Impmon GP Egg (VB DIM card; unlocks on the Factory Night road)
    66: "bridgenight", # Black Roar Egg (VB DIM card; unlocks on the Bay Bridge Night road)
    67: "fileisland",  # Shadow Howl Egg (VB DIM card; unlocks on the Island Sunset road)
    68: "datatunnel",  # Louwemon EX Egg (VB DIM card; unlocks on the Data Tunnel road)
    69: "greenhills",  # Wolf Howl Egg (VB DIM card; unlocks on the Green Hills road)
    70: "blossom",     # Espimon Egg (VB DIM card; unlocks on the Flower Field Sunset road)
    71: "boulevard",   # Blitzmon EX Egg (VB DIM card; unlocks on the Boulevard road)
    72: "sunsetshore", # Wolfmon EX Egg (VB DIM card; unlocks on the Seafloor Sunset road)
    73: "desert",      # Agnimon EX Egg (VB DIM card; unlocks on the Desert road)
    74: "baybridge",   # Terriermon EX Egg (VB DIM card; unlocks on the Bay Bridge road)
    75: "moonmeadow",  # Renamon GP Egg (VB DIM card; unlocks on the Moonlit Meadow road)
    76: "tealhollow",  # Renamon EX Egg (VB DIM card; unlocks on the Teal Hollow road)
    77: "islandsea",   # Monodramon GP Egg (VB DIM card; unlocks on the Island Day road)
    78: "islandsea",   # Ancient Warriors Egg (VB DIM card; unlocks on the Island Day road)
    79: "underwater",  # Chackmon EX Egg (VB DIM card; unlocks on the Seafloor road)
    80: "greenhills",  # Titan of Dust Egg (VB DIM card; unlocks on the Green Hills road)
    81: "forestgate",  # Primeval Warriors Egg (VB DIM card; unlocks on the Green Hollow road)
    82: "city",        # Dynasty of the Evil Egg (VB DIM card; unlocks on the City road)
}


# the E picker's shelf (restored 2026-07-17: "add the e action back"): every
# named scene except the arena is a FREE pick, the clone's final ruling
# ("get rid of the price walls" -- Joel 2026-07-16).  The egg still decides
# the DEFAULT scene; a pick merely overrides it (pet.bg_pick).
# ...in FAMILY + THEME order, not A-Z (Joel 2026-10-15: "Shouldn't they at least
# be more organized?"): every recolour sits beside its base (structural
# correlation, measured: Green/Golden Hollow 0.98, Boulevard/Dusk 0.96, Flower
# Field/Sunset 0.96, City/Sunset 0.95, Island 0.85, Bay Bridge 0.85, Seafloor
# 0.72, Factory 0.70; Teal Hollow is the same path redrawn), and the families
# run land -> water -> city -> digital.
PICKS = ("greenhills", "moonmeadow", "lakeside",
         "flowerfield", "blossom",
         "forestgate", "goldenwood", "tealhollow",
         "jungle", "mountains", "frozenpeak", "desert", "volcano",
         "cove", "islandsea", "fileisland", "islandnight",
         "underwater", "seafloor", "sunsetshore",
         "city", "citysunset", "cityday", "boulevard", "boulevardusk",
         "baybridge", "bridgenight", "factory", "factorynight",
         "datatunnel")
assert sorted(PICKS) == sorted(k for k in NAMES if k != "tourneyBack")


def scene_for_egg(egg_type):
    """The scene an egg wires its whole line to (unknown egg -> DEFAULT)."""
    try:
        return EGG_BG.get(int(egg_type), DEFAULT)
    except (TypeError, ValueError):
        return DEFAULT


def name(key):
    return NAMES.get(key, key)
