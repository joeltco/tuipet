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
