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


def _pool(pet, is_food):
    """randomizeShop's candidate pool: ShopUnlocked, price > 0, within the
    season's shop hours (and tuipet's functional-item filter)."""
    si, hr = _season_i(pet), _hour(pet)
    want = "f:" if is_food else "i:"
    out = []
    for e in data.home_shop_pool():
        if (e["key"].startswith(want) and e.get("shop_unlocked")
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
    pool = []
    for e in data.home_shop_pool():
        if not (e["key"].startswith(want) and e.get("shop_unlocked")
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


def resell_price(e):
    """getResellPrice: price / DefaultResellFactor; factor 0 = unsellable."""
    econ = e if "resell_factor" in e else (entry(e.get("key", "")) or {})
    factor = econ.get("resell_factor", 0)
    if not factor:
        return 0
    return max(1, econ.get("price", e.get("price", 0)) // factor)
