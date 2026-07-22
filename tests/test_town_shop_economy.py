"""The TOWN ECONOMY (shops arc, 2026-07-21: Joel — "shops, town shops,
deals").

Pins the four ordered systems on the authored data (towns.csv override
lists -> shopConsumable.csv econ -> CATALOG identities): per-town stock
(two food families = the trade map), the rotating daily deal (canon
checkSale price//SaleFactor, crc32 day-seeded), festival sales (every row
on a holiday), and buy-low/sell-high (stocked goods resell at the canon
price//ResellFactor, unstocked DEMAND pays 70% of catalog) — bounded by
the authored maxStock as a per-town DAILY cap, without which DVPet's 375b
town steak against the 2000b catalog is a money printer.
"""
import datetime

from tuipet import data, persistence, shop
from tuipet.pet import Pet

D = datetime.date(2026, 3, 3)          # an ordinary day (no festival)
FEST = datetime.date(2026, 1, 1)       # New Year — a festival day
A_TOWN, B_TOWN = 0, 4                  # one town from each authored family


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def test_the_authored_tables_load_and_split_two_families():
    towns = data.load_towns()
    assert len(towns) == 26 and len(data.load_shop_overrides()) == 22
    fams = {tuple(t["foods_override"]) for t in towns.values()}
    assert len(fams) == 2                              # the trade map
    assert all(tuple(t["items_override"]) == tuple(towns[0]["items_override"])
               for t in towns.values())                # one shared items shelf


def test_town_stock_serves_living_catalog_at_authored_prices():
    a = {e["key"]: e for e in shop.town_stock(A_TOWN, D)}
    b = {e["key"]: e for e in shop.town_stock(B_TOWN, D)}
    for stock in (a, b):
        for e in stock.values():
            assert shop.entry(e["key"])                # every row is a REAL entry
            assert e["base_price"] > 0
    assert "anti_evo_chip" in a and "anti_evo_chip" not in b
    assert "steak" in b and "steak" not in a           # the family exclusives
    # the PRICE LAW: catalog * authored ratio (steak: 2000 * 375/500)
    assert b["steak"]["base_price"] == 1500
    assert a["anti_evo_chip"]["base_price"] == 500     # chips: authored HALF


def test_no_town_price_undercuts_the_home_flip():
    """The printer audit: every town's every NON-DEAL price stays at or
    above the home resale, so buy-in-town/sell-at-home never profits."""
    for tid in data.load_towns():
        for e in shop.town_stock(tid, D):
            assert e["base_price"] >= shop.resell_price(shop.entry(e["key"]))


def test_the_rotating_deal_is_one_a_day_and_canon_half():
    stock = shop.town_stock(A_TOWN, D)
    deals = [e for e in stock if e["deal"]]
    assert len(deals) == 1                             # ONE deal, not a sale rack
    d = deals[0]
    assert d["price"] == d["base_price"] // 2          # canon checkSale, factor 2
    again = [e["key"] for e in shop.town_stock(A_TOWN, D) if e["deal"]]
    assert again == [d["key"]]                         # stable all day
    sids = {shop.town_deal_sid(A_TOWN, D + datetime.timedelta(days=i))
            for i in range(14)}
    assert len(sids) > 1                               # ...and it ROTATES


def test_a_festival_puts_the_whole_counter_on_sale():
    stock = shop.town_stock(A_TOWN, FEST)
    assert stock and all(e["deal"] for e in stock)
    assert all(e["price"] == e["base_price"] // 2 for e in stock)


def test_the_sell_spread_is_the_trade_game():
    # a B-town pays a pittance for its OWN steak (canon local//ResellFactor)...
    assert shop.town_sell_price("steak", B_TOWN) == 1500 // 10
    # ...an A-town, which never stocks it, pays DEMAND: 70% of catalog
    cat = shop.entry("steak")["price"]
    assert shop.town_sell_price("steak", A_TOWN) == cat * 7 // 10
    # home stays the flat half — and a town-priced bag row overrides it
    assert shop.resell_price(shop.entry("steak")) == cat // 2
    assert shop.resell_price(dict(shop.entry("steak"), sell_price=42)) == 42


def test_the_daily_stock_cap_stops_the_money_printer():
    p = _pet()
    p.bits = 50_000
    e = next(x for x in shop.town_stock(B_TOWN, D, pet=p) if x["key"] == "steak")
    assert e["left"] == 3                # min(authored maxStock 50, tuipet cap)
    for i in range(3):
        msg, sfx = shop.town_buy(p, e, today=D)
        assert sfx == "confirm"
        e = next(x for x in shop.town_stock(B_TOWN, D, pet=p)
                 if x["key"] == "steak")
    assert p.inventory.get("steak") == 3
    assert e["left"] == 0                              # the shelf is bare
    msg, sfx = shop.town_buy(p, e, today=D)
    assert sfx == "error" and "Sold out" in msg
    # a new day restocks; the ledger survives a save round trip
    d = persistence.to_save_dict(p)
    q, _msg = persistence.pet_from_save(d)
    assert q.town_bought == p.town_bought
    e3 = next(x for x in shop.town_stock(B_TOWN, D + datetime.timedelta(days=1),
                                         pet=q) if x["key"] == "steak")
    assert e3["left"] == 3


def test_the_town_panel_serves_the_counter(monkeypatch):
    from tuipet import tournament
    from tuipet.shopscreen import ShopPanel
    monkeypatch.setattr(tournament, "_today", lambda: D)
    p = _pet()
    p.bits = 10_000
    pan = ShopPanel(p, town_id=B_TOWN)
    assert pan._tabs() == ["Food", "Items"]            # no eggs/honors in town
    pan.tab = 0                                        # the Food shelf
    rows = pan._rows()
    assert [e["key"] for e in rows] == ["steak"]
    bits0 = p.bits
    pan.key("enter")                                   # buy at the LOCAL price
    assert bits0 - p.bits == rows[0]["price"]
    pan.key("enter"), pan.key("enter")                 # drain the daily cap
    assert "out" in pan.text().plain                   # the shelf shows it
    # the town bag pays the town's rates
    bag = ShopPanel(p, start_mode="bag", bag_only=True, town_id=A_TOWN)
    row = next(e for e in bag._rows() if e["key"] == "steak")
    assert row["sell_price"] == shop.town_sell_price("steak", A_TOWN)
    bits1 = p.bits
    bag.cursor = next(i for i, e in enumerate(bag._rows()) if e["key"] == "steak")
    bag.key("r")                                       # sell into A-town demand
    assert p.bits - bits1 == shop.town_sell_price("steak", A_TOWN)


def test_every_town_keeps_one_standing_guest_good():
    """Gameplay polish #24 (2026-07-22): after catalog mapping the 26
    counters collapsed to TWO variants one SKU apart.  Each town now keeps
    ONE crc32-picked guest from the ungated catalog -- permanent per town
    (the daily deal rotates; a town's character doesn't), never the
    map-gated Adventure shelf, at flat catalog price (no printer)."""
    guests = {}
    for tid in data.load_towns():
        rows = shop._town_rows(tid)
        g = [(sid, k, o, local) for sid, k, o, local in rows
             if str(sid).startswith("guest:")]
        assert len(g) == 1, tid
        sid, k, o, local = g[0]
        e = shop.entry(k)
        assert e["category"] != "Adventure"          # the gate holds
        assert local == shop.CATALOG[k][2]           # flat catalog price
        assert shop._town_rows(tid)[-1][1] == k      # stable across calls
        guests[tid] = k
    assert len(set(guests.values())) > 2             # real variety landed


def test_the_first_generation_starts_with_pocket_money():
    """Gameplay polish #23: gen-1 started at 0 bits with every faucet
    gated (adventure needs Rookie, cups need a stake).  250 opens the
    first Rookie stake or one treat; heirs inherit the estate instead."""
    p = Pet.new_egg(generation=1)
    assert p.bits == 250
