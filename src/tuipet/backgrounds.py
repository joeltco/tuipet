"""The background catalog (the Great Simplification, 2026-07-15).

Habitats, weather, temperature and the day/night cycle are gone (Joel: "its
too much") -- the scene behind the mon is now a PICKED COSMETIC.  The art is
official Digimon location art (the DSprite rip set, Joel-approved source
2026-07-15), cropped top-and-bottom to the 40x24 LCD.  Basic backgrounds are
free; the fancy ones cost bits.  `townBack` is not in the catalog: it
survives for ADVENTURE town events only.
"""
from . import data

DEFAULT = "greenhills"          # every save owns the free set; this one starts picked

# key -> (display name, price in bits; 0 = free)
CATALOG = {
    "greenhills":   ("Green Hills", 0),
    "city":         ("City", 0),
    "desert":       ("Desert", 0),
    "flowerfield":  ("Flower Field", 0),
    "lakeside":     ("Lakeside", 0),
    "forestgate":   ("Forest Gate", 0),
    "jungle":       ("Jungle", 0),
    "boulevard":    ("Boulevard", 0),
    "islandsea":    ("Island Sea", 200),
    "cityday":      ("White City", 200),
    "mountains":    ("Mountains", 200),
    "factory":      ("Factory", 200),
    "blossom":      ("Blossom Field", 300),
    "cove":         ("Cove", 300),
    "boulevardusk": ("Boulevard Dusk", 300),
    "baybridge":    ("Bay Bridge", 300),
    "fileisland":   ("File Island", 400),
    "citysunset":   ("City Sunset", 400),
    "goldenwood":   ("Golden Wood", 400),
    "seafloor":     ("Seafloor", 400),
    "factorynight": ("Factory Night", 500),
    "tealhollow":   ("Teal Hollow", 500),
    "islandnight":  ("Island Night", 600),
    "moonmeadow":   ("Moonlit Meadow", 600),
    "sunsetshore":  ("Sunset Shore", 600),
    "bridgenight":  ("Bridge Night", 600),
    "underwater":   ("Underwater", 800),
    "datatunnel":   ("Data Tunnel", 800),
    "volcano":      ("Volcano", 800),
    "frozenpeak":   ("Frozen Peak", 800),
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
    return CATALOG.get(key, (key, 0))[0]


def price(key):
    return CATALOG.get(key, ("", 0))[1]


def frame(key):
    """The single scene frame for `key` (or None) -- backgrounds no longer
    carry time-of-day/weather sheets, one look each."""
    sheet = data.load_backgrounds().get(key)
    return sheet[0] if sheet else None
