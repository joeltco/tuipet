"""The shop: a fixed catalog of priced items (the clone rebuild, 2026-07-15).

Every priced entry in the item table is on the shelf, grouped by its own
category column; buying moves it into the bag at face value; the bag can
sell it back for half.  Effects live in Pet.use_item — the token text here
mirrors those exact effects so the shelf, the bag and the belly can never
disagree.
"""
from __future__ import annotations
from . import data

# a season name survives as pure flavour text for the town greeters
SEASONS = ("Spring", "Summer", "Fall", "Winter")
SEASON_DAYS = 13


def season_name(pet):
    return SEASONS[(getattr(pet, "age_days", 0) // SEASON_DAYS) % len(SEASONS)]


# what each usable item DOES (mirrors Pet.use_item exactly)
EFFECTS = {
    "energy_drink": "energy to FULL",
    "best_fruit": "hunger +1 · effort +1",
    "normal_fruit": "hunger +1",
    "worst_fruit": "hunger +1 · weight +3",
    "deadly_fruit": "DO NOT FEED",
    "junk_food": "fills belly · a care mistake",
    "premium_meat": "12h satiety",
    "poop_clean_pill": "auto-clean 24h",
    "care_mistake_eraser": "mistake -1",
    "sleeping_pill": "sleep now",
    "alarm_clock": "wake now",
    "time_gear": "growth +120min",
    "anti_evo_chip": "toggle evolution lock",
    "x_antibody": "the X path (if one exists)",
    "training_pack": "training +5",
    "revive_floppy": "raise the dead",
    "super_carrot": "weight -10",
}
# the crest eggs: used from the bag, they trigger an ITEM EVOLUTION
ARMOR_CATEGORY = "Armor-Spirit"


def _usable(key, category):
    """Only goods Pet.use_item can actually APPLY are sold (the same
    doctrine as data.item_is_functional): the ripped catalog also carries
    28 theme_* skins and the 200k storage_drive, whose systems (app themes,
    the D-Terminal) don't exist in tuipet -- up to 200k bits bought NOTHING
    (audit 2026-07-15).  Extend EFFECTS as each system is built."""
    return category == ARMOR_CATEGORY or key in EFFECTS


def catalog():
    """Every buyable entry: [{key, name, price, category}], price order."""
    out = []
    for k, v in data.load_vitems().items():
        if isinstance(v, dict) and v.get("price") \
                and _usable(k, v.get("category", "Item")):
            out.append({"key": k, "name": v.get("name", k),
                        "price": int(v["price"]),
                        "category": v.get("category", "Item")})
    out.sort(key=lambda e: (e["category"], e["price"], e["name"]))
    return out


def entry(key):
    v = data.load_vitems().get(key)
    if not isinstance(v, dict):
        return None
    return {"key": key, "name": v.get("name", key),
            "price": int(v.get("price", 0) or 0),
            "category": v.get("category", "Item")}


def categories():
    return sorted({e["category"] for e in catalog()})


def shelf(cat):
    return [e for e in catalog() if e["category"] == cat]


def effect_line(e):
    if e["category"] == ARMOR_CATEGORY:
        return "an armor evolution (right Child)"
    return EFFECTS.get(e["key"], "a curiosity")


def buy(pet, e):
    """-> (message, sfx)."""
    if pet.bits < e["price"]:
        return (f"Need {e['price']}b — you have {pet.bits}b.", "error")
    pet.spend_bits(e["price"])
    pet.add_item(e["key"])
    return (f"Bought {e['name']}!", "buy")


def resell_price(e):
    return max(1, e.get("price", 0) // 2)


def sell(pet, e):
    if not pet.take_item(e["key"]):
        return ("You don't have that.", "error")
    pet.add_bits(resell_price(e))
    return (f"Sold {e['name']} for {resell_price(e)}b.", "buy")


# ---- town storefronts: the same catalog behind every counter ----

def home_shop_open(pet):
    return True


def town_shop_open(pet, town, is_food):
    return True


def town_shop_hours(pet, town, is_food):
    return (0, 24)


def roll_town_shop(pet, town, is_food):
    """A town counter: food items on the food shelf, gear on the other."""
    want = ("Food", "Care") if is_food else None
    out = []
    for e in catalog():
        if want is None and e["category"] not in ("Food", "Care"):
            out.append(dict(e, stock=9, sale=0))
        elif want is not None and e["category"] in want:
            out.append(dict(e, stock=9, sale=0))
    return out


def slot_label(e):
    return f"{e['name']}  {e['price']}b"


def slot_info(pet, e, tw):
    return [e["name"][:tw], f"{e['price']}b", effect_line(e)[:tw]]


def sell_info(pet, e, tw):
    return [e["name"][:tw], f"sells {resell_price(e)}b", effect_line(e)[:tw]]


def purchase_price(e):
    return e["price"]
