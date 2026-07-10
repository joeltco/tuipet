"""Shop -- DVPet's HOME shop (PhysicalState.randomizeShop / restockShop).

The storefront is a rolled ROSTER, not a catalog: each game day the shop clears
(dailyChange) and lazily re-rolls on open -- must-stock items first, then a
random fill of consumables that pass their seasonal stock chance, up to 8 food /
12 item slots.  Every slot gets a real stock count (DefaultMinStock..MaxStock)
and a seasonal sale roll (salePrice = price - price/saleFactor).  Sold-out slots
sit empty until a banked restock credit (1% per 5 game-min, max 4) is spent on
the next shop visit: each empty slot then either re-fills or swaps for a NEW
item (RestockNewItemChance 50%).  All economy numbers come from each
consumable's own Default* columns (foods/items.csv) -- nothing is invented.
"""
from __future__ import annotations
import random
from . import data
from .weather import SEASONS

FOOD_MAX = 8                  # MaxFoodShopInventory
ITEM_MAX = 12                 # MaxItemShopInventory
HOME_HOURS = (6, 23)          # config.csv FoodShopTime/ItemShopTime rows 752/753:
#                               "6t23" all four seasons -- the HOME shop keeps
#                               canon trading hours (drawShop gates on isShopOpen)
RESTOCK_MIN = 5               # RestockMin: game-min between credit rolls (1 game-min == 1s)
RESTOCK_CHANCE = 1            # RestockShopChance %
RESTOCK_NEW_ITEM = 50         # RestockNewItemChance %
RESTOCK_MAX = 4               # RestockMax banked credits


def _season_i(pet):
    return SEASONS.index(pet.season)


def _hour(pet):
    from .pet import DAY_LENGTH
    return int((pet.world_seconds % DAY_LENGTH) / DAY_LENGTH * 24)


def entry(key):
    return data.consumable_by_key(key)


def _unlocked(e, found):
    """getShopUnlocked: the csv flag, OR earned -- a consumable found in the
    wild joins the shelves for good (canon unlockItem/unlockFood; shop/economy
    audit 2026-07-06)."""
    return e.get("shop_unlocked") or e["key"] in found


def _pool(pet, is_food):
    """randomizeShop's candidate pool: ShopUnlocked (csv or earned), price > 0,
    within the season's shop hours (and tuipet's functional-item filter)."""
    from . import persistence as _persist
    found = _persist.shop_unlocks()
    si, hr = _season_i(pet), _hour(pet)
    want = "f:" if is_food else "i:"
    out = []
    for e in data.home_shop_pool():
        if (e["key"].startswith(want) and _unlocked(e, found)
                and e.get("price", 0) > 0 and data.item_is_functional(e)):
            t0, t1 = e["time_avail"][si]
            if t0 <= hr <= t1:
                out.append(e)
    return out


def _rand_stock(e):
    """ShopConsumable.randomizeStock: minStock, or a draw up to maxStock."""
    if 0 < e["min_stock"] < e["max_stock"]:
        return random.randint(e["min_stock"], e["max_stock"])
    return e["min_stock"]


def _mk_slot(pet, e, check_sale):
    sale = 0
    if (check_sale and e.get("sale_factor")
            and random.randrange(100) < e["sale_chance"][_season_i(pet)]):
        sale = e["price"] - e["price"] // e["sale_factor"]   # checkSale
    return {"key": e["key"], "stock": _rand_stock(e), "sale": sale}


def _roll(pet, is_food, check_sale=True, exclude=()):
    """randomizeShop + addConsumables: mustStock first, then the seasonal
    stock-chance pool, drawn in random order until the shop is full."""
    pool = _pool(pet, is_food)
    si = _season_i(pet)
    must = [e for e in pool if e["must_stock"]]
    avail = [e for e in pool if not e["must_stock"]
             and random.randrange(100) < e["stock_chance"][si]]
    mx = FOOD_MAX if is_food else ITEM_MAX
    slots, seen = [], set(exclude)
    for group in (must, avail):
        random.shuffle(group)                     # addConsumables draws by nextInt
        for e in group:
            if len(slots) >= mx:
                break
            if e["key"] in seen:
                continue
            seen.add(e["key"])
            slots.append(_mk_slot(pet, e, check_sale))
    return slots


def home_shop_open(pet):
    """PhysicalState.isShopOpen on the HOME hours (Utility.isOpen):
    the shelves trade 6:00-23:00 game time, every season."""
    return HOME_HOURS[0] <= _hour(pet) <= HOME_HOURS[1]


def town_shop_hours(pet, town, is_food):
    """This season's (open, close) span for the town shop, or None when the
    data carries none (always open)."""
    return (town.get("food_hours" if is_food else "item_hours") or {}).get(pet.season)


def town_shop_open(pet, town, is_food):
    """Utility.isOpen on the town's per-season shop hours (towns.csv
    Food/ItemShopOpen): open <= hour <= close, literally -- a '24t17' span can
    never match a real hour, which is canon for CLOSED THIS SEASON (the
    winter-market towns 6/13/18 trade only in winter)."""
    span = town_shop_hours(pet, town, is_food)
    if not span:
        return True
    return span[0] <= _hour(pet) <= span[1]


def roll_town_shop(pet, town, is_food):
    """Town.getFood/ItemShop: the home pool with the TOWN's shopConsumable.csv
    override econ substituted per consumable (compareConsumables), rolled to
    the town's own inventory size.  Transient: a fresh roll per visit."""
    ov = data.load_shop_overrides()
    by_cid = {}
    for sid in town["foods_override" if is_food else "items_override"]:
        o = ov.get(sid)
        if o and o["is_food"] == is_food:
            by_cid[o["consumable_id"]] = o
    si, hr = _season_i(pet), _hour(pet)
    want = "f:" if is_food else "i:"
    from . import persistence as _persist
    found = _persist.shop_unlocks()
    pool = []
    for e in data.home_shop_pool():
        if not (e["key"].startswith(want) and _unlocked(e, found)
                and data.item_is_functional(e)):
            continue
        o = by_cid.get(e["id"])
        if o:
            e = dict(e, **{k: o[k] for k in ("price", "min_stock", "max_stock",
                                             "stock_chance", "time_avail", "must_stock",
                                             "sale_chance", "sale_factor", "resell_factor")})
        if e.get("price", 0) <= 0:
            continue
        t0, t1 = e["time_avail"][si]
        if t0 <= hr <= t1:
            pool.append(e)
    mx = town["food_max" if is_food else "item_max"]
    must = [e for e in pool if e["must_stock"]]
    avail = [e for e in pool if not e["must_stock"]
             and random.randrange(100) < e["stock_chance"][si]]
    slots, seen = [], set()
    # the town's biome SPECIALTY leads the shelf (world.biome_specialty_keys):
    # local goods it fronts ahead of the daily roll so each biome's town reads
    # distinct -- drawn from the SAME gated pool as the roll, so the town's own
    # prices, the shop-unlock progression and the seasonal/hourly windows all
    # still apply (the raw home-pool shortcut bypassed them; audit 2026-07-10)
    from . import world
    pool_by_key = {e["key"]: e for e in pool}
    for key in world.biome_specialty_keys(town["id"], is_food):
        e = pool_by_key.get(key)
        if not e or len(slots) >= mx or key in seen:
            continue
        seen.add(key)
        slot = _mk_slot(pet, e, True)
        slot["price"] = e["price"]          # the town's own price rides the slot
        slots.append(slot)
    for group in (must, avail):
        random.shuffle(group)
        for e in group:
            if len(slots) >= mx:
                break
            if e["key"] in seen:
                continue
            seen.add(e["key"])
            slot = _mk_slot(pet, e, True)
            slot["price"] = e["price"]          # the town's own price rides the slot
            slots.append(slot)
    return slots


def open_shop(pet, is_food):
    """Entering the shop page: dailyChange reset, lazy roll, restock-on-open."""
    from .pet import DAY_LENGTH
    day = int(pet.world_seconds // DAY_LENGTH)
    if pet.shop_day != day:                       # dailyChange clears the shops
        pet.shop_day = day
        pet.shop_food, pet.shop_item = [], []
    attr = "shop_food" if is_food else "shop_item"
    slots = getattr(pet, attr)
    if not slots:
        slots = _roll(pet, is_food, check_sale=True)   # randomize<X>Shop(checkSale)
        setattr(pet, attr, slots)
    elif pet.shop_restock > 0 and any(s["stock"] == 0 for s in slots):
        _restock(pet, slots, is_food)             # restock<X>Shop spends one credit
    return slots


def _restock(pet, slots, is_food):
    """restockShop: each sold-out slot swaps for a NEW item not already stocked
    (RestockNewItemChance) or just re-rolls its stock.  No new sale rolls."""
    fresh = _roll(pet, is_food, check_sale=False,
                  exclude=[s["key"] for s in slots])
    for i, s in enumerate(slots):
        if s["stock"] != 0:
            continue
        if random.randrange(100) < RESTOCK_NEW_ITEM and fresh:
            slots[i] = fresh.pop(0)
        else:
            e = entry(s["key"])
            if e:
                s["stock"] = _rand_stock(e)
    pet.shop_restock = max(0, pet.shop_restock - 1)


def check_restock_tick(pet, dt):
    """checkRestock: every RestockMin game-minutes, RestockShopChance% to bank
    a restock credit, capped at RestockMax."""
    pet.shop_restock_t += dt
    while pet.shop_restock_t >= RESTOCK_MIN:
        pet.shop_restock_t -= RESTOCK_MIN
        if pet.shop_restock < RESTOCK_MAX and random.randrange(100) < RESTOCK_CHANCE:
            pet.shop_restock += 1


def purchase_price(slot):
    """getPurchasePrice: the rolled sale price when on sale, else list price."""
    if slot.get("sale"):
        return slot["sale"]
    if "price" in slot:
        return slot["price"]
    e = entry(slot["key"])
    return e["price"] if e else 0


def effect_line(e):
    """One terse readout of a consumable's applyFood/applyItem effects."""
    parts = []
    for k, lbl in (("hunger", "food"), ("mood", "mood"), ("weight", "wt"), ("energy", "en"),
                   ("strength", "eff"), ("vaccine", "Va"), ("data", "Da"), ("virus", "Vi")):
        if e.get(k):
            parts.append("%s%+d" % (lbl, e[k]))
    if e.get("cured"):
        parts.append("cure")
    if e.get("healed"):
        parts.append("heal")
    return " ".join(parts) or "-"


def slot_label(e):
    """One shop-list row: name / stock / sale tag / price.  The ONE format
    the home shop and every town shop share (refactor 2026-07-05)."""
    price = e.get("sale") or e.get("price", 0)
    qty = "OUT" if e.get("stock", 0) <= 0 else "x%d" % e["stock"]
    tag = "*" if e.get("sale") else " "
    return "%-18s %4s%s %5db" % (e["name"][:18], qty, tag, price)


def slot_info(pet, e, tw):
    """The selected shop slot's info column (rides beside the icon cell)."""
    owned = pet.inventory.get(e["key"], 0)
    price = ("SALE %db" % e["sale"]) if e.get("sale") else "%db" % e.get("price", 0)
    stock = "SOLD OUT" if e.get("stock", 0) <= 0 else "stock x%d" % e["stock"]
    return [e["name"][:tw], price, "%s  own %d" % (stock, owned), effect_line(e)[:tw]]


def sell_info(pet, e, tw):
    """The selected sellable's info column: what you hold and what it fetches."""
    owned = pet.inventory.get(e["key"], 0)
    val = resell_price(e)
    return [e["name"][:tw], "x%d" % owned,
            ("sell %db" % val) if val else "can't resell", effect_line(e)[:tw]]


def buy(pet, slot):
    """Buy a slot -> (msg, sfx): reward when bits actually moved, else error.
    The bits-delta sfx rule the home shop and town shops both hand-rolled."""
    bits0 = pet.bits
    msg = pet.buy_slot(slot)
    return msg, ("reward" if pet.bits < bits0 else "error")


def resell_price(e):
    """getResellPrice: price / DefaultResellFactor; factor 0 = unsellable.
    (Canon re-audit 2026-07: canon has NO floor -- the old max(1, ...) was
    not canon; no shipped consumable hits the sell-for-0 edge anyway.)

    tuipet's bag counts USES (canon quantity IS uses), so a multi-use item
    resells PER USE: the canon item value / UsesPerItem.  Paying the whole-
    item price per unit let a fresh egg milk its 100-flush starter Toilet
    for 100b a FLUSH -- a 10,000b printer (egg-shop audit 2026-07-05); a
    full toilet still fetches exactly the canon 100b."""
    econ = e if "resell_factor" in e else (entry(e.get("key", "")) or {})
    factor = econ.get("resell_factor", 0)
    if not factor:
        return 0
    per_item = econ.get("price", e.get("price", 0)) // factor
    return per_item // max(1, int(econ.get("uses_per", 1) or 1))
