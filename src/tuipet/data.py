"""Load game data. Roster / sprites / stages / evolution graph now come from the
authentic DM20 corpus via `species` + `data/dm20_sprites.json.gz` (DVPet 16x16 art in
native DVPet frame order). The remaining DVPet CSVs (foods/enemies/care) are still read here until those
subsystems are rebuilt."""
from __future__ import annotations
import csv
import gzip
import json
import os
import re
from functools import lru_cache
from . import species

_HERE = os.path.dirname(__file__)
_DATA = os.path.join(_HERE, "data")
_RAW = _DATA  # bundled CSVs (foods/enemies/care) live alongside sprites
_ATLAS = os.path.join(_DATA, "dm20_sprites.json.gz")

# Animation roles + growth order now come from the authentic DM20 atlas (DVPet-native
# frame order). See species.ROLES / species.STAGE_ORDER.
ROLES = species.ROLES
MIRROR_ROLES = species.MIRROR_ROLES
STAGE_ORDER = species.STAGE_ORDER        # Baby I .. Super Ultimate (authentic, not anime tiers)
STAGE_RANK = species.STAGE_RANK          # ["Egg"] + STAGE_ORDER


def stage_rank(stage):
    return species.stage_rank(stage)


def pretty_field(name):
    """Display form of a CamelCase Field value (the data keeps it joined for
    matching): 'NightmareSoldier' -> 'Nightmare Soldier'. 'None'/single words
    are unchanged."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name or "")


PLACEHOLDER_NUMS: set[int] = set()


def _content_fill(frame):
    rows = [r for r in frame if "1" in r]
    if not rows:
        return 0.0
    left = min(r.find("1") for r in rows)
    right = max(r.rfind("1") for r in rows)
    w = right - left + 1
    return sum(r[left:right + 1].count("1") for r in rows) / (w * len(rows))


@lru_cache(maxsize=1)
def load_sprites():
    """The authentic DM20 sprite atlas (DVPet 16x16 art, native frame order), keyed by species num."""
    from . import placeholder
    with gzip.open(_ATLAS, "rt", encoding="utf-8") as fh:
        data = json.load(fh)["sprites"]
    for rec in data:
        frames = rec["frames"]
        first = next((f for f in frames if f), None)
        if first is None:                       # no sprite extracted (the 6 unsourceable mons)
            PLACEHOLDER_NUMS.add(rec["num"])
            rec["frames"], rec["w"], rec["h"] = placeholder.FRAMES, placeholder.W, placeholder.H
            rec["_placeholder"] = True
        else:
            # fill any empty role frame with the first real one so nothing renders blank
            rec["frames"] = [f if f else first for f in frames]
    by_num = {d["num"]: d for d in data}
    return data, by_num


def is_placeholder(num):
    load_sprites()
    return num in PLACEHOLDER_NUMS


@lru_cache(maxsize=1)
def load_evolutions():
    """num -> list of target nums it can evolve into (from the species evolution graph)."""
    by_id = {r["id"]: r["num"] for r in species.roster()}
    evo = {}
    for r in species.roster():
        targets = [by_id[e["to_id"]] for e in r["evolves_to"]
                   if e.get("to_id") in by_id]
        if targets:
            evo[r["num"]] = targets
    return evo


@lru_cache(maxsize=1)
def load_foods():
    path = os.path.join(_RAW, "foods.csv")
    foods = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            try:
                foods.append({
                    "name": row["Name"],
                    "hunger": int(row["Hunger"] or 0),
                    "weight": int(row["Weight"] or 0),
                    "mood": int(row["Mood"] or 0),
                    "energy": int(row["Energy"] or 0),
                    "strength": int(row["Strength"] or 0),
                    "obedience": int(row["Obedience"] or 0),
                    "enthusiasm": int(row["Enthusiasm"] or 0),
                    "category": (row.get("Type") or "").strip(),
                    "protein": int(row.get("Proteins") or 0),
                    "vitamin_n": int(row.get("Vitamins") or 0),
                    "mineral": int(row.get("Minerals") or 0),
                })
            except (KeyError, ValueError):
                continue
    return foods


def next_stage(stage):
    try:
        i = STAGE_ORDER.index(stage)
    except ValueError:
        return None
    return STAGE_ORDER[i + 1] if i + 1 < len(STAGE_ORDER) else None


def evolution_targets(num, stage):
    """Real evolution targets whose stage is the next stage up (with sprites)."""
    _, by_num = load_sprites()
    evo = load_evolutions()
    want = next_stage(stage)
    out = []
    for t in evo.get(num, []):
        rec = by_num.get(t)
        if rec and (want is None or rec["stage"] == want):
            out.append(t)
    # fall back to any next-stage creature if the graph has no usable target
    if not out and want:
        out = [n for n, rec in by_num.items() if rec["stage"] == want]
    return out

# Food taste categories (still used by the feeding/taste system in pet.py).
FOOD_CATEGORIES = ("Meat", "Fish", "Veg", "Fruit", "Med", "Junk", "Grain", "Dairy")


@lru_cache(maxsize=1)
def load_orbs():
    with gzip.open(os.path.join(_DATA, "orbs.json.gz")) as fh:
        return json.load(fh)


def attack_orb(num, attribute, power):
    """The generic per-attribute battle orb at the power tier floor(power/25). Authentic
    mono v-pet battle has no per-mon special attacks — the projectile is purely the
    attribute, scaled by power."""
    orbs = load_orbs()
    tiers = orbs["generic"].get(attribute) or orbs["generic"]["Vaccine"]
    t = max(0, min(int(power) // 25, len(tiers) - 1))
    return tiers[t] or next((x for x in tiers if x), None)


@lru_cache(maxsize=1)
def load_requirements():
    """Per-mon evolution/physiology gates were DVPet digimon.csv data (keyed by DVPet
    nums, absent for the authentic species roster). The engine now reads everything
    from `species` + the corpus, so this is an empty map — every `.get(num, {})` caller
    falls back to its sensible default. (digimon.csv is gone.)"""
    return {}


# ---------------------------------------------------------------------------
# Battle enemies (parsed from enemies.csv).  Each enemy references a Digimon by
# number (its sprite + attribute) and carries battle Health and attribute power.
# ---------------------------------------------------------------------------
_MOVES = None


# Authentic mono v-pet battle: attacks are by ATTRIBUTE, not per-mon named moves with
# effect "chips" (those VaccineName/Effect columns were DVPet/colour-device data, absent
# from the humulos corpus). The "move" is simply the attribute attack; there are no effects.
def move_name(num, attribute):
    """The attribute attack a Digimon throws (mono devices don't name per-mon moves)."""
    return attribute


def attack_info(num, attribute):
    """Mono battle has no attack-effect chips -> a plain attribute attack, no effect."""
    return {"name": attribute, "effect": "None", "conditions": []}



# ---------------------------------------------------------------------------
# Shop & consumables (foods.csv / items.csv sold via shopConsumable.csv).
# Each consumable carries care effects applied to the pet when used.
# ---------------------------------------------------------------------------
def _consumable(row, id_field):
    def num(k):
        try:
            return float(row.get(k) or 0)
        except ValueError:
            return 0.0
    def flag(k):
        return (row.get(k) or "FALSE").strip().upper() == "TRUE"
    return {
        "id": int(row[id_field]),
        "name": (row.get("Name") or "?").replace("<br>", " "),
        "desc": (row.get("Description") or "").replace("<br>", " "),
        "price": int(num("DefaultPrice")),
        "hunger": int(num("Hunger")),
        "mood": int(num("Mood")),
        "enthusiasm": int(num("Enthusiasm")),   # DVPet keeps spirit separate from mood
        "weight": int(num("Weight")),
        "energy": int(num("Energy (<1 * maxEnergy)") or num("Energy")),
        "strength": int(num("Strength")),
        "obedience": int(num("Obedience")),
        "vaccine": int(num("Vaccine")),
        "data": int(num("Data")),
        "virus": int(num("Virus")),
        "cured": flag("Cured"),
        # DVPet Healed clears an injury; Recovered only restores battle HP (no tuipet
        # analog -- HP is recomputed per battle), so do NOT fold Recovered into healed,
        # else Steak/Tuna/Honey/Bath/etc. would falsely cure injuries (DVPet applyConsumable).
        "healed": flag("Healed"),
        # foods.csv uses FatiguedRelieved/DepressedRelieved; items.csv uses Removes *
        "unfatigue": flag("Removes Fatigue") or flag("FatiguedRelieved"),
        "vitamin": int(num("Vitamins")) > 0,   # foods.csv Vitamins>0 (e.g. "Vitamin") guards vs injury worsening
        "undepressed": flag("Removes Depressed") or flag("DepressedRelieved"),
        "seconds": int(num("Seconds")),     # DVPet setTotalLifespan: lifespan delta (sec)
        "temp": int(num("Temp")),           # DVPet temp change (clamped 0..MaxTemp=100)
        "sleep": flag("Sleep"),             # DVPet item Sleep flag: induce sleep
        # DVPet FoodID/ItemID cols: ";"-list of consumables this one yields when used
        # (a "crafter" -- Toy Oven bakes random foods, Chocolate Egg pops random capsules)
        "unlocks_food": _idlist(row.get("FoodID")),
        "unlocks_item": _idlist(row.get("ItemID")),
        "action": (row.get("AnimationType") or "").strip(),  # DVPet item behaviour driver
        "dexnum": int(num("DigimonID")),  # direct ItemEvol target form (-1 if none)
        "category": (row.get("Type") or "").strip(),  # foods.csv food category for taste
        "effect_id": int(num("EffectID")) if (row.get("EffectID") or "").strip() not in ("", "-1") else -1,
        # DVPet Consumable uses-model: a held consumable carries uses up to MaxUses;
        # using spends UsesPer*; can_inc/can_dec gate buying/using (foods/items.csv).
        "max_uses": int(num("MaxUses") or 1),
        "uses_per": int(num("UsesPerFood") or num("UsesPerItem") or 1),
        "can_inc": (row.get("CanIncUses") or "TRUE").strip().upper() != "FALSE",
        "can_dec": (row.get("CanDecUses") or "TRUE").strip().upper() != "FALSE",
        # DVPet getNormalItems: only items flagged ShowInInventory appear in the bag
        # (transports / key / evolution items are hidden). Foods have no column -> shown.
        "show_in_inventory": (row.get("ShowInInventory") or "TRUE").strip().upper() != "FALSE",
    }


def _idlist(s):
    out = []
    for x in (s or "").split(";"):
        x = x.strip()
        if x and x.lstrip("-").isdigit() and int(x) >= 0:
            out.append(int(x))
    return out


@lru_cache(maxsize=1)
def _load_consumables():
    foods, items = {}, {}
    for r in csv.DictReader(open(os.path.join(_DATA, "foods.csv"))):
        try:
            foods[int(r["FoodIdentificationNum"])] = _consumable(r, "FoodIdentificationNum")
        except (KeyError, ValueError):
            continue
    for r in csv.DictReader(open(os.path.join(_DATA, "items.csv"))):
        try:
            items[int(r["ItemIdentificationNum"])] = _consumable(r, "ItemIdentificationNum")
        except (KeyError, ValueError):
            continue
    return foods, items


# An item is "functional" in tuipet only if use_item actually applies an effect.
# Pure action-items whose AnimationType drives an UNIMPLEMENTED system (the
# *Transport warps, ItemEvol evolution items, Recover lives, Inherit digimemory)
# carry zero stats and currently do nothing -- they are filtered out of the shop
# and loot until their system is built. Extend this as each system is implemented.
_FUNC_STATS = ("hunger", "mood", "enthusiasm", "weight", "energy",
               "strength", "obedience", "vaccine", "data", "virus")
_FUNC_FLAGS = ("cured", "healed", "unfatigue", "undepressed", "vitamin")


# DVPet world-warp items (items.csv AnimationType); handled by transportscreen.
TRANSPORT_ACTIONS = {"PhoenixTransport", "BirdraTransport", "GarudaTransport", "WhaTransport"}


def item_is_functional(e):
    if not e:
        return False
    if any(e.get(k) for k in _FUNC_STATS) or any(e.get(k) for k in _FUNC_FLAGS):
        return True
    if e.get("seconds") or e.get("temp") or e.get("sleep"):   # lifespan / temp / sleep items
        return True
    if e.get("effect_id", -1) >= 0:     # grants a temporary care effect (Futon)
        return True
    if e.get("action") == "ItemEvol":   # item-triggered evolution (now implemented)
        return True
    if e.get("action") in TRANSPORT_ACTIONS:   # world-warp items (now implemented)
        return True
    return bool(e.get("special") or e.get("unlocks_food") or e.get("unlocks_item"))


# ---------------------------------------------------------------------------
# Shop taxonomy: every consumable gets a shop category + a price-tier unlock stage.
# Categories: food / medicine / toy / chip / special. Special (evolution items,
# transports, X-gear) are NOT sold in the everyday shop -- they come from drops/DNA.
# ---------------------------------------------------------------------------
_SPECIAL_ANIMS = {"ItemEvol", "X_Program", "Inherit", "PhoenixTransport",
                  "BirdraTransport", "GarudaTransport", "WhaTransport", "PortToilet"}
_UNLOCK_STAGES = ["Baby I", "Child", "Adult", "Perfect", "Ultimate"]


def shop_category(e):
    """Bucket a consumable into food / medicine / toy / chip / special."""
    act = (e.get("action") or "").strip()
    if act in _SPECIAL_ANIMS or e.get("special") == "xantibody":
        return "special"
    if "Chip" in (e.get("name") or ""):          # the named battle chips only
        return "chip"
    if ("Med" in (e.get("category") or "") or e.get("cured")
            or act in ("Recover", "Bandaging")):  # cures / first-aid (not every healing food)
        return "medicine"
    return "food" if str(e.get("key", "")).startswith("f:") else "toy"


def _assign_unlock_stages(catalog):
    """Price-tier unlock: within each category, the cheapest items unlock first
    (Fresh) and pricier ones reveal as the pet grows (...Mega), 5 even bands."""
    from collections import defaultdict
    by = defaultdict(list)
    for e in catalog:
        by[e["shop_cat"]].append(e)
    for items in by.values():
        items.sort(key=lambda e: e["price"])
        n = max(1, len(items))
        for idx, e in enumerate(items):
            e["unlock_stage"] = _UNLOCK_STAGES[min(4, idx * 5 // n)]


@lru_cache(maxsize=1)
def shop_catalog():
    """The full buyable catalog: every functional, NON-special consumable (all
    foods + items), classified and price-tiered. Special items (evolution /
    transport / X-gear) are excluded -- those come from drops / DNA, not the shop."""
    foods, items = _load_consumables()
    out = []
    for cid, base in foods.items():
        e = dict(base); e["key"] = "f:%d" % cid; out.append(e)
    for cid, base in items.items():
        e = dict(base); e["key"] = "i:%d" % cid; out.append(e)
    for e in out:
        e["shop_cat"] = shop_category(e)
    shop = [e for e in out if e["shop_cat"] != "special" and e.get("price", 0) > 0
            and item_is_functional(e)]
    # collapse identical-named entries (e.g. the 11 gacha "Capsule" items) to one, cheapest
    seen = {}
    for e in sorted(shop, key=lambda x: x["price"]):
        seen.setdefault((e["shop_cat"], e["name"]), e)
    shop = list(seen.values())
    _assign_unlock_stages(shop)
    shop.sort(key=lambda e: (e["shop_cat"], e["price"]))
    return shop


def _shop_season4(val, default=0):
    """Parse a ';'-separated per-season list (Spring;Summer;Fall;Winter) of ints."""
    parts = [x.strip() for x in (val or "").split(";")]
    out = []
    for i in range(4):
        try:
            out.append(int(parts[i]))
        except (IndexError, ValueError):
            out.append(default)
    return out


def _shop_time4(val):
    """Parse DefaultTimeAvailable 'AtB;AtB;AtB;AtB' -> 4 per-season [start,end] hour windows."""
    out = []
    for seg in (val or "").split(";"):
        seg = seg.strip()
        if "t" in seg:
            a, b = seg.split("t", 1)
            try:
                out.append([int(a), int(b)]); continue
            except ValueError:
                pass
        out.append([0, 23])
    while len(out) < 4:
        out.append(out[-1] if out else [0, 23])
    return out[:4]


def _shop_econ(r):
    """DVPet ShopConsumable economy fields for one shopConsumable.csv row."""
    def i(k, d):
        try:
            return int(r.get(k) or d)
        except ValueError:
            return d
    return {
        "min_stock": i("minStock", 1), "max_stock": i("maxStock", 1),
        "stock_chance": _shop_season4(r.get("stockChance(SpringSummerFallWinter)"), 100),
        "time_avail": _shop_time4(r.get("DefaultTimeAvailable(HtH;SpringSummerFallWinter)")),
        "must_stock": (r.get("MustStock") or "false").strip().lower() == "true",
        "sale_chance": _shop_season4(r.get("SaleChance(SpringSummerFallWinter)"), 0),
        "sale_factor": i("SaleFactor", 1), "resell_factor": i("ResellFactor", 0),
    }


def _shop_econ_default():
    """Always-stocked, no-sale defaults for specialty items not in shopConsumable.csv."""
    # NOT must_stock: these specialty extras (X-Antibody etc.) are not in DVPet's
    # shopConsumable.csv -- keep them buyable but as an occasional rare find, not a
    # permanent shelf fixture, so they do not clutter the faithful storefront.
    return {"min_stock": 1, "max_stock": 1, "stock_chance": [20] * 4,
            "time_avail": [[6, 23]] * 4, "must_stock": False,
            "sale_chance": [0] * 4, "sale_factor": 1, "resell_factor": 10}


@lru_cache(maxsize=1)
def load_shop():
    """Shop inventory: resolved consumables with a stable key and shop price."""
    foods, items = _load_consumables()
    out = []
    seen = set()
    for r in csv.DictReader(open(os.path.join(_DATA, "shopConsumable.csv"))):
        try:
            cid = int(r["ConsumableID"])
        except (KeyError, ValueError):
            continue
        is_food = (r.get("IsFood") or "false").strip().lower() == "true"
        src = foods if is_food else items
        base = src.get(cid)
        if not base:
            continue
        key = f"{'f' if is_food else 'i'}:{cid}"
        if key in seen:
            continue
        seen.add(key)
        entry = dict(base)
        entry["key"] = key
        try:
            entry["price"] = int(r.get("Price") or entry["price"])
        except ValueError:
            pass
        entry.update(_shop_econ(r))
        out.append(entry)
    # special X-Antibody gear — not in shopConsumable.csv, but buyable here (and so
    # droppable as rare loot); using one induces the X-Antibody state, not care stats
    for sid, price in ((79, 2000), (14, 4000)):
        base = items.get(sid)
        key = f"i:{sid}"
        if base and key not in seen:
            entry = dict(base)
            entry["key"], entry["price"], entry["special"] = key, price, "xantibody"
            entry.update(_shop_econ_default()); out.append(entry); seen.add(key)
    # specialty stock not listed in shopConsumable.csv: the Vitamin (injury guard) and the
    # two "crafter" consumables, so their mechanics are actually reachable.
    for src_map, prefix, cid, price in ((foods, "f", 5, 300), (foods, "f", 58, 800), (items, "i", 66, 1200)):
        base = src_map.get(cid); key = f"{prefix}:{cid}"
        if base and key not in seen:
            entry = dict(base); entry["key"], entry["price"] = key, price
            entry.update(_shop_econ_default()); out.append(entry); seen.add(key)
    out = [e for e in out if item_is_functional(e)]   # hide inert action-items
    for e in out:
        e["shop_cat"] = shop_category(e)
    _assign_unlock_stages(out)
    out.sort(key=lambda e: e["price"])
    return out


def consumable_by_key(key):
    for e in load_shop():
        if e["key"] == key:
            return e
    # fall back to the full tables -- crafted/loot consumables need not have a shop slot
    try:
        kind, cid = key.split(":"); cid = int(cid)
    except (ValueError, AttributeError):
        return None
    foods, items = _load_consumables()
    base = (foods if kind == "f" else items).get(cid)
    if base:
        e = dict(base); e["key"] = key
        return e
    return None


@lru_cache(maxsize=1)
def load_backgrounds():
    """Habitat background scenes (per time-of-day/weather frame) keyed by file name."""
    path = os.path.join(_DATA, "backgrounds.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


@lru_cache(maxsize=1)
def load_effects():
    """Auxiliary effect overlays (poop/zzz/frozen/wash/emotes) keyed by name."""
    path = os.path.join(_DATA, "effects.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


@lru_cache(maxsize=1)
def load_icons():
    """Food/item icons (frame 0) keyed f:<id> / i:<id>, or empty if not extracted."""
    path = os.path.join(_DATA, "icons.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


@lru_cache(maxsize=1)
def load_care_effects():
    """DVPet careEffect.csv -> {id: effect}. Temporary care buffs (the Futon's sleep
    boost): a duration plus per-tick rate changes ("amount;every_n_ticks") and pause
    flags. Applied by pet.use_item / pet.tick."""
    def pair(v):
        parts = (v or "0;0").split(";")
        try:
            return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
        except ValueError:
            return (0, 0)
    def flag(v):
        return (v or "FALSE").strip().upper() == "TRUE"
    out = {}
    path = os.path.join(_DATA, "careEffect.csv")
    if not os.path.exists(path):
        return out
    for r in csv.DictReader(open(path)):
        try:
            eid = int(r["EffectID"])
        except (ValueError, KeyError, TypeError):
            continue
        out[eid] = {
            "name": (r.get("Name") or "").strip(),
            "desc": (r.get("Description") or "").strip(),
            "duration": int(r.get("MaxDuration") or 0),
            "end_on_sleep": flag(r.get("EndOnSleepChange")),
            "pause_temp": flag(r.get("PauseTemp")),
            "pause_call": flag(r.get("PauseCall")),
            "mood": pair(r.get("MoodChange")),
            "energy": pair(r.get("EnergyChange")),
            "hunger": pair(r.get("HungerChange")),
            "strength": pair(r.get("StrengthChange")),
            "can_reapply": flag(r.get("CanReapply")),
        }
    return out


@lru_cache(maxsize=1)
def load_egg_unlock():
    """DVPet eggUnlock.csv -> {egg_index: rule}. Joined to tuipet egg indices by the
    egg's hatch name. Each rule is the parsed set of conditions that gate the egg;
    egg.evaluate() tests them against persistence.get_progress()."""
    from . import egg as egg_mod
    name_to_idx = {}
    for i in range(egg_mod.count()):
        name_to_idx.setdefault(egg_mod.hatch_name(i), i)

    def _int(v):
        v = (v or "").strip()
        return int(v) if v.lstrip("-").isdigit() else None

    def _opt(v):
        v = (v or "").strip()
        return None if v in ("", "-1", "None", "FALSE") else v

    rules = {}
    path = os.path.join(_DATA, "eggUnlock.csv")
    rows = list(csv.reader(open(path)))
    for r in rows[1:]:
        if len(r) < 23:
            continue
        idx = name_to_idx.get(r[0].strip())
        if idx is None:
            continue                      # egg not in this tuipet build
        hist = None
        if _opt(r[12]):
            hist = [int(x) for x in r[12].split(":") if x.strip().isdigit()]
        price = _int(r[2]) or 0
        rules[idx] = {
            "idx": idx,
            "name": r[0].strip(),
            "start": r[1].strip() == "TRUE",
            "price": price if price > 0 else 0,
            "map": _int(r[3]) if (_int(r[3]) is not None and _int(r[3]) >= 0) else None,
            "stage": _opt(r[4]),
            "xanti": r[5].strip() == "TRUE",
            "zone": _opt(r[7]),
            "gen": _int(r[8]) if (_int(r[8]) is not None and _int(r[8]) >= 0) else None,
            "prev_field": _opt(r[9]),
            "prev_attr": _opt(r[10]),
            "prev_elem": _opt(r[11]),
            "history": hist,
            "food": _int(r[13]) if (_int(r[13]) is not None and _int(r[13]) >= 0) else None,
            "item": _int(r[14]) if (_int(r[14]) is not None and _int(r[14]) >= 0) else None,
            "password": _opt(r[16]),
            "obedience": _int(r[17]) if (_int(r[17]) is not None and _int(r[17]) >= 0) else None,
            "mood": _int(r[19]) if (_int(r[19]) is not None and _int(r[19]) >= 0) else None,
            "desc": (r[21] or "").strip(),
            "can_perm": r[22].strip() == "TRUE",
        }
    return rules

