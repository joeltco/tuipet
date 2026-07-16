"""The home shop: a rolled storefront, not a fixed catalogue.

Each game day the shelves clear and lazily re-roll when you open them -- the
must-stock staples first, then a random fill of consumables that pass their
seasonal stock chance, up to 8 food / 12 item slots.  Every slot carries a real
stock count and a seasonal sale roll (sale price = price - price/saleFactor).
Sold-out slots stay empty until a banked restock credit (1% per 5 game-minutes,
capped at 4) is spent on your next visit: each empty slot then re-fills or swaps
for a fresh item (50% of the time).  Every economy number is read from the
consumable's own columns in foods/items.csv -- nothing is invented.
"""
from __future__ import annotations
import random
from . import data
from .weather import SEASONS

FOOD_MAX = 8                  # MaxFoodShopInventory
ITEM_MAX = 12                 # MaxItemShopInventory
HOME_HOURS = (6, 23)          # the home shelves trade 6:00-23:00 every season;
#                               the storefront is shuttered outside those hours
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
    """Whether a consumable can appear on the shelves: its csv flag, OR earned
    -- a consumable found in the wild joins the shop for good."""
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
    """Is the town shop open this season: open <= hour <= close, literally --
    a span like 24-17 can never match a real hour, which is how a shop reads as
    CLOSED THIS SEASON (the winter-market towns 6/13/18 trade only in winter)."""
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


def life_token(e):
    """The LIFESPAN delta, in GAME HOURS -- the effect the shop used to hide.

    ⛔ Consumables carry `Seconds` in CANON seconds, and pet.py applies it as
    `lifespan += seconds / 60` REAL seconds.  One real second is one game
    minute (the clock-unit law), so `seconds` lands as seconds/60 GAME MINUTES
    == seconds/3600 GAME HOURS.  That is the number to show a player.

    This mattered: Miracle Drink costs -6h of your pet's life, Vitamin -1h, and
    the Gold Pill BUYS you +12h -- which is the entire reason to own one.  None
    of it appeared anywhere in the shop, the bag or the feed page (item-info
    audit 2026-07-14).  The toys carry a trivial +60s (+1 game-minute); that is
    rounded away like any other stat that rounds to zero.
    """
    secs = int(e.get("seconds") or 0)
    hours = secs / 3600.0
    if abs(round(hours)) >= 1:
        return "LIFE%+dh" % round(hours)
    return None


ATTR_LBL = (("vaccine", "Va"), ("data", "Da"), ("virus", "Vi"))


def trade_token(e):
    """The ATTRIBUTE TRADE, rendered as the conversion it actually is.

    The six trade toys (Board Game, Skateboard, Dumbbell, Computer Game, Music
    Player, Television) carry a symmetric zero-sum pair -- Board Game is
    Vaccine -15 / Data +15 -- and pet.py APPLIES it, conserving the total through
    applyAttributeChange + _compensate_attrs().  So "Vaccine to Data" is real.

    It was already shown, but only as two unrelated stats ("Va-15 Da+15"), which
    reads like two coincidental nudges rather than one TRADE.  Rendering the
    arrow makes the mechanic legible -- and it is generated from the deltas, so
    it still cannot drift from what the code does.
    """
    vals = {k: int(e.get(k) or 0) for k, _ in ATTR_LBL}
    pos = [k for k, v in vals.items() if v > 0]
    neg = [k for k, v in vals.items() if v < 0]
    if len(pos) == 1 and len(neg) == 1 and sum(vals.values()) == 0:
        lbl = dict(ATTR_LBL)
        return "%s\u2192%s%d" % (lbl[neg[0]], lbl[pos[0]], vals[pos[0]])
    return None


def effect_tokens(e, dp=False):
    """EVERY effect the game actually applies, most consequential first.

    Truth from data: generated from the same fields pet.py reads, so it cannot
    promise something the code does not do.  The authored `Description` column is
    not quoted -- not because it lies (it does not; "Vaccine to Data" is a real,
    implemented trade), but because a generated line carries the EXACT numbers
    and can never drift from the data behind it.

    Tidying rules: a stat that rounds to zero is dropped, a uniform Vaccine/Data/
    Virus nudge collapses to one "attr", and a symmetric zero-sum pair collapses
    to one TRADE arrow (Va->Da15).
    """
    t = []
    life = life_token(e)
    if life:
        t.append(life)                      # first: it is the costly one
    va, da, vi = e.get("vaccine", 0) or 0, e.get("data", 0) or 0, e.get("virus", 0) or 0
    trade = trade_token(e)
    uniform_attr = bool(va) and va == da == vi
    for k, lbl in (("hunger", "food"), ("mood", "mood"), ("energy", "en"),
                   ("strength", "eff"), ("health", "maxHP"), ("weight", "wt")):
        v = int(e.get(k) or 0)
        if v:
            t.append("%s%+d" % (lbl, v))
            if dp and k == "strength" and v > 0:
                t.append("DP+1")            # a strength food banks a jogress point
    if trade:
        t.append(trade)                     # one TRADE, not two loose nudges
    elif uniform_attr:
        t.append("attr%+d" % int(va))
    else:
        for k, lbl in ATTR_LBL:
            v = int(e.get(k) or 0)
            if v:
                t.append("%s%+d" % (lbl, v))
    for k, lbl in (("obedience", "obd"), ("sleep_lapse", "bed")):
        v = int(e.get(k) or 0)
        if v:
            t.append("%s%+d" % (lbl, v))
    if e.get("cured"):
        t.append("cure")
    if e.get("healed"):
        t.append("heal")
    # The LAPSE items work by SHORTENING an affliction rather than clearing it
    # outright (pet.py applies these to sick_length / inj_length / fatigue_length).
    # Med is the case that exposed it: its Cured flag is FALSE and its whole
    # function is cure_lapse -2 -- so the shelf described "basic medicine to treat
    # illness" as, simply, "mood-10".
    for k, lbl in (("cure_lapse", "sick"), ("heal_lapse", "inj"),
                   ("fatigue_lapse_change", "tired")):
        v = int(e.get(k) or 0)
        if v:
            t.append("%s%+d" % (lbl, v))
    if e.get("adv_life"):
        t.append("advLife%+d" % int(e["adv_life"]))   # Life Recovery, out on the road
    if e.get("unfatigue"):
        t.append("-tired")
    if e.get("undepressed"):
        t.append("-sad")
    if e.get("sleep"):
        t.append("zzz")
    return t


def effect_lines(e, w, rows, dp=False):
    """The effects wrapped into `rows` lines of `w` cols.

    NEVER silently drops a token: a consumable whose truth does not fit is a bug,
    and tests/test_item_info.py pins that every food and item fits.  Truncating
    here is how the lifespan cost stayed invisible in the first place.
    """
    lines, cur = [], ""
    for tok in effect_tokens(e, dp=dp):
        if not cur:
            cur = tok
        elif len(cur) + 1 + len(tok) <= w:
            cur += " " + tok
        else:
            lines.append(cur)
            cur = tok
    if cur:
        lines.append(cur)
    if not lines:
        lines = ["-"]
    return lines + [""] * (rows - len(lines))


def effect_line(e):
    """The one-line join (still used where a single terse row is all there is)."""
    return " ".join(effect_tokens(e)) or "-"


def slot_label(e):
    """One shop-list row: name / stock / sale tag / price.  The ONE format
    the home shop and every town shop share (refactor 2026-07-05)."""
    price = e.get("sale") or e.get("price", 0)
    qty = "OUT" if e.get("stock", 0) <= 0 else "x%d" % e["stock"]
    tag = "*" if e.get("sale") else " "
    return "%-18s %4s%s %5db" % (e["name"][:18], qty, tag, price)


def slot_info(pet, e, tw):
    """The selected shop slot's info column (rides beside the icon cell).

    Price/stock/owned share ONE row so the effects get TWO -- the old single
    effect row was 26 cols and silently truncated anything longer, which is how
    a -6h lifespan cost never reached the player (item-info audit 2026-07-14).
    """
    owned = pet.inventory.get(e["key"], 0)
    price = ("SALE %db" % e["sale"]) if e.get("sale") else "%db" % e.get("price", 0)
    stock = "SOLD OUT" if e.get("stock", 0) <= 0 else "x%d" % e["stock"]
    return [e["name"][:tw],
            "%s  %s  own %d" % (price, stock, owned),
            *effect_lines(e, tw, 2)]


def sell_info(pet, e, tw):
    """The selected sellable's info column: what you hold and what it fetches."""
    owned = pet.inventory.get(e["key"], 0)
    val = resell_price(e)
    val_s = ("sell %db" % val) if val else "can't resell"
    return [e["name"][:tw],
            "x%d  %s" % (owned, val_s),
            *effect_lines(e, tw, 2)]


def buy(pet, slot):
    """Buy a slot -> (msg, sfx): reward when bits actually moved, else error.
    The bits-delta sfx rule the home shop and town shops both hand-rolled."""
    bits0 = pet.bits
    msg = pet.buy_slot(slot)
    return msg, ("reward" if pet.bits < bits0 else "error")


def resell_price(e):
    """Resale value: price / resell_factor; a factor of 0 means unsellable
    (no floor -- no shipped consumable hits the sell-for-0 edge anyway).

    The bag counts USES, so a multi-use item resells PER USE: its item value
    divided by uses-per-item.  Charging the whole-item price per unit would let
    a fresh egg milk its 100-flush starter Toilet for 100b a FLUSH -- a
    10,000b printer; a full toilet still fetches exactly its 100b."""
    econ = e if "resell_factor" in e else (entry(e.get("key", "")) or {})
    factor = econ.get("resell_factor", 0)
    if not factor:
        return 0
    per_item = econ.get("price", e.get("price", 0)) // factor
    return per_item // max(1, int(econ.get("uses_per", 1) or 1))
