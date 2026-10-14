"""Town deals, festival discounts, daily caps and home shop behavior."""
import datetime

from tuipet import persistence, shop
from tuipet.pet import Pet

D = datetime.date(2026, 3, 3)          # an ordinary day (no festival)
FEST = datetime.date(2026, 1, 1)       # New Year — a festival day
A_TOWN, B_TOWN = 0, 4                  # one town from each authored family


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def test_no_town_price_undercuts_the_home_flip():
    """The printer audit: every town's every NON-DEAL price stays at or
    above the home resale, so buy-in-town/sell-at-home never profits."""
    from tuipet import adventure
    for tid in range(len(adventure.MAPS)):
        for e in shop.town_stock(tid, D):
            assert e["base_price"] >= shop.resell_price(shop.entry(e["key"]))


def test_the_rotating_deal_is_one_a_day_and_canon_half():
    stock = shop.town_stock(A_TOWN, D)
    deals = [e for e in stock if e["deal"]]
    assert len(deals) == 1                             # ONE deal, not a sale rack
    d = deals[0]
    assert d["price"] == shop.deal_price(d["base_price"])   # 25% off (audit 2026-10-14)
    again = [e["key"] for e in shop.town_stock(A_TOWN, D) if e["deal"]]
    assert again == [d["key"]]                         # stable all day
    sids = {shop.town_deal_sid(A_TOWN, D + datetime.timedelta(days=i))
            for i in range(14)}
    assert len(sids) > 1                               # ...and it ROTATES


def test_a_festival_puts_the_whole_counter_on_sale():
    stock = shop.town_stock(A_TOWN, FEST)
    # every everyday good, 25% off; progression goods never (audit 2026-10-14)
    assert stock and all(e["deal"] == shop.deal_ok(e["key"]) for e in stock)
    assert all(e["price"] == shop.deal_price(e["base_price"]) for e in stock if e["deal"])


def test_the_daily_stock_cap_stops_the_money_printer():
    p = _pet()
    p.bits = 50_000
    e = next(x for x in shop.town_stock(B_TOWN, D, pet=p) if x["key"] == "steak")
    # TIERED STOCK (D1, 2026-07-24): a town parts with tier-many a day --
    # min(authored maxStock, daily cap, tier cap).
    # ⭐The steak's BAND MOVED 2026-08-02 when rarity was decoupled from price:
    # at 2000b the price ladder called it rare (1 a day), but the authored
    # columns say a shop stocks it every time and carries twenty -- it is a
    # COMMON good that happens to be dear, which is precisely the case the
    # decoupling exists to express.  The cap still bites; it bites at 3.
    assert e["left"] == shop.tier_stock("steak") == 3
    for i in range(e["left"]):
        msg, sfx = shop.town_buy(p, e, today=D)
        assert sfx == "confirm"
        e = next(x for x in shop.town_stock(B_TOWN, D, pet=p)
                 if x["key"] == "steak")
    assert p.inventory.get("steak") == shop.tier_stock("steak")
    assert e["left"] == 0                              # the shelf is bare
    msg, sfx = shop.town_buy(p, e, today=D)
    assert sfx == "error" and "Sold out" in msg
    # a new day restocks; the ledger survives a save round trip
    d = persistence.to_save_dict(p)
    q, _msg = persistence.pet_from_save(d)
    assert q.town_bought == p.town_bought
    e3 = next(x for x in shop.town_stock(B_TOWN, D + datetime.timedelta(days=1),
                                         pet=q) if x["key"] == "steak")
    assert e3["left"] == shop.tier_stock("steak")


    #                                                  never a trap


def test_the_first_generation_starts_with_pocket_money():
    """Gameplay polish #23: gen-1 started at 0 bits with every faucet
    gated (adventure needs Rookie, cups need a stake).  250 opens the
    first Rookie stake or one treat; heirs inherit the estate instead."""
    p = Pet.new_egg(generation=1)
    assert p.bits == 250


# ---- daily deal: dedup + the home shop deal (2026-07-24) --------------------

def test_no_town_deal_repeats_two_days_running():
    """Joel: "dedup the town deal".  The crc32 pick compared raw indices,
    so a day that was itself bumped could be silently repeated by the next.
    Now the picks walk forward off each other -- no shelf shows the same
    deal two days in a row."""
    for t in range(26):
        if len(shop._town_rows(t)) <= 1:
            continue
        seq = [shop.town_deal_sid(t, D + datetime.timedelta(days=i))
               for i in range(45)]
        for a, b in zip(seq, seq[1:]):
            assert a != b, (t, a)


def test_the_home_shop_has_a_daily_deal():
    """Joel: "add the home daily deal".  Home stays fixed-price except for
    one rotating bargain, half off, marked like a town deal."""
    rows = shop.home_stock(D)
    deals = [e for e in rows if e.get("deal")]
    assert len(deals) == 1, "exactly one home deal a day"
    d = deals[0]
    assert d["price"] == shop.deal_price(d["base_price"])
    assert d["price"] < d["base_price"]


def test_the_home_deal_rotates_and_never_repeats():
    seq = [shop.home_deal_key(D + datetime.timedelta(days=i)) for i in range(45)]
    assert len(set(seq)) > 1, "the home deal must rotate"
    for a, b in zip(seq, seq[1:]):
        assert a != b, a


def test_the_home_deal_is_stable_within_a_day():
    assert shop.home_deal_key(D) == shop.home_deal_key(D)
    a = next(e for e in shop.home_stock(D) if e.get("deal"))["key"]
    b = next(e for e in shop.home_stock(D) if e.get("deal"))["key"]
    assert a == b


def test_the_home_deal_is_never_a_gift_or_gated_item():
    """It is dealt from the always-stocked priced goods, so the bargain is
    always something you can actually see and buy on the shelf."""
    for i in range(45):
        k = shop.home_deal_key(D + datetime.timedelta(days=i))
        assert shop.CATALOG[k].price is not None            # not a gift
        assert shop.CATALOG[k].category != "Adventure"       # not map-gated


def test_buying_the_home_deal_charges_the_cut_price():
    d = next(e for e in shop.home_stock(D) if e.get("deal"))
    p = _pet()
    p.bits = d["price"]
    msg, sfx = shop.buy(p, d)
    assert sfx == "confirm" and p.bits == 0
    assert p.inventory.get(d["key"]) == 1
