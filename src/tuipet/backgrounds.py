"""The background catalog (the Great Simplification, 2026-07-15).

Habitats, weather, temperature and the day/night cycle are gone (Joel: "its
too much") -- the scene behind the mon is now a PICKED COSMETIC.  The art is
official location art (the DSprite rip set, Joel-approved source
2026-07-15; picker = the Xross range, Godzilla range = world data only,
2026-07-16), cropped top-and-bottom to the 40x24 LCD.  Every catalog scene
is FREE for now.  `townBack` is not in the catalog: it survives for
ADVENTURE town events only.
"""
from . import data

DEFAULT = "forestgate"          # every save owns the catalog; this one starts picked

# key -> (display name, price in bits; 0 = free).  ALL FREE for now (Joel
# 2026-07-16: "get rid of the price walls") -- the price column stays so the
# walls can return without a schema change.
#
# The picker offers the XROSS-range tiles only.  The GODZILLA-range tiles
# (DSprite's own select marks BG 14-47 "Godzilla": the cityscapes, factory,
# islands, desert, jungle, lakeside, mountains, cove, greenhills) stay in
# backgrounds.json.gz as WORLD DATA -- adventure roads and special rooms may
# wear them -- but they are not choosable home scenes (Joel 2026-07-16).
CATALOG = {
    "forestgate":   ("Forest Gate", 0),
    "flowerfield":  ("Flower Field", 0),
    "blossom":      ("Blossom Field", 0),
    "goldenwood":   ("Golden Wood", 0),
    "tealhollow":   ("Teal Hollow", 0),
    "moonmeadow":   ("Moonlit Meadow", 0),
    "underwater":   ("Underwater", 0),
    "seafloor":     ("Seafloor", 0),
    "volcano":      ("Volcano", 0),
    "sunsetshore":  ("Sunset Shore", 0),
    "baybridge":    ("Bay Bridge", 0),
    "bridgenight":  ("Bridge Night", 0),
    "datatunnel":   ("Data Tunnel", 0),
    "frozenpeak":   ("Frozen Peak", 0),
}

# names for the off-catalog data scenes (roads, special rooms, old picks)
_DATA_NAMES = {
    "city": "City", "cityday": "White City", "citysunset": "City Sunset",
    "boulevard": "Boulevard", "boulevardusk": "Boulevard Dusk",
    "factory": "Factory", "factorynight": "Factory Night",
    "fileisland": "Lone Island", "islandsea": "Island Sea",
    "islandnight": "Island Night", "desert": "Desert", "jungle": "Jungle",
    "lakeside": "Lakeside", "mountains": "Mountains", "cove": "Cove",
    "greenhills": "Green Hills", "townBack": "Town",
}

FREE = tuple(k for k, (_, p) in CATALOG.items() if p == 0)

# special rooms (not picks): the tournament/PvP arena and the adventure town
ARENA = "datatunnel"
TOWN = "townBack"

# adventure zone scenery: the zones.csv habitat bands survive as WORLD DATA
# (biome ids name the terrain); each biome wears a catalog scene on the road
BIOME_BG = {
    0: "datatunnel",    # Hard Disk
    1: "frozenpeak",    # Sky -- the cloud sea
    2: "greenhills",    # Plains
    3: "mountains",     # Canyon
    4: "forestgate",    # Forest
    5: "frozenpeak",    # Tundra
    6: "islandsea",     # Ocean
    7: "lakeside",      # Lake
    8: "underwater",    # Underwater
    9: "factorynight",  # Evil Castle -- dark iron
    10: "flowerfield",  # Field
    11: "city",         # City
    12: "cove",         # Cliffside
    13: TOWN,           # Town (the kept DVPet sheet, adventures only)
    14: "volcano",      # Volcano
    15: "desert",       # Desert
}


def biome_frame_key(hid):
    return BIOME_BG.get(hid, DEFAULT)


def name(key):
    if key in CATALOG:
        return CATALOG[key][0]
    return _DATA_NAMES.get(key, key)


def price(key):
    return CATALOG.get(key, ("", 0))[1]


def frame(key):
    """The single scene frame for `key` (or None) -- backgrounds no longer
    carry time-of-day/weather sheets, one look each."""
    sheet = data.load_backgrounds().get(key)
    return sheet[0] if sheet else None
