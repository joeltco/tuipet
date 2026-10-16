"""Build src/tuipet/data/adventure_maps.json -- tuipet's OWN adventure world
(rebuild 2026-10-14, Joel: "it was built with an older llm ... needs to be
built from scratch").  30 maps, one per scene background, one map = one run.

Every row is derived from data already in the game, never invented:
  wilds  = the dex forms of the map's TIER whose FIELD fits the terrain
           (placeholders and the Godzilla line excluded -- kaiju live on
           Monster Island only)
  boss   = the lowest-numbered form of those fields one tier UP (Mega maps:
           Mega), never reused by an earlier map
  finds  = food + care catalog items for the terrain family
  reward = the tier's power item (+ a Human Spirit on the ten deepest maps,
           + the X-Program on the Mega maps: the retired road was their only
           source -- the spirits as zone finds, the X-Program as an elite drop;
           + a Grow Capsule on maps 7 and 23, its only source since the
           shop stopped selling it -- shop/loot audit 2026-10-14)
Run:  PYTHONPATH=src python3 tools/build_adventure_maps.py
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from tuipet import data, shop, backgrounds  # noqa: E402

NS, DS, WG, JT, DR = "NatureSpirit", "DeepSaver", "WindGuardian", "JungleTrooper", "DragonsRoar"
ME, NSO, VB, DA, NO = "MetalEmpire", "NightmareSoldier", "VirusBuster", "DarkArea", "None"
GZ = "godzilla"

FIELDS_ = ["fish", "vegetable", "candy", "cupcake", "meat"]
FLOWERS = ["vegetable", "candy", "cookie", "honey", "fruit"]
HOLLOW = ["poison_mushroom", "vegetable", "candy"]
WATER = ["fish", "tuna", "vegetable", "cookie"]
ISLAND = ["tuna", "fish", "cupcake", "orange"]
HIGH = ["steak", "cheese", "bread", "red_pepper", "vitamin"]
SAND = ["tuna", "vitamin", "yellow_pepper", "orange"]
TOWN = ["cheese_burger", "bread", "food_pill"]
WIRE = ["green_pepper", "food_pill", "med"]

# (scene, tier, fields, finds) in ROAD ORDER -- map 1 first
MAPS = [
    ("greenhills", "Rookie", [NS], FIELDS_),
    ("flowerfield", "Rookie", [WG], FLOWERS),
    ("lakeside", "Rookie", [DS], WATER),
    ("forestgate", "Rookie", [JT], HOLLOW),
    ("cove", "Rookie", [DS, NS], WATER),
    ("islandsea", "Rookie", [DR], ISLAND),
    ("moonmeadow", "Rookie", [NSO], FIELDS_),
    ("blossom", "Champion", [WG], FLOWERS),
    ("goldenwood", "Champion", [NS], HOLLOW),
    ("jungle", "Champion", [JT], HOLLOW),
    ("tealhollow", "Champion", [NSO], HOLLOW),
    ("mountains", "Champion", [DR], HIGH),
    ("desert", "Champion", [NO], SAND),
    ("underwater", "Champion", [DS], WATER),
    ("citysunset", "Champion", [ME], TOWN),
    ("seafloor", "Ultimate", [DS], WATER),
    ("frozenpeak", "Ultimate", [WG], HIGH),
    ("city", "Ultimate", [ME], TOWN),
    ("cityday", "Ultimate", [VB], TOWN),
    ("boulevard", "Ultimate", [NO], TOWN),
    ("volcano", "Ultimate", [DR], HIGH),
    ("fileisland", "Ultimate", [NS, JT], ISLAND),
    ("islandnight", "Ultimate", GZ, ISLAND),
    ("sunsetshore", "Mega", [DS], WATER),
    ("baybridge", "Mega", [WG, JT], TOWN),
    ("boulevardusk", "Mega", [VB], TOWN),
    ("bridgenight", "Mega", [DR], TOWN),
    ("factory", "Mega", [ME], WIRE),
    ("factorynight", "Mega", [NSO], WIRE),
    ("datatunnel", "Mega", [DA], WIRE),
]
NAME_OVERRIDE = {"islandnight": "Monster Island"}
GROW_CAPSULE_MAPS = (6, 22)        # maps 7 and 23 (0-based)
UP = {"Rookie": "Champion", "Champion": "Ultimate", "Ultimate": "Mega", "Mega": "Mega"}
REWARD = {"Rookie": "vitamin", "Champion": "hp_chip", "Ultimate": "hp_chip_g", "Mega": "omni_chip_g"}
SPIRITS = ["human_fire_spirit", "human_light_spirit", "human_ice_spirit", "human_wind_spirit",
           "human_thunder_spirit", "human_earth_spirit", "human_water_spirit", "human_wood_spirit",
           "human_metal_spirit", "human_dark_spirit"]
GZ_BOSS = 1644          # Godzilla 1994


def is_gz(n):
    return 1623 <= n <= 1650


def is_card_only(n):
    """The VB card forms kitbashed 2026-10-15: they hatch from their cards, never roam the maps."""
    return 1651 <= n <= 1658


def main():
    _, by = data.load_sprites()
    live = {n: r for n, r in by.items() if not data.is_placeholder(n) and not is_card_only(n)}
    for k in sum((m[3] for m in MAPS), []) + list(REWARD.values()) + SPIRITS:
        assert k in shop.CATALOG, k
    taken, out = set(), []
    for i, (scene, tier, fields, finds) in enumerate(MAPS):
        assert scene in backgrounds.NAMES, scene
        if fields == GZ:
            wilds = sorted(n for n, r in live.items()
                           if is_gz(n) and r["stage"] in ("Champion", "Ultimate"))
            boss = GZ_BOSS
        else:
            wilds = sorted(n for n, r in live.items()
                           if r["stage"] == tier and r["field"] in fields and not is_gz(n))
            boss = min(n for n, r in live.items()
                       if r["stage"] == UP[tier] and r["field"] in fields
                       and not is_gz(n) and n not in taken)
        taken.add(boss)
        reward = [REWARD[tier]] + (["x_program"] if tier == "Mega" else [])
        deep = len(MAPS) - len(SPIRITS)
        if i >= deep:
            reward.append(SPIRITS[i - deep])
        if i in GROW_CAPSULE_MAPS:
            reward.append("grow_capsule")
        out.append({"id": scene, "name": NAME_OVERRIDE.get(scene, backgrounds.NAMES[scene]),
                    "scene": scene, "tier": tier,
                    "fields": "Godzilla kaiju" if fields == GZ else fields,
                    "wilds": wilds, "boss": boss, "finds": finds + ["life_recovery", "rest_kit"],
                    "wild_drops": finds, "reward": reward})
    path = os.path.join(os.path.dirname(__file__), "..", "src", "tuipet", "data",
                        "adventure_maps.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    for i, m in enumerate(out, 1):
        print(f"{i:2} {m['name']:19} {m['tier']:8} wild {len(m['wilds']):3} "
              f"boss {by[m['boss']]['name']:18} {m['reward']}")


if __name__ == "__main__":
    main()
