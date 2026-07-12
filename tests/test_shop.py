"""Home shop vs DVPet PhysicalState.randomizeShop/restockShop + ShopConsumable."""
import random
from tuipet.pet import Pet, DAY_LENGTH
from tuipet import data, shop


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine", bits=100000)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_roster_is_rolled_to_the_slot_caps():
    p = _pet()
    food = shop.open_shop(p, True)
    items = shop.open_shop(p, False)
    assert len(food) == shop.FOOD_MAX == 8          # MaxFoodShopInventory
    assert len(items) == shop.ITEM_MAX == 12        # MaxItemShopInventory
    assert len({s["key"] for s in food}) == len(food)   # no duplicate slots


def test_slots_carry_real_stock_counts():
    p = _pet()
    for s in shop.open_shop(p, True):
        e = shop.entry(s["key"])
        assert e["min_stock"] <= s["stock"] <= max(e["min_stock"], e["max_stock"])


def test_must_stock_items_always_shelved():
    # items.csv: Futon / Toilet / Port. Potty are DefaultMustStock=TRUE
    p = _pet()
    keys = {s["key"] for s in shop.open_shop(p, False)}
    must = {e["key"] for e in data.home_shop_pool()
            if e.get("must_stock") and e.get("shop_unlocked") and e["price"] > 0
            and data.item_is_functional(e)}
    assert must and must <= keys


def test_daily_reset_rerolls():
    p = _pet()
    shop.open_shop(p, True)
    p.shop_food[0]["stock"] = 0
    p.world_seconds += DAY_LENGTH                   # next game day -> dailyChange
    food = shop.open_shop(p, True)
    assert all(s["stock"] > 0 for s in food)


def test_buy_decrements_stock_and_pays_sale_price():
    p = _pet()
    slot = {"key": "f:8", "stock": 2, "sale": 250}  # Steak 500b, on sale
    assert shop.purchase_price(slot) == 250
    msg = p.buy_slot(slot)
    assert "Bought" in msg and slot["stock"] == 1
    assert p.bits == 100000 - 250
    slot["stock"] = 0
    assert p.buy_slot(slot) == "Sold out."


def test_resell_uses_the_data_factor():
    steak = data.consumable_by_key("f:8")           # DefaultResellFactor 10
    assert shop.resell_price(steak) == steak["price"] // 10
    warp = next(e for e in data.home_shop_pool()
                if e["resell_factor"] == 0 and e["price"] > 0)
    assert shop.resell_price(warp) == 0             # factor 0 = unsellable


def test_restock_swaps_or_refills_sold_out_slots():
    random.seed(3)
    p = _pet()
    slots = shop.open_shop(p, True)
    dead = [s["key"] for s in slots]
    for s in slots:
        s["stock"] = 0
    p.shop_restock = 1
    out = shop.open_shop(p, True)                   # restock-on-open spends the credit
    assert p.shop_restock == 0
    assert all(s["stock"] > 0 or s["key"] not in dead for s in out)
    assert any(s["stock"] > 0 for s in out)


def test_restock_credits_accrue_capped():
    p = _pet(shop_restock=shop.RESTOCK_MAX)
    for _ in range(200):
        shop.check_restock_tick(p, 5.0)
    assert p.shop_restock == shop.RESTOCK_MAX       # never exceeds RestockMax


def test_roster_survives_the_save_round_trip():
    from tuipet import persistence
    p = _pet()
    shop.open_shop(p, True)
    d = persistence.to_save_dict(p)
    p2, _ = persistence.pet_from_save(d, catch_up=False)
    assert p2.shop_food == p.shop_food and p2.shop_day == p.shop_day


# ---- gift call (checkGiftCall / getGift / giftEnd) ---------------------------

def test_gift_needs_a_happy_grown_awake_pet():
    p = _pet(mood=0)                                # Neutral: never rolls
    p.gift_t = 999.0
    p._check_gift_call(0.0)
    assert p.gift == ""
    p2 = _pet(mood=300, obedience=150, stage="Egg")
    p2.gift_t = 999.0
    p2._check_gift_call(0.0)
    assert p2.gift == ""


def test_gift_roll_matches_the_canon_range():
    # mood 300 + obedience 150 -> nextInt(100-150+0+70) = 1/20 per window
    random.seed(0)
    p = _pet(mood=300, obedience=150)
    hits = 0
    for _ in range(2000):
        p.gift = ""
        p.gift_t = 999.0
        p._check_gift_call(0.0)
        hits += bool(p.gift)
    assert 0.02 < hits / 2000 < 0.09                # ~1/20


def test_gift_pool_is_giftchance_gated():
    random.seed(1)
    p = _pet(mood=300, obedience=150)
    for _ in range(30):
        key = p._pick_gift()
        assert key
        e = data.consumable_by_key(key)
        assert e["gift_chance"] > 0 and e["can_inc"]


def test_claim_gift_bags_it_and_cheers():
    p = _pet()
    p.gift = "f:8"                                  # Steak
    msg = p.claim_gift()
    assert "Steak" in msg and p.inventory.get("f:8") == 1
    assert p.gift == "" and p.anim == "happy"
    assert p.claim_gift() == ""                     # nothing pending -> no-op


# ---- home shop hours (audit 2026-07-04): config FoodShopTime/ItemShopTime ----

def test_home_shop_keeps_its_trading_hours():
    """The home shelves trade 6:00-23:00 every season; outside those hours the
    shutters come down and there is nothing to browse or buy."""
    from tuipet import shop
    from tuipet.shopscreen import ShopPanel
    p = _pet()
    p.world_seconds = 3 * 60.0                      # 3am
    assert not shop.home_shop_open(p)
    pan = ShopPanel(p)
    assert "Closed" in pan.msg
    assert pan._rows() == []                        # shutters down: nothing to buy
    assert "shutters" in pan.text().plain
    pan.key("enter")                                # no purchase path exists
    assert "Bought" not in pan.msg
    pan.key("right"); pan.key("right")              # the egg license counter never closes
    assert pan._tabs()[pan.tab] == "egg" and not pan._shelves_closed()
    pan.key("tab")                                  # ...and neither does your bag
    assert pan._rows() is not None and not pan._shelves_closed()
    p.world_seconds = 6 * 60.0                      # opening bell
    pan2 = ShopPanel(p)
    assert shop.home_shop_open(p) and pan2._rows()


def test_shop_draws_its_own_closed_plate():
    """When the shelves are shut, the icon cell shows tuipet's drawn CLOSED
    plate and the info column carries the trading hours (the old sprite blurred
    into noise at this size, so the shop draws its own sign now)."""
    from tuipet.shopscreen import ShopPanel
    p = _pet()
    p.world_seconds = 3 * 60.0                      # 3am, shutters down
    body = ShopPanel(p).text().plain
    assert "CLOSED" in body
    assert "Open 6:00" in body


def test_effect_line_fits_the_info_column():
    """Every consumable's effect readout fits the info column beside the icon
    and never prints a rounds-to-zero stat like 'en+0'."""
    from tuipet import shop, data
    tw = 38 - 10 - 2                               # W - IC_W - 2
    for e in data.home_shop_pool():
        el = shop.effect_line(e)
        assert len(el) <= tw, (e["name"], el)
        assert "+0" not in el and "-0" not in el, (e["name"], el)


def test_uniform_attribute_boost_collapses_to_one_token():
    """A uniform Vaccine/Data/Virus nudge reads as one 'attr' token so the
    busiest foods stay on a single line; a mixed nudge stays spelled out."""
    from tuipet import shop
    uni = shop.effect_line({"hunger": 2, "mood": 20, "vaccine": 1, "data": 1, "virus": 1})
    assert "attr+1" in uni and "Va+1" not in uni
    mix = shop.effect_line({"mood": 50, "vaccine": -15, "virus": 15})
    assert "Va-15" in mix and "Vi+15" in mix and "attr" not in mix
