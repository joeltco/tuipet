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


# ============================ THE TUIPET CATALOG ============================
# Authored 2026-07-18 (Joel: "we can pretty much make anything we want. i
# need you to make tuipet items" / "you can make the items whatever you
# want using the sprites").  The law of the set: DSprite is the mechanics
# GRAMMAR, DVPet is the ART -- every entry wears a real DVPet atlas strip
# (all 59 foods + 84 items carry 4-frame rips; zero placeholders), and
# every effect lands on a meter that is LIVE today.  vitems.json stays a
# pristine rip: it now feeds only the 11 Digimentals; the consumable shelf
# is THIS table.  price None = never sold (birthday-only treats).
# key: (name, icon, price, category, effect-text mirroring use_item, tagline)
CATALOG = {
    # ---- FOOD (eaten on the LCD through their own 4-frame strips) ----------
    "fish":            ("Fish",            "f:1",  50,   "Food", "hunger +1", "the everyday catch"),
    "vegetable":       ("Vegetable",       "f:3",  150,  "Food", "hunger +1 · weight -1", "crunchy diet fare"),
    "tuna":            ("Tuna",            "f:14", 400,  "Food", "hunger +2 · energy +1", "a hearty catch"),
    "cake":            ("Cake",            "f:6",  300,  "Food", "hunger +1 · energy +2 · weight +2", "a celebration slice"),
    "cheese_burger":   ("Cheese burger",   "f:57", 50,   "Food", "fills belly · weight +4 · a care mistake", "greasy, regrettable"),
    "giga_meal":       ("Giga Meal",       "f:28", 800,  "Food", "fills belly · energy +4 · weight +6", "a feast fit for a Mega"),
    "steak":           ("Steak",           "f:8",  2000, "Food", "fills belly · 12h satiety", "the premium table"),
    "poison_mushroom": ("Poison Mushroom", "f:13", 200,  "Food", "DO NOT FEED", "it does look delicious"),
    "cupcake":         ("Cupcake",         "f:55", None, "Food", "hunger +1 · energy +1", "a birthday's reward"),
    "cookie":          ("Cookie",          "f:54", None, "Food", "hunger +1 · energy +1", "a birthday's treat"),
    "candy":           ("Candy",           "f:7",  None, "Food", "hunger +1 · energy +1", "a consolation sweet"),
    # ---- CARE ---------------------------------------------------------------
    "energy_drink":    ("Energy Drink",    "f:17", 200,  "Care", "energy to FULL", "instant pep"),
    "slim_drink":      ("Slim Drink",      "f:23", 100,  "Care", "weight -10", "the crash diet"),
    "vitamin":         ("Vitamin",         "f:5",  500,  "Care", "effort to FULL", "effort in a capsule"),
    "sleeping_pill":   ("Sleep Pill",      "f:34", 300,  "Care", "sleep now", "lights out, no argument"),
    "caffeine_pill":   ("Caffeine Pill",   "f:38", 300,  "Care", "bedtime pushed later", "tonight runs long"),
    "music_player":    ("Music Player",    "i:9",  300,  "Care", "wake now, no grudge", "a gentle waking song"),
    "textbook":        ("Textbook",        "i:0",  1500, "Care", "erase ALL care mistakes", "study the slate clean"),
    "port_potty":      ("Port. Potty",     "i:83", 2000, "Care", "clean + auto-clean 24h", "it cleans itself"),
    # ---- GROWTH -------------------------------------------------------------
    "dumbbell":        ("Dumbbell",        "i:7",  300,  "Evolution", "training +10", "reps in a box"),
    "grow_capsule":    ("Grow Capsule",    "i:78", 500,  "Evolution", "growth +120min", "time in a bottle"),
    "anti_evo_chip":   ("Anti-Evo Chip",   "f:32", 1000, "Evolution", "toggle evolution lock", "holds this form"),
    "x_antibody":      ("X-Antibody",      "i:79", 2000, "Evolution", "the X-Antibody takes hold", "the X factor"),
    "dna_crystal":     ("DNA Crystal",     "i:35", 1500, "Evolution", "+10 own-Field DNA banked", "a Field's worth of code"),
    # i:64 (the notched-square disk glyph): i:32 is DVPet's own Digimemory
    # sprite, and two catalog entries sharing an icon broke key_for_icon
    # (consistency audit 2026-07-21) -- the floppy wears its own rip now
    "revive_floppy":   ("Rev. Floppy",     "i:64", 2500, "Medical", "raise the dead", "one more chance"),
    "digimemory":      ("Digimemory",      "i:32", None, "Medical", "the ancestor's Va·D·Vi + lifespan", "its data lives on"),
    # ---- TOYS (the shows the engine already ships; small LIVE stat dials:
    # exercise sheds weight, couch time buys energy at a weight price) --------
    "ball":            ("Ball",            "i:3",  100,  "Toy", "play! weight -1", "a grand kickabout"),
    "skateboard":      ("Skateboard",      "i:6",  500,  "Toy", "ride! weight -2 · energy -1", "shred the living room"),
    "xylophone":       ("Xylophone",       "i:63", 800,  "Toy", "a recital · energy +2", "music hath charms"),
    "video_game":      ("Video Game",      "i:65", 600,  "Toy", "couch time · energy +2 · weight +1", "one more level…"),
    "television":      ("Television",      "i:10", 1000, "Toy", "deep couch · energy +3 · weight +1", "glued to the screen"),
    "bubble_bath":     ("Bubble Bath",     "i:26", 400,  "Toy", "washes the filth, with style", "rubber duck included"),
    "cold_shower":     ("Cold Shower",     "i:67", 300,  "Toy", "a bracing wake · energy +2", "brrr. effective."),
    # ---- ADVENTURE (the road's own shelf -- cleared maps open it) -----------
    "town_transport":     ("Town Transport",   "i:29", 500,  "Adventure", "on the road: T-warp to a town + rest", "a Birdramon ride"),
    "disaster_transport": ("Disaster Transp.", "i:30", 250,  "Adventure", "on the road: T-dash to the boss + ambush", "a Garudamon ride"),
    "life_recovery":      ("Life Recovery",    "i:27", 1000, "Adventure", "restore adventure lives on the road", "a second wind"),
}

# the road's shelf unlocks by CLEARING MAPS (the profile `maps` set): once a
# tamer has beaten a continent, the transports/recovery it needs go on sale.
# key -> how many maps must be cleared.  Same earned-access rule as the eggs.
ADVENTURE_GATES = {
    "town_transport": 1, "disaster_transport": 1, "life_recovery": 2,
}


def adventure_open(key, prog=None):
    """Is this road-shelf item unlocked (enough maps cleared)?  Non-gated keys
    are always open."""
    need = ADVENTURE_GATES.get(key)
    if need is None:
        return True
    if prog is None:
        from . import persistence
        prog = persistence.get_progress()
    return len(prog.get("maps", ()) or ()) >= need


# sprite icon (i:/f:) -> the CATALOG key that wears it: adventure loot is
# authored by data id, but the bag/use system speaks CATALOG keys (the same
# "the bag could neither show nor use" trap the i:32 heal fixed) -- so found
# loot maps back through this to a real, usable entry.
_BY_ICON = {}
for _k, _v in CATALOG.items():
    _BY_ICON.setdefault(_v[1], _k)


def key_for_icon(icon):
    """The CATALOG key whose sprite is `icon`, or None (unmapped loot)."""
    return _BY_ICON.get(icon)

# compat views over the one table (shelf text / icons / tests import these)
EFFECTS = {k: v[4] for k, v in CATALOG.items()}
ICON_KEYS = {k: v[1] for k, v in CATALOG.items()}
FLAVORS = {k: v[5] for k, v in CATALOG.items()}   # the dossier taglines

# foods ride the EAT fx on their DVPet strip; toys ride their canon itemfx
# script (the AnimationType painters shipped since the DVPet era)
FOOD_KEYS = frozenset(k for k, v in CATALOG.items() if v[3] == "Food")
TOY_SCRIPTS = {"ball": "Bounce", "skateboard": "Ride",
               "xylophone": "InteractXylophone", "video_game": "Play",
               "television": "InteractTelevision", "bubble_bath": "Bathe",
               "cold_shower": "Shower"}

# old-catalog keys -> their heirs (the save-heal maps bags 1:1 on load;
# nobody loses goods when the shelf turns over)
LEGACY_KEYS = {
    "best_fruit": "tuna", "normal_fruit": "fish", "worst_fruit": "vegetable",
    "deadly_fruit": "poison_mushroom", "junk_food": "cheese_burger",
    "premium_meat": "steak", "super_carrot": "slim_drink",
    "care_mistake_eraser": "textbook", "alarm_clock": "music_player",
    "time_gear": "grow_capsule", "training_pack": "dumbbell",
    "poop_clean_pill": "port_potty",
    # the inheritance chip circulated under its raw icon key -- a key the
    # bag could neither show nor use (gameplay audit 2026-07-19)
    "i:32": "digimemory",
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


# --- per-town egg market (Joel 2026-07-21: "different towns sell different
# eggs -- all shops feel unique").  Each town stocks a DISTINCT band of the
# earnable digitama, shown as the real 8x8 egg thumbnails; buying one owns it
# outright (bits -> persistence.egg_own).  Eggs still unlock FREE by condition
# elsewhere -- a town is the road shortcut, priced.
EGG_STOCK_PER_TOWN = 6


def _sellable_eggs():
    """The digitama a town may stock: every egg that ISN'T a free starter
    (the five START babies you already own)."""
    from . import egg as egg_mod, data
    rules = data.load_egg_unlock()
    return [i for i in range(egg_mod.count())
            if not (rules.get(i) or {}).get("start")]


def town_egg_stock(town_id, count=EGG_STOCK_PER_TOWN):
    """The DISTINCT set of eggs THIS town sells -- a stable band over the
    earnable digitama, rotated by town so no two town shops feel the same."""
    pool = _sellable_eggs()
    if not pool:
        return []
    count = min(count, len(pool))
    start = (int(town_id) * count) % len(pool)
    return [pool[(start + i) % len(pool)] for i in range(count)]


def egg_price(idx):
    """A town egg's bit price -- earned eggs are a treat, so the buy-outright
    shortcut costs real bits.  Starters (never stocked) are free."""
    from . import data
    rule = data.load_egg_unlock().get(idx) or {}
    return 0 if rule.get("start") else 800

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
    """Only goods Pet.use_item can actually APPLY are sold.  Since the
    TUIPET catalog (2026-07-18) the consumables are authored in CATALOG;
    vitems contributes only the Digimentals (its theme_* skins,
    storage_drive and retired consumables never reach the shelf)."""
    return category == ARMOR_CATEGORY or key in CATALOG


def catalog():
    """Every buyable entry: [{key, name, price, category}], price order.
    The consumable shelf is the authored CATALOG (price None = unsold);
    the 11 Digimentals still come from vitems.json.  A Digimental whose
    wave isn't reached is SEALED: it stays off the shelf entirely (the
    egg-carousel rule), though entry() still resolves it so an
    already-owned one renders in the bag."""
    from . import persistence
    prog = persistence.get_progress()
    out = []
    for k, (name, _icon, price, cat, _eff, _fl) in CATALOG.items():
        if price is not None and adventure_open(k, prog):   # road shelf gated by maps
            out.append({"key": k, "name": name, "price": price,
                        "category": cat})
    for k, v in data.load_vitems().items():
        if isinstance(v, dict) and v.get("category") == ARMOR_CATEGORY \
                and digimental_open(k, prog):
            out.append({"key": k, "name": v.get("name", k),
                        "price": _price(v),
                        "category": ARMOR_CATEGORY})
    out.sort(key=lambda e: (e["category"], e["price"], e["name"]))
    return out


def entry(key):
    """Resolve any key: the authored CATALOG first (an unsold treat still
    renders in the bag at a nominal resale), then vitems (Digimentals)."""
    c = CATALOG.get(key)
    if c is not None:
        name, _icon, price, cat, _eff, _fl = c
        return {"key": key, "name": name,
                "price": price if price is not None else 100,
                "category": cat}
    v = data.load_vitems().get(key)
    if not isinstance(v, dict):
        return None
    return {"key": key, "name": v.get("name", key),
            "price": _price(v),
            "category": v.get("category", "Item")}


def categories():
    have = {e["category"] for e in catalog()}
    out = [c for c in CATEGORY_ORDER if c in have]
    return out + sorted(have - set(out))


def shelf(cat):
    return [e for e in catalog() if e["category"] == cat]


# shelf tabs in PLAY order -- everyday care first, the relics last (shop
# polish 2026-07-17: the old alphabetical order opened the shop on a
# two-item Armor-Spirit tab).  Unknown categories append alphabetically.
CATEGORY_ORDER = ("Care", "Food", "Evolution", "Medical", "Toy",
                  "Adventure", ARMOR_CATEGORY)


def crest_answer(pet, key):
    """The forms THIS pet's armor jump would land right now -- the same
    evolution.check gate the crest egg runs on use (display only, no
    roll).  [] when nothing answers (not a crest key, egg/dead, gates
    unmet)."""
    from . import evolution
    from .pet import Pet
    item_id = Pet._CREST_IDS.get(key, -1)
    if (item_id < 0 or pet is None or getattr(pet, "num", -1) < 0
            or getattr(pet, "dead", False) or pet.stage == "Egg"):
        return []
    _, by_num = data.load_sprites()
    return sorted({by_num[t]["name"]
                   for t in data.load_evolutions().get(pet.num, [])
                   if t in by_num and not data.is_placeholder(t)
                   and evolution.check(pet, t, item=item_id)})


# the sealed-wave tease texts, keyed by gate -- live numbers filled from
# persistence.get_progress() (the egg carousel's locked-hint pattern).
# Kept SHORT: they ride the 38-col shop footer, and footers never marquee.
_WAVE_TEASE = {
    ("armor_evos", 1): "your 1st armor evo wakes the crest 5",
    ("wins", 25): "wins {have}/25 wake Light & Kindness",
    ("raids", 2): "raids {have}/2 wake Miracles",
    ("max_gen", 5): "generation {have}/5 wakes Destiny",
}


def wave_status(prog=None):
    """(sealed_count, closest-wave tease) from live DIGIMENTAL_GATES
    progress -- (0, '') once every relic is on the shelf."""
    if prog is None:
        from . import persistence
        prog = persistence.get_progress()
    sealed = [g for k, g in DIGIMENTAL_GATES.items()
              if g is not None and not digimental_open(k, prog)]
    if not sealed:
        return 0, ""

    def ratio(g):
        sig, need = g
        return min(1.0, int(prog.get(sig, 0)) / need)
    sig, need = max(set(sealed), key=ratio)
    have = min(int(prog.get(sig, 0)), need)
    tease = _WAVE_TEASE.get((sig, need), "more relics stir out there")
    return len(sealed), tease.format(have=have, need=need)


def effect_line(e):
    if e.get("category") == ARMOR_CATEGORY:
        return "an armor evolution (the right Child)"
    k = e["key"]
    eff = EFFECTS.get(k, "a curiosity")
    fl = FLAVORS.get(k)
    # the dossier speaks effect AND character ("polish up the shop
    # descriptions" 2026-07-18) -- but the info block holds exactly two
    # 26-col rows, so a long effect keeps the stage to itself
    if fl:
        import textwrap
        joined = f"{eff} — {fl}"
        if len(textwrap.wrap(joined, 26)) <= 2:
            return joined
    return eff


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


# (the town storefront chain -- home_shop_open / town_shop_open /
# town_shop_hours / roll_town_shop / slot_label / slot_info / sell_info /
# purchase_price + Pet.buy_slot -- CUT 2026-07-19, Joel: "cut the town
# chain".  Towns and their counters died with adventure in v0.5.8; these
# served screens that no longer exist, and nothing live called them.)
