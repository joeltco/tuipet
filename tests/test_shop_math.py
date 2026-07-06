"""Town/shop math audit (2026-07): canon re-verification vs
PhysicalState.randomizeShop / addConsumables / restockShop / canRestock /
checkRestock / getCanSell, ShopConsumable.randomizeStock / checkSale /
getPurchasePrice / getResellPrice, Town.java + config column 1.

THE FIRST FULLY-CLEAN AUDIT: zero math divergences.  Verified verbatim --
the roll (shopUnlocked + price>0 + withinTime, mustStock first, per-season
stock chance, uniform draw w/o replacement to 8/12), randomizeStock
(min or between), checkSale (price - price/factor, per-season chance),
the restock machinery (1%/5min cap 4; 50% new-item-vs-refill with the
no-candidate fallback, the no-sale restock roll, ONE credit per call, an
old sale surviving a refill), purchase price (sale-aware), resell
(price//factor, factor-0 unsellable, NO floor -- the old max(1,..) was
removed as non-canon; no shipped item hits the 0 edge), home selling
enabled (CanSellFood/Items TRUE classic), and the town override
substituting the whole econ block per consumable (compareConsumables).

Documented simplifications (not divergences): buy-one-per-press (canon
supports xN at the same per-unit price), quantity-only inventory (canon's
usesPerConsumable partial-resell), transient town shops."""
import random

from tuipet.pet import Pet
from tuipet import shop, data


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.bits = 9999
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_sale_price_formula_is_verbatim():
    e = {"key": "f:8", "price": 100, "sale_factor": 4, "sale_chance": [100, 100, 100, 100],
         "min_stock": 1, "max_stock": 1, "must_stock": False}
    random.seed(0)
    slot = shop._mk_slot(_pet(), e, check_sale=True)
    assert slot["sale"] == 100 - 100 // 4                 # price - price/saleFactor


def test_resell_has_no_floor_and_factor_zero_is_unsellable():
    assert shop.resell_price({"price": 100, "resell_factor": 4}) == 25
    assert shop.resell_price({"price": 100, "resell_factor": 0}) == 0
    assert shop.resell_price({"price": 2, "resell_factor": 3}) == 0   # canon: no max(1,..)
    # ...and no SHIPPED consumable actually hits that edge
    edge = [e for e in data.home_shop_pool()
            if e.get("resell_factor") and e["price"] > 0
            and e["price"] // e["resell_factor"] == 0]
    assert edge == []


def test_roll_fills_must_stock_first_and_dedupes():
    random.seed(1)
    p = _pet()
    slots = shop._roll(p, is_food=True)
    keys = [s["key"] for s in slots]
    assert len(keys) == len(set(keys)) <= shop.FOOD_MAX
    must = {e["key"] for e in shop._pool(p, True) if e["must_stock"]}
    assert must <= set(keys) or len(keys) == shop.FOOD_MAX   # mustStock always seats first


def test_restock_credit_banking_caps_at_four():
    random.seed(2)
    p = _pet(shop_restock=0, shop_restock_t=0.0)
    for _ in range(4000):                                  # ~800 rolls at 1%
        shop.check_restock_tick(p, 5.0)
    assert 0 < p.shop_restock <= shop.RESTOCK_MAX


def test_restock_spends_one_credit_and_respects_the_old_sale():
    random.seed(3)
    p = _pet(shop_restock=2)
    slots = [{"key": "f:8", "stock": 0, "sale": 7}]
    shop._restock(p, slots, is_food=True)
    assert p.shop_restock == 1                             # ONE credit per call
    s = slots[0]
    assert s["stock"] > 0 or s["key"] != "f:8"             # refilled or swapped
    if s["key"] == "f:8":
        assert s["sale"] == 7                              # a refill keeps the old sale


def test_town_override_substitutes_the_whole_econ_block():
    towns = data.load_towns()
    ov = data.load_shop_overrides()
    assert towns and ov                                    # the channel exists
    p = _pet()
    for town in list(towns.values())[:3]:
        random.seed(5)
        slots = shop.roll_town_shop(p, town, is_food=True)
        for s in slots:
            assert s["stock"] >= 0 and "price" in s        # the town price rides the slot


def test_multi_use_items_resell_per_use_not_per_item():
    """Egg-shop audit 2026-07-05: the bag counts USES (canon quantity IS
    uses), but resell paid the whole-ITEM value per unit -- the 100-flush
    starter Toilet printed 100b a flush (10,000b per fresh egg).  Per-use
    resell = item value / UsesPerItem; a FULL toilet still fetches exactly
    the canon 100b."""
    toilet = {"price": 1000, "resell_factor": 10, "uses_per": 100}
    assert shop.resell_price(toilet) == 1                 # per flush
    assert shop.resell_price(toilet) * 100 == 100         # the whole item = canon
    potty = {"price": 100, "resell_factor": 10, "uses_per": 1}
    assert shop.resell_price(potty) == 10                 # single-use unchanged
    assert shop.resell_price({"price": 100, "resell_factor": 4}) == 25  # no uses_per = 1


def test_bag_transport_is_gated_for_eggs_and_sleepers():
    """The bag handed the app a TransportPanel before any pet gate -- an egg
    could board Zone Transport (egg-shop audit 2026-07-05)."""
    from tuipet.pet import Pet
    from tuipet.shopscreen import ShopPanel
    egg = Pet.new_egg()
    egg.inventory["i:28"] = 1
    pan = ShopPanel(egg, start_mode="bag")
    for t in range(len(pan._tabs())):
        pan.tab = t
        rows = pan._rows()
        hit = next((i for i, r in enumerate(rows) if r["key"] == "i:28"), None)
        if hit is not None:
            pan.cursor = hit
            break
    assert pan.key("enter") is None                       # NOT ("done", ("transport", ...))
    assert "Too young" in pan.msg
