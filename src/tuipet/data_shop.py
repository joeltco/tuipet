"""The economy data (tier-1 split, 2026-07-17): foods, the vitems
catalog, the DVPet consumable tables, shop overrides/econ, loot tables."""
from __future__ import annotations
import csv  # noqa: F401
import gzip  # noqa: F401
import json  # noqa: F401
import os
import re  # noqa: F401
from functools import lru_cache  # noqa: F401

_HERE = os.path.dirname(__file__)
_DATA = os.path.join(_HERE, "data")
_RAW = _DATA  # bundled CSVs (digimon/evolutions/foods) live alongside sprites
from .data_core import (  # noqa: F401  (shared plumbing)
    AssetsError, _load_bundled, _open_data)


@lru_cache(maxsize=1)
def load_vitems():
    """The DSprite item catalog (vitems.json, cloned from the v0.4.x rebuild;
    BASIC VPET 2026-07-16) -- the shop/bag speak THIS now; the DVPet
    foods/items.csv consumable machine is retired."""
    with _open_data(os.path.join(_DATA, "vitems.json")) as fh:
        return json.load(fh)

@lru_cache(maxsize=1)
def load_foods():
    path = os.path.join(_RAW, "foods.csv")
    foods = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            try:
                fid = int(row["FoodIdentificationNum"])
                foods.append({
                    "id": fid,
                    "key": f"f:{fid}",
                    # DVPet's Java UI embeds <br> line breaks in names
                    # ("Vaccine<br>Chip G") -- strip like the consumable parser
                    "name": (row["Name"] or "?").replace("<br>", " "),
                    "hunger": int(row["Hunger"] or 0),
                    "weight": int(row["Weight"] or 0),
                    "health": int(row.get("Health") or 0),   # permanent HP gain (HP Chip)
                    "mood": int(row["Mood"] or 0),
                    "energy": int(row["Energy"] or 0),
                    "strength": int(row["Strength"] or 0),
                    "obedience": int(row["Obedience"] or 0),
                    "enthusiasm": int(row["Enthusiasm"] or 0),
                    "category": (row.get("Type") or "").strip(),
                    "protein": int(row.get("Proteins") or 0),
                    "vitamin_n": int(row.get("Vitamins") or 0),
                    "mineral": int(row.get("Minerals") or 0),
                    # inventory model (DVPet Consumable): StartingQuantity seeds what
                    # you own; CanDec=false = never depletes (the staples: Meat/Fish/
                    # Fruit/Vegetable); ShowInInventory=false = not on the feed page
                    # (Med/Vitamin ride the heal flows instead)
                    "bm": int(row.get("BMGauge") or 0),
                    # canon re-audit 2026-07: applyConsumable reads these for FOODS
                    # too -- 39 calorie foods, 3 lifespan foods, 7 attribute foods,
                    # a sleep food and 2 temp foods were silently dropped
                    "calories": int(row.get("Calories") or 0),
                    "seconds": int(row.get("Seconds") or 0),
                    "vaccine": int(row.get("Vaccine") or 0),
                    "data": int(row.get("Data") or 0),
                    "virus": int(row.get("Virus") or 0),
                    "sleep_lapse": int(row.get("SleepLapse") or 0),
                    "temp": int(row.get("Temp") or 0),
                    # changeToPrefTemp (canon applyConsumable): snap to the
                    # comfort midpoint (no shipped food carries it; data-driven)
                    "pref_temp": (row.get("ChangeToPrefTemp") or "").strip().upper() == "TRUE",
                    # trait affinity (checkRefused personality mods): a food that
                    # suits the pet's temperament goes down easier
                    "t_glutton": int(row.get("Glutton") or 0),
                    "t_restless": int(row.get("Restless") or 0),
                    "t_disposition": int(row.get("Disposition") or 0),
                    "start": int(row.get("StartingQuantity") or 0),
                    "can_dec": (row.get("CanDec") or "").strip().lower() == "true",
                    "show": (row.get("ShowInInventory") or "").strip().upper() == "TRUE",
                })
            except (KeyError, ValueError):
                continue
    return foods

# DVPet DNA fields by name ("None" is Enum.Field ordinal 0 = a REAL bankable/chargeable
# slot; only NA is excluded). Order here is tuipet's menu display order -- inventory and
# evolution gates are keyed by NAME (digimon.csv {Field}Key/{Field}Value matched by name),
# so this tuple's order is independent of Enum.Field ordinals.
FOOD_CATEGORIES = ("Meat", "Fish", "Veg", "Fruit", "Med", "Junk", "Grain", "Dairy")

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
        # a FRACTIONAL energy is a share of maxEnergy (canon applyItem: the
        # X-Program's -0.8, the Digimentals' -0.66) -- the old int() zeroed
        # every one of them (energy audit 2026-07-06).  Whole values stay int.
        "energy": (lambda v: v if v != int(v) else int(v))(
            num("Energy (<1 * maxEnergy)") or num("Energy")),
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
        # changeToPrefTemp: snap temp to the ideal midpoint (the Futon tucks
        # the room comfy, then PauseTemp holds it).  Ported 2026-07-15 on
        # Joel's call ("if futons snap to comfort temp in canon, then switch
        # it back") -- this reversed the one-day-old deliberate omission.
        "pref_temp": flag("ChangeToPrefTemp"),
        "sleep": flag("Sleep"),             # DVPet item Sleep flag: induce sleep
        # foods.csv SleepLapse: the bedtime nudge (Caffeine Pill) -- parsed by
        # load_foods for feed() but DROPPED here, so the bag door lost the
        # pill's signature effect (items.csv has no column -> 0; audit 2026-07-13)
        "sleep_lapse": int(num("SleepLapse")),
        # items.csv Disturb: using this item WAKES a sleeping pet -- canon useItem's
        # `if (item.disturb()) this.disturb()`.  Every item disturbs but the Futon
        # (Disturb=FALSE); foods have no column, so flag() defaults them to False.
        "disturb": flag("Disturb"),
        # checkMaxHoursBeforeSleep (sleep audit 2026-07-15): -1 = usable any
        # time; else the item only applies asleep or within N game-MINUTES of
        # nod-off (canon compares the raw column against the minute-based
        # sleep clocks -- "Hours" is the column's own misnomer).  Only the
        # Futon carries it (1): it's a tuck-in for a sleeper, not day furniture.
        "max_hours_sleep": int(row.get("MaxHoursBeforeSleep") or -1),
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
        "gift_chance": int(num("GiftChance/100")),   # per-item odds of being the gift-call present
        # applyConsumable recovery deltas (in LAPSES): Med -2 sick, Bandage -2 injury
        "cure_lapse": int(num("CureLapseChange")),
        "heal_lapse": int(num("HealLapseChange")),
        "fatigue_lapse_change": int(num("FatigueLapseChange")),
        # toy engagement (applyItemNoObedience) + personality mood shaping
        "diminishing": flag("DiminishingReturns"),
        "interest_change": int(num("ItemDisinterestChange")),
        "t_glutton": int(num("Glutton")),
        "t_restless": int(num("Restless")),
        "t_disposition": int(num("Disposition")),
        "health": int(num("Health")),   # permanent fullHealthPoints gain (HP Chip)
        # items.csv AdventureLifeInc (Life Recovery, item 27): +N Digital World
        # life, gated at MaxAdventureLife (PhysicalState.useItem)
        "adv_life": int(num("AdventureLifeInc")),

        "uses_per": int(num("UsesPerFood") or num("UsesPerItem") or 1),
        # items.csv names these CanIncUses/CanDecUses; foods.csv CanInc/CanDec --
        # reading only the items name defaulted every FOOD to can_inc=True, letting
        # staples into the gift/discover pools (audit 2026-07)
        "can_inc": (row.get("CanIncUses") or row.get("CanInc") or "TRUE").strip().upper() != "FALSE",
        "can_dec": (row.get("CanDecUses") or row.get("CanDec") or "TRUE").strip().upper() != "FALSE",
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
    for r in csv.DictReader(_open_data(os.path.join(_DATA, "foods.csv"))):
        try:
            foods[int(r["FoodIdentificationNum"])] = _consumable(r, "FoodIdentificationNum")
        except (KeyError, ValueError):
            continue
    for r in csv.DictReader(_open_data(os.path.join(_DATA, "items.csv"))):
        try:
            items[int(r["ItemIdentificationNum"])] = _consumable(r, "ItemIdentificationNum")
        except (KeyError, ValueError):
            continue
    return foods, items

# An item is "functional" in tuipet only if use_item actually applies an
# effect.  Since the strict-DSprite item cut the live effects are the DSprite
# name table + the egg_of_* crests; a DVPet ACTION-item (transports, Life
# Recovery, ItemEvol relics, the Digimemory redeem) has NO handler and must
# never count as functional -- the old "(now implemented)" claims described
# systems that left with adventure/towns (liveness audit 2026-07-18).
# (mood/enthusiasm/undepressed dropped 2026-07-16: those meters left with
# their systems -- an item whose only effect was them would sell a no-op)
_FUNC_STATS = ("hunger", "weight", "energy",
               "strength", "obedience", "vaccine", "data", "virus")

_FUNC_FLAGS = ("cured", "healed", "unfatigue", "vitamin")

def item_is_functional(e):
    if not e:
        return False
    if any(e.get(k) for k in _FUNC_STATS) or any(e.get(k) for k in _FUNC_FLAGS):
        return True
    # sleep_lapse joined the list when mood left (2026-07-16): the Caffeine
    # Pill's bedtime nudge is real, and mood no longer vouches for it
    if e.get("seconds") or e.get("sleep") or e.get("sleep_lapse"):   # lifespan / sleep items
        return True
    # (the effect_id clause -- "grants a temporary care effect" -- left with
    # the careEffect runtime: strict-DSprite items, 2026-07-17; the ItemEvol/
    # Inherit/Life-Recovery/transport clauses left 2026-07-18 -- their
    # handlers died with adventure/towns and the DVPet item machine, so they
    # marked paid DUDS as sellable goods)
    return bool(e.get("special") or e.get("unlocks_food") or e.get("unlocks_item"))

# ---------------------------------------------------------------------------
# Bag taxonomy: shop_category buckets owned consumables into the bag tabs
# (food / medicine / toy / chip / special).  The SHOP roster itself is the
# DVPet home-shop roll (shop.py) -- no invented category/stage gating.
# ---------------------------------------------------------------------------
_SPECIAL_ANIMS = {"ItemEvol", "X_Program", "Inherit", "PhoenixTransport",
                  "BirdraTransport", "GarudaTransport", "WhaTransport", "PortToilet"}

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

def _default_econ(r):
    """DVPet home-shop economy: each consumable's OWN Default* columns
    (FoodType/Item build their _homeShop ShopConsumable from these).
    shopConsumable.csv is only the per-TOWN override table -- tuipet has the
    single home shop, so the Default* columns are the whole economy."""
    def i(k, d):
        try:
            return int(r.get(k) or d)
        except ValueError:
            return d
    return {
        "min_stock": i("DefaultMinStock", 1), "max_stock": i("DefaultMaxStock", 1),
        "stock_chance": _shop_season4(r.get("DefaultStockChance(SpringSummerFallWinter)"), 100),
        "time_avail": _shop_time4(r.get("DefaultTimeAvailable(HtH;SpringSummerFallWinter)")),
        "must_stock": (r.get("DefaultMustStock") or "false").strip().lower() == "true",
        "sale_chance": _shop_season4(r.get("DefaultSaleChance(SpringSummerFallWinter)"), 0),
        "sale_factor": i("DefaultSaleFactor", 1), "resell_factor": i("DefaultResellFactor", 0),
        "shop_unlocked": (r.get("ShopUnlocked") or "FALSE").strip().upper() == "TRUE",
    }

# (load_shop_overrides left 2026-07-18: zero callers since the towns/adventure
# removal -- the CSV stays on disk, dormant.)

# (load_towns left 2026-07-18: zero callers since the towns/adventure
# removal -- the CSV stays on disk, dormant.)

def _shop_econ_default():
    """Always-stocked, no-sale defaults for specialty items not in shopConsumable.csv."""
    # NOT must_stock: these specialty extras (X-Antibody etc.) are not in DVPet's
    # shopConsumable.csv -- keep them buyable but as an occasional rare find, not a
    # permanent shelf fixture, so they do not clutter the faithful storefront.
    return {"min_stock": 1, "max_stock": 1, "stock_chance": [20] * 4,
            "time_avail": [[6, 23]] * 4, "must_stock": False,
            "sale_chance": [0] * 4, "sale_factor": 1, "resell_factor": 10}

@lru_cache(maxsize=1)
def home_shop_pool():
    """Every consumable + its own Default* shop economy.  randomizeShop pools
    the ones with ShopUnlocked && price > 0 (shop.py applies that filter); the
    rest are here so bag/loot lookups get data-driven resell factors too."""
    foods, items = _load_consumables()
    out = {}
    for fn, id_field, src, prefix in (("foods.csv", "FoodIdentificationNum", foods, "f"),
                                      ("items.csv", "ItemIdentificationNum", items, "i")):
        for r in csv.DictReader(_open_data(os.path.join(_DATA, fn))):
            try:
                cid = int(r[id_field])
            except (KeyError, ValueError):
                continue
            base = src.get(cid)
            if not base:
                continue
            e = dict(base)
            e["key"] = f"{prefix}:{cid}"
            e.update(_default_econ(r))
            out[e["key"]] = e
    # tuipet specialty adaptations (kept from the old shop): the X-gear, the plain
    # Vitamin and the crafters ship with price 0 / ShopUnlocked false in the data,
    # but their mechanics must stay reachable -- stocked as occasional 20% finds
    for key, price in (("i:79", 2000), ("i:14", 4000), ("f:5", 300), ("f:58", 800), ("i:66", 1200)):
        e = out.get(key)
        if e and not (e.get("shop_unlocked") and e.get("price", 0) > 0):
            e["price"] = price
            e.update(_shop_econ_default())
            e["shop_unlocked"] = True
            if key in ("i:79", "i:14"):
                e["special"] = "xantibody"
    return list(out.values())

def consumable_by_key(key):
    for e in home_shop_pool():
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

# (load_loot_tables left 2026-07-18: zero callers since the towns/adventure
# removal -- the CSV stays on disk, dormant.)
