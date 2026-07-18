"""The shop: a fixed catalog of priced items (the DSprite item system,
cloned from the v0.4.x rebuild -- BASIC VPET 2026-07-16).

Every priced entry in vitems.json is on the shelf, grouped by its own
category column; buying moves it into the bag at face value; the bag can
sell it back for half.  Effects live in Pet.use_item — the token text here
mirrors those exact effects so the shelf, the bag and the belly can never
disagree.  The DVPet rolled-slot/town-hours shop machine is retired; the
town counters serve the same catalog.  The digitama-licence shelf was cut
2026-07-17 ("i never wanted egg licenses"): eggs unlock by condition only,
like the real devices -- the shop sells goods, never digitama.
"""
from __future__ import annotations
from . import data


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
    "x_antibody": "the X-Antibody takes hold",
    "training_pack": "training +5",
    "revive_floppy": "raise the dead",
    "super_carrot": "weight -10",
}
# the crest eggs: used from the bag, they trigger the classic ARMOR evolution
# (Pet._crest_egg -> evolution.item_select via the Digimental ids)
ARMOR_CATEGORY = "Armor-Spirit"

# the Digimental waves (Joel 2026-07-17: "wire the gates") -- the canon
# discovery order, on the same earned-access rule as the egg carousel:
# sealed ones simply don't appear.  Courage & Hope open armor evolution
# from day one; the crest seven follow the FIRST armor evolution; the 02
# pair rides lifetime wins; Miracles is golden (raids); Destiny is the
# movie one (generation 5).  Gate signals are persistence.get_progress().
DIGIMENTAL_GATES = {
    "egg_of_courage": None,
    "egg_of_hope": None,
    "egg_of_friendship": ("armor_evos", 1),
    "egg_of_love": ("armor_evos", 1),
    "egg_of_knowledge": ("armor_evos", 1),
    "egg_of_sincerity": ("armor_evos", 1),
    "egg_of_reliability": ("armor_evos", 1),
    "egg_of_light": ("wins", 25),
    "egg_of_kindness": ("wins", 25),
    "egg_of_miracles": ("raids", 2),
    "egg_of_destiny": ("max_gen", 5),
}


def digimental_open(key, prog=None):
    """Is this Digimental's wave reached?  (Non-digimental keys are open.)"""
    gate = DIGIMENTAL_GATES.get(key)
    if gate is None:
        return True
    if prog is None:
        from . import persistence
        prog = persistence.get_progress()
    sig, need = gate
    return int(prog.get(sig, 0)) >= need

# (the DVPet staple props -- Toilet/Port. Potty/Futon, items.csv 81-83, and
# their uses/cap stock maths -- left 2026-07-17: strict-DSprite items
# ("go strict").  DSprite's catalog has no furniture; the shelf is exactly
# vitems.json.)

# the source shop prices any entry with no explicit price at a flat default
# (`e.price || 1e3`); the 11 crest eggs ship priceless, so without this they
# never reach the shelf.  Faithful to the source default, not invented.
DEFAULT_PRICE = 1000

def _price(v):
    return int(v.get("price") or DEFAULT_PRICE)


def _usable(key, category):
    """Only goods Pet.use_item can actually APPLY are sold: the ripped
    catalog also carries 28 theme_* skins and the 200k storage_drive, whose
    systems don't exist in tuipet."""
    return category == ARMOR_CATEGORY or key in EFFECTS


def catalog():
    """Every buyable entry: [{key, name, price, category}], price order.
    A Digimental whose wave isn't reached is SEALED: it stays off the shelf
    entirely (the egg-carousel rule), though entry() still resolves it so
    an already-owned one renders in the bag."""
    from . import persistence
    prog = persistence.get_progress()
    out = []
    for k, v in data.load_vitems().items():
        if isinstance(v, dict) and _usable(k, v.get("category", "Item")) \
                and digimental_open(k, prog):
            out.append({"key": k, "name": v.get("name", k),
                        "price": _price(v),
                        "category": v.get("category", "Item")})
    out.sort(key=lambda e: (e["category"], e["price"], e["name"]))
    return out


def entry(key):
    v = data.load_vitems().get(key)
    if not isinstance(v, dict):
        return None
    return {"key": key, "name": v.get("name", key),
            "price": _price(v),
            "category": v.get("category", "Item")}


def categories():
    return sorted({e["category"] for e in catalog()})


def shelf(cat):
    return [e for e in catalog() if e["category"] == cat]


def effect_line(e):
    if e.get("category") == ARMOR_CATEGORY:
        return "an armor evolution (the right Child)"
    return EFFECTS.get(e["key"], "a curiosity")


def buy(pet, e):
    """-> (message, sfx)."""
    if pet.bits < e["price"]:
        return (f"Need {e['price']}b — you have {pet.bits}b.", "error")
    pet.spend_bits(e["price"])
    pet.add_item(e["key"])
    return (f"Bought {e['name']}!", "confirm")


def resell_price(e):
    return max(1, e.get("price", 0) // 2)


def sell(pet, e):
    if pet.inventory.get(e["key"], 0) <= 0:
        return ("You don't have that.", "error")
    pet.take_item(e["key"])                    # classic take_item returns None
    pet.bits += resell_price(e)
    return (f"Sold {e['name']} for {resell_price(e)}b.", "confirm")


# ---- town storefronts: the same catalog behind every counter ----

def home_shop_open(pet):
    return True


def town_shop_open(pet, town, is_food):
    return True


def town_shop_hours(pet, town, is_food):
    return (0, 24)


def roll_town_shop(pet, town, is_food):
    """A town counter: fruit/food items on the food shelf, gear on the other."""
    want = ("Food", "Fruit", "Care") if is_food else None
    out = []
    for e in catalog():
        if want is None and e["category"] not in ("Food", "Fruit", "Care"):
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
