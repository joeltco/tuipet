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
from functools import lru_cache
from typing import NamedTuple

from . import data


class Item(NamedTuple):
    """One catalog entry, with its fields NAMED (items refactor P1,
    2026-07-23).  The authored table below stays a plain aligned tuple
    literal -- it reads better as a table and the churn of 37 keyword
    calls buys nothing -- but every CONSUMER now says `.category`
    instead of `v[3]`, which was the actual complaint (scoping board
    P-A).

    Still a tuple, so indexing keeps working.  The first SIX fields are
    the authored contract and must never be reordered -- P2 appended to
    the end, and anything later appends further.

    P2 (2026-07-23) added the last three:

    * `touches` -- the LIVE pet stats this item's `use_item` handler
      moves DIRECTLY.  This is the yardstick for "redo them all to fit
      everything we got going on" (plan §2 goal 2): a pin walks it and
      fails if an item aims at a stat that is dormant or does not exist.
      Side channels are deliberately NOT listed -- `_set_energy` bills
      obedience when a drop lands in the red, and `_disturbed()` bills a
      care mistake, but those belong to those helpers, not to the item.
    * `where` -- "home" (usable from the bag) or "road" (spent on the
      march; the home bag refuses it).  Replaces reading intent out of
      refusal STRINGS (scoping board P-F).
    * `tier` -- rarity slot.  DECLARED, NOT POPULATED: it is the hook the
      distribution arc attaches to (plan §7), and populating it here
      would be inventing an economy nobody has ruled on."""
    name: str
    icon: str
    price: int | None       # None = never sold (grant-only treats)
    category: str
    effect: str             # the text mirroring use_item (see plan §1g)
    flavor: str
    touches: tuple = ()     # LIVE pet stats the handler moves directly
    where: str = "home"     # "home" | "road"
    tier: str | None = None  # distribution arc populates this


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
# -- authored positionally, then wrapped into `Item` (P1) so every reader
# gets named fields.  Keep the alignment: this table is meant to be read.
_AUTHORED = {
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
    # ---- MEDICINE (the two ailments: sick and injured) ----------------------
    "vitamin":         ("Vitamin",         "f:5",  500,  "Medicine", "effort FULL · injury guard", "effort in a capsule"),
    "bandage":         ("Bandage",         "i:80", 300,  "Medicine", "treats an injury", "the second med, restored"),
    # ---- CARE (upkeep: sleep, lights, filth, the mistake slate) -------------
    "sleeping_pill":   ("Sleep Pill",      "f:34", 300,  "Care", "sleep now", "lights out, no argument"),
    "caffeine_pill":   ("Caffeine Pill",   "f:38", 300,  "Care", "bedtime pushed later", "tonight runs long"),
    "music_player":    ("Music Player",    "i:9",  300,  "Care", "wake now, no grudge", "a gentle waking song"),
    "textbook":        ("Textbook",        "i:0",  1500, "Care", "erase ALL care mistakes", "study the slate clean"),
    "port_potty":      ("Port. Potty",     "i:83", 2000, "Care", "clean + auto-clean 24h", "it cleans itself"),
    # ---- TRAINING (the body: effort, weight, drills) ------------------------
    "energy_drink":    ("Energy Drink",    "f:17", 200,  "Training", "energy to FULL", "instant pep"),
    "slim_drink":      ("Slim Drink",      "f:23", 100,  "Training", "weight -10", "the crash diet"),
    "dumbbell":        ("Dumbbell",        "i:7",  300,  "Training", "training +10", "reps in a box"),
    # ---- EVOLUTION (the gates: growth, locks, X, DNA) -----------------------
    "grow_capsule":    ("Grow Capsule",    "i:78", 500,  "Evolution", "growth +120min", "time in a bottle"),
    "anti_evo_chip":   ("Anti-Evo Chip",   "f:32", 1000, "Evolution", "toggle evolution lock", "holds this form"),
    "x_antibody":      ("X-Antibody",      "i:79", 2000, "Evolution", "the X-Antibody takes hold", "the X factor"),
    "dna_crystal":     ("DNA Crystal",     "i:35", 1500, "Evolution", "+10 own-Field DNA banked", "a Field's worth of code"),
    # ---- LEGACY (death and inheritance -- NOT medicine, which is why the
    # old "Medical" name had to go: it never held a med) ---------------------
    # i:64 (the notched-square disk glyph): i:32 is DVPet's own Digimemory
    # sprite, and two catalog entries sharing an icon broke key_for_icon
    # (consistency audit 2026-07-21) -- the floppy wears its own rip now
    "revive_floppy":   ("Rev. Floppy",     "i:64", 2500, "Legacy", "raise the dead", "one more chance"),
    "digimemory":      ("Digimemory",      "i:32", None, "Legacy", "the ancestor's Va·D·Vi", "its data lives on"),
    # ---- PLAY (the shows the engine already ships; small LIVE stat dials:
    # exercise sheds weight, couch time buys energy at a weight price) --------
    "ball":            ("Ball",            "i:3",  100,  "Play", "play! weight -1", "a grand kickabout"),
    "skateboard":      ("Skateboard",      "i:6",  500,  "Play", "ride! weight -2 · energy -1", "shred the living room"),
    "xylophone":       ("Xylophone",       "i:63", 800,  "Play", "a recital · energy +2", "music hath charms"),
    "video_game":      ("Video Game",      "i:65", 600,  "Play", "couch time · energy +2 · weight +1", "one more level…"),
    "television":      ("Television",      "i:10", 1000, "Play", "deep couch · energy +3 · weight +1", "glued to the screen"),
    "bubble_bath":     ("Bubble Bath",     "i:26", 400,  "Play", "washes the filth, with style", "rubber duck included"),
    "cold_shower":     ("Cold Shower",     "i:67", 300,  "Play", "a bracing wake · energy +2", "brrr. effective."),
    # ---- ADVENTURE (the road's own shelf -- cleared maps open it) -----------
    "town_transport":     ("Town Transport",   "i:29", 500,  "Adventure", "on the road: T-warp to a town + rest", "a Birdramon ride"),
    "disaster_transport": ("Disaster Transp.", "i:30", 250,  "Adventure", "on the road: T-dash to the boss + ambush", "a Garudamon ride"),
    "life_recovery":      ("Life Recovery",    "i:27", 1000, "Adventure", "restore adventure lives on the road", "a second wind"),
}

# ---------------------------------------------------------------------------
# WHAT EACH ITEM ACTUALLY MOVES (items refactor P2, 2026-07-23)
#
# Read out of petcare.use_item's handlers one by one -- NOT inferred from
# the effect text, which is the very thing that can drift (plan §1g).
# Every name here is a real Pet dataclass field; test_catalog_touches.py
# proves that and proves none of them is a DORMANT stat.
#
# Omitted on purpose: the indirect billing inside shared helpers.
# `_set_energy` stings obedience when a drop lands in the red and
# `_disturbed()` books a care mistake -- those are the helpers' effects,
# not the item's, and listing them would make every energy item look like
# a discipline item.
_TOUCHES = {
    # ---- FOOD ----
    "fish": ("hunger",),
    "vegetable": ("hunger", "weight"),
    "tuna": ("hunger", "energy"),
    "cake": ("hunger", "energy", "weight"),
    "cupcake": ("hunger", "energy"),
    "cookie": ("hunger", "energy"),
    "candy": ("hunger", "energy"),
    "cheese_burger": ("hunger", "weight", "care_mistakes"),
    "giga_meal": ("hunger", "energy", "weight"),
    "steak": ("hunger", "full_until"),
    "poison_mushroom": ("dead",),          # _die(): the one lethal entry
    # ---- CARE ----
    "energy_drink": ("energy",),
    "slim_drink": ("weight",),
    "vitamin": ("strength", "vitamin_lapse"),
    "bandage": ("injured", "inj_length"),
    "sleeping_pill": ("asleep", "lights", "nap"),
    "caffeine_pill": ("sleep_lapse",),     # or the _bed_postpone_t grace channel
    "music_player": ("asleep", "lights", "nap", "awake_lapse"),
    "textbook": ("care_mistakes",),
    "port_potty": ("poop", "poop_sizes", "auto_clean_until"),
    # ---- GROWTH ----
    "dumbbell": ("stage_trainings",),
    "grow_capsule": ("stage_seconds",),
    "anti_evo_chip": ("evo_blocked",),
    "x_antibody": ("x_antibody",),
    "dna_crystal": ("dna_owned",),
    "revive_floppy": ("dead",),
    "digimemory": ("vaccine", "data_power", "virus", "digimemory"),
    # ---- TOYS ----
    "ball": ("weight",),
    "skateboard": ("weight", "energy"),
    "xylophone": ("energy",),
    "video_game": ("energy", "weight"),
    "television": ("energy", "weight"),
    "bubble_bath": ("poop", "poop_sizes"),
    "cold_shower": ("energy", "asleep"),   # runs its OWN disturb, so: asleep
    # ---- ADVENTURE ----
    # Empty by design: from the HOME bag these three only refuse.  Their
    # real work is adventure-run state (the march's location, its lives),
    # which is not Pet state and does not belong in this namespace.
    # `where="road"` is what carries that meaning.
    "town_transport": (),
    "disaster_transport": (),
    "life_recovery": (),
}

_ROAD_ONLY = frozenset({"town_transport", "disaster_transport",
                        "life_recovery"})

# THE catalog: the authored table, field-named.  Everything downstream
# reads this, never `_AUTHORED`.
CATALOG = {
    _k: Item(*_v,
             touches=_TOUCHES.get(_k, ()),
             where="road" if _k in _ROAD_ONLY else "home")
    for _k, _v in _AUTHORED.items()
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
    _BY_ICON.setdefault(_v.icon, _k)


def key_for_icon(icon):
    """The CATALOG key whose sprite is `icon`, or None (unmapped loot)."""
    return _BY_ICON.get(icon)

# compat views over the one table (shelf text / icons / tests import these)
EFFECTS = {k: v.effect for k, v in CATALOG.items()}
ICON_KEYS = {k: v.icon for k, v in CATALOG.items()}
FLAVORS = {k: v.flavor for k, v in CATALOG.items()}   # the dossier taglines

# foods ride the EAT fx on their DVPet strip; toys ride their canon itemfx
# script (the AnimationType painters shipped since the DVPet era)
FOOD_KEYS = frozenset(k for k, v in CATALOG.items() if v.category == "Food")
# Items whose use has its OWN door and must never be hijacked by a
# generic item show: the memory chip's inherit flow, the two road
# transports and the road's Life Recovery (all spent on the march), and
# the Revive Floppy -- its canon type is Play, but it is used on a DEAD
# pet and the bag is unreachable at the grave, so that show could only
# ever be wrong or unplayable (item-show audit 2026-07-23).
_OWN_FLOW = frozenset({"digimemory", "town_transport", "disaster_transport",
                       "life_recovery", "revive_floppy"})


def item_is_eaten(key):
    """True when USING this item should play the EAT show.

    The canon rule is the SHEET (item-show audit 2026-07-23, Joel "do
    the eat show for the consumables too"): foods.csv carries no
    AnimationType column at all, because eating IS the animation --
    exactly how the pill already works ("the pill is EATEN, the
    source's EATING action, same as meat", pill-anim fix 2026-07-18).
    So every `f:` item eats: the 11 foods as before, plus the six
    food-sheet CONSUMABLES that used to flash bare text -- both
    drinks, both pills, the vitamin and the anti-evo chip.  `i:`
    items take a script instead (see item_script)."""
    return ICON_KEYS.get(key, "").startswith("f:")


def item_script(key):
    """The canon SHOW for a catalog item, or None.

    ONE SOURCE (item-show audit 2026-07-23, Joel: "is all of that
    already wired in?"): items.csv carries an AnimationType for every
    row, and our icon key `i:N` IS that row id -- so the mapping is
    free.  This replaces TOY_SCRIPTS, a 7-entry hand-map that
    duplicated the column and left 19 items with ripped art and no
    show at all.  Returns None for anything without an implemented
    script, for own-door items, and for `f:` consumables -- food-sheet
    items are EATEN (foods.csv has no AnimationType at all) and ride
    the eat fx, exactly like the pill."""
    if key in _OWN_FLOW:
        return None
    icon = ICON_KEYS.get(key, "")
    if not icon.startswith("i:"):
        return None
    from . import itemfx
    act = (data.consumable_by_key(icon) or {}).get("action") or ""
    return act if act in itemfx.SCRIPTS else None

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
    for k, v in CATALOG.items():
        if v.price is not None and adventure_open(k, prog):  # road shelf gated by maps
            out.append({"key": k, "name": v.name, "price": v.price,
                        "category": v.category})
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
        return {"key": key, "name": c.name,
                "price": c.price if c.price is not None else 100,
                "category": c.category}
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
CATEGORY_ORDER = ("Food", "Medicine", "Care", "Training", "Play",
                  "Evolution", "Legacy",
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
    # a town-priced bag row carries its LOCAL sell price (buy-low/sell-high,
    # shops arc 2026-07-21); home keeps the flat half
    if "sell_price" in e:
        return max(1, int(e["sell_price"]))
    return max(1, e.get("price", 0) // 2)


def sell(pet, e):
    if pet.inventory.get(e["key"], 0) <= 0:
        return ("You don't have that.", "error")
    pet.take_item(e["key"])                    # classic take_item returns None
    pet.bits += resell_price(e)
    return (f"Sold {e['name']} for {resell_price(e)}b.", "confirm")


# (the OLD town storefront chain -- home_shop_open / town_shop_open /
# town_shop_hours / roll_town_shop / slot_label / slot_info / sell_info /
# purchase_price + Pet.buy_slot -- CUT 2026-07-19, Joel: "cut the town
# chain".  The hours/rolled-slot machine stays dead.  What follows is the
# NEW town economy Joel ordered 2026-07-21 ("shops, town shops, deals"):
# deterministic, no rolls, no opening hours -- the authored data driving
# tuipet-idiom systems.)

# -- the town economy (shops arc, 2026-07-21) --------------------------------
# towns.csv override lists -> shopConsumable.csv econ rows -> CATALOG
# identities.  The 26 towns split into TWO authored stock families (a shared
# items shelf + two food families) -- that split IS the trade map: a town
# pays DEMAND rates for goods it doesn't stock.
TOWN_DEMAND_NUM, TOWN_DEMAND_DEN = 7, 10   # unstocked goods: towns pay 70%
#                                            (home pays 50%; canon towns pay
#                                            price//ResellFactor for their
#                                            OWN stock -- they have plenty)
TOWN_DAILY_CAP = 3        # tuipet's own per-(town,item,day) purchase bound.
#                           DVPet's 25-50-steak crates served ITS economy;
#                           against tuipet's catalog even ratio-scaled deal
#                           margins would compound into a printer at 50/day.

# PRICE LAW: a town price is the AUTHORED RATIO scaled to tuipet's catalog --
# catalog_price * row_price / DefaultPrice (the Default* cols are DVPet's own
# home economy, so the ratio IS the authored "towns discount steak 25%, halve
# chips, sell furniture at par" structure).  Raw row prices against tuipet's
# repriced catalog were money printers (375b steak vs 2000b catalog: +625
# per home flip); the ratio keeps every flip at-or-below water and makes
# DEALS the only trade window -- by design.


def _today_ordinal(today=None):
    from . import tournament
    d = today if today is not None else tournament._today()
    return d.toordinal()


@lru_cache(maxsize=1)
def _town_maps():
    """town_id -> the MAP whose zone hosts the town (the road's own
    geography; item diversity audit 2026-07-23)."""
    from . import data
    out = {}
    for mp in data.load_maps():
        for z in mp["zones"]:
            for _lo, _hi, tid in z.get("towns", ()):
                out[tid] = z["map"]
    return out


# P4 (item diversity audit 2026-07-23, Joel: "do it all"): each MAP's
# towns carry ONE regional specialty beyond the 2-variant authored base,
# so the five maps read differently before the guest good even lands.
# Late maps sell the premium tier -- map 4 (the hardest region) is where
# the Revive Floppy waits.
_MAP_SPECIALTY = {1: "cake", 2: "xylophone", 3: "x_antibody",
                  4: "revive_floppy", 5: "vitamin"}


def _econ_stub(key):
    """A synthetic econ row for non-authored shelf rows (guest/regional):
    catalog price, standard factors, capped stock -- no money printer."""
    v = CATALOG[key]
    return {"price": v.price, "sale_factor": 2, "resell_factor": 2,
            "max_stock": 2, "is_food": v.category == "Food",
            "consumable_id": -1}


def _base_rows(town_id):
    """The town's authored shelf + its map's regional specialty:
    [(sid, catalog_key, econ_row, local_price)] in list order (items shelf
    first, then the food family).  local_price is the PRICE-LAW ratio (see
    above); rows whose consumable has no living CATALOG identity are
    dropped -- their systems (chips, furniture) aren't in tuipet, and
    dormant data stays dormant."""
    from . import data
    t = data.load_towns().get(town_id)
    if not t:
        return []
    ov = data.load_shop_overrides()
    foods, items = data._load_consumables()
    rows = []
    for sid in t["items_override"] + t["foods_override"]:
        o = ov.get(sid)
        if not o or o["price"] <= 0:
            continue
        icon = ("f:" if o["is_food"] else "i:") + str(o["consumable_id"])
        k = key_for_icon(icon)
        if not k:
            continue
        e = entry(k)
        default = ((foods if o["is_food"] else items).get(o["consumable_id"])
                   or {}).get("price", 0)
        if e and default > 0:
            local = max(1, round(e["price"] * o["price"] / default))
        else:
            local = o["price"]
        rows.append((sid, k, o, local))
    sk = _MAP_SPECIALTY.get(_town_maps().get(town_id))
    if sk and sk not in {k for _sid, k, _o, _p in rows}:
        rows.append((f"regional:{town_id}", sk, _econ_stub(sk),
                     CATALOG[sk].price))
    return rows


@lru_cache(maxsize=1)
def _guest_deal():
    """town_id -> its standing guest good, dealt WITHOUT replacement
    across ALL towns (item diversity audit 2026-07-23: the old per-town
    crc32 pick birthday-collided -- 8 items served 2-3 towns each, and
    towns 11+12 were byte-identical shops).  The pool is the UNGATED
    priced catalog minus Adventure (its map-clear gate must hold) and
    minus the Poison Mushroom (a town's one signature good is never a
    trap -- the raid-pool rule).  26 towns, 28 candidates: every town's
    guest is unique game-wide.  crc32-ordered, so the deal is STABLE --
    a town's character stays permanent (the guest-good law); the daily
    deal already rotates."""
    import zlib
    pool = [k for k, v in CATALOG.items()
            if v.price is not None and v.category != "Adventure"
            and k != "poison_mushroom"]
    pool.sort(key=lambda k: zlib.crc32(f"guest2:{k}".encode()))
    taken, out = set(), {}
    for tid in sorted(_town_maps()):
        stocked = {k for _sid, k, _o, _p in _base_rows(tid)}
        pick = (next((k for k in pool
                      if k not in taken and k not in stocked), None)
                or next((k for k in pool if k not in stocked), None))
        if pick:
            taken.add(pick)
            out[tid] = pick
    return out


def _town_rows(town_id):
    """The full town shelf: authored base + regional specialty + the
    standing guest good (gameplay polish #24; re-dealt collision-free in
    the item diversity audit 2026-07-23)."""
    rows = _base_rows(town_id)
    gk = _guest_deal().get(town_id)
    if gk:
        rows.append((f"guest:{town_id}", gk, _econ_stub(gk),
                     CATALOG[gk].price))
    return rows


def town_deal_sid(town_id, today=None):
    """The town's ONE rotating daily deal: crc32-seeded on (town, day) --
    stable all day, different tomorrow, different next town."""
    import zlib
    rows = _town_rows(town_id)
    if not rows:
        return None
    i = zlib.crc32(f"{town_id}:{_today_ordinal(today)}".encode()) % len(rows)
    return rows[i][0]


def _stocked(town_id, key):
    """This town's shelf row for `key`, or None (the demand test)."""
    for _sid, k, o, local in _town_rows(town_id):
        if k == key:
            return o, local
    return None


def _town_taken(pet, today=None):
    """The day's purchase ledger for this pet ({} once the day turns)."""
    tb = getattr(pet, "town_bought", None) or {}
    return tb if tb.get("day") == _today_ordinal(today) else {}


def town_stock(town_id, today=None, pet=None):
    """The town shop's shelves as ready entries [{key,name,price,category,
    base_price,deal,left,town_id}].  The day's rotating deal (and, on a
    FESTIVAL, every row -- the festival market) sells at the canon
    checkSale price: price // SaleFactor.  `left` is the authored maxStock
    minus the day's take (the anti-pump: town prices are DVPet's own,
    far under the catalog -- the daily cap is what makes the demand
    resale a treat instead of a printer)."""
    from . import adventure
    deal = town_deal_sid(town_id, today)
    fest = bool(adventure.active_holiday(today))
    taken = _town_taken(pet, today) if pet is not None else {}
    out = []
    for sid, k, o, local in _town_rows(town_id):
        e = entry(k)
        if not e:
            continue
        on = fest or sid == deal
        price = local // max(1, o["sale_factor"]) if on else local
        cap = min(o["max_stock"], TOWN_DAILY_CAP)
        left = max(0, cap - int(taken.get(f"{town_id}:{k}", 0)))
        out.append(dict(e, price=max(1, price), base_price=local,
                        deal=on, left=left, town_id=town_id))
    return out


def town_egg_rows(town_id):
    """The town's digitama band as SHOP ROWS (shops-look-the-same,
    2026-07-22: Joel — "the egg tabs in town shops are different than the
    normal shops, why arent these things modulized").  Same entry shape
    the shelf renders everywhere; `egg_idx` rides the existing menu icon
    plumbing (shop eggs draw their real egg frames)."""
    from . import egg as egg_mod, persistence
    owned = persistence.get_eggs_owned()
    return [{"key": f"egg:{i}", "name": egg_mod.hatch_name(i)[:18],
             "price": egg_price(i), "category": "Digitama",
             "egg_idx": i, "owned": i in owned, "town_id": town_id}
            for i in town_egg_stock(town_id)]


def town_egg_buy(pet, idx):
    """Buy a digitama outright (bits -> persistence.egg_own) -> (msg, sfx).
    THE single buy path — the town egg panel and the shop's Eggs tab both
    call here (single-source law)."""
    from . import egg as egg_mod, persistence
    if idx in persistence.get_eggs_owned():
        return ("You already own that egg.", "error")
    price = egg_price(idx)
    if not pet.spend_bits(price):
        return (f"{price}b — not enough bits.", "error")
    persistence.egg_own(idx)
    return (f"Bought the {egg_mod.hatch_name(idx)} egg — "
            "it's on your carousel!", "reward")


def town_buy(pet, e, today=None):
    """A town counter purchase: blocked once the day's authored stock is
    gone, recorded in the pet's daily ledger otherwise."""
    if e.get("left", 0) <= 0:
        return ("Sold out today — come back tomorrow.", "error")
    msg, sfx = buy(pet, e)
    if sfx == "confirm":
        day = _today_ordinal(today)
        tb = getattr(pet, "town_bought", None) or {}
        if tb.get("day") != day:
            tb = {"day": day}                  # a new day sweeps the ledger
        k = f"{e['town_id']}:{e['key']}"
        tb[k] = int(tb.get(k, 0)) + 1
        pet.town_bought = tb
    return (msg, sfx)


def town_sell_price(key, town_id):
    """Buy-low/sell-high: a good this town STOCKS resells at the canon
    local_price // ResellFactor (it has plenty); one it DOESN'T stock is
    in DEMAND -- 70% of catalog price, better than home's half.  The
    trade window: buy a family's exclusive ON DEAL, carry it to the
    OTHER family's towns."""
    hit = _stocked(town_id, key)
    if hit is not None:
        o, local = hit
        return max(1, local // max(1, o["resell_factor"]))
    e = entry(key)
    if not e:
        return 1
    return max(1, e["price"] * TOWN_DEMAND_NUM // TOWN_DEMAND_DEN)
