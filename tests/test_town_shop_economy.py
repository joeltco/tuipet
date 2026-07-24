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
    # TIERED STOCK (D1, 2026-07-24): the steak is RARE (2000b), so a town
    # parts with one a day -- min(authored maxStock, daily cap, tier cap).
    assert e["left"] == shop.tier_stock("steak") == 1
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


def test_the_town_panel_serves_the_counter(monkeypatch):
    from tuipet import tournament
    from tuipet.shopscreen import ShopPanel
    monkeypatch.setattr(tournament, "_today", lambda: D)
    p = _pet()
    p.bits = 10_000
    pan = ShopPanel(p, town_id=B_TOWN)
    # the digitama band is a real shop tab (shops-look-the-same 2026-07-22);
    # honors stay a home prestige
    assert pan._tabs() == ["Food", "Items", "Eggs"]
    pan.tab = 0                                        # the Food shelf
    rows = pan._rows()
    # steak (authored) + cake (map 1's regional specialty -- item
    # diversity audit 2026-07-23); town 4's guest is a non-food
    assert [e["key"] for e in rows] == ["steak", "cake"]
    pan.cursor = 0                                     # buy the steak
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
    # the collision-free deal (item diversity audit 2026-07-23): the old
    # per-town crc32 pick served 8 items to 2-3 towns each and made towns
    # 11+12 byte-identical shops.  Dealt without replacement now.
    assert len(set(guests.values())) == len(guests)  # unique GAME-WIDE
    assert "poison_mushroom" not in guests.values()  # a signature good is
    #                                                  never a trap


def test_the_regional_specialty_marks_every_map():
    """P4 (item diversity audit 2026-07-23): each map's towns carry ONE
    regional SKU beyond the 2-variant authored base -- the five maps read
    differently before the guest good even lands.  Map 4 (the hardest
    region) is where the Revive Floppy waits."""
    tm = shop._town_maps()
    for tid in data.load_towns():
        want = shop._MAP_SPECIALTY[tm[tid]]
        keys = [k for _sid, k, _o, _p in shop._town_rows(tid)]
        assert want in keys, (tid, want)
        # ...and the guest is never a duplicate of anything on the shelf
        assert len(keys) == len(set(keys)), tid
    assert shop._MAP_SPECIALTY[4] == "revive_floppy"
    assert len(set(shop._MAP_SPECIALTY.values())) == 5   # five distinct


def test_the_regional_row_buys_like_any_town_good():
    p = _pet()
    p.bits = 10_000
    e = next(x for x in shop.town_stock(B_TOWN, D, pet=p)
             if x["key"] == shop._MAP_SPECIALTY[shop._town_maps()[B_TOWN]])
    bits0 = p.bits
    msg, sfx = shop.town_buy(p, e, today=D)
    assert sfx == "confirm" and p.inventory.get(e["key"], 0) == 1
    assert bits0 - p.bits == e["price"]


def test_former_twin_towns_read_differently():
    """Towns 11 and 12 shared the same authored shelf AND the same guest
    good -- two byte-identical shops (audit finding F5)."""
    r11 = [k for _s, k, _o, _p in shop._town_rows(11)]
    r12 = [k for _s, k, _o, _p in shop._town_rows(12)]
    assert r11 != r12


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
    assert d["price"] == max(1, d["base_price"] // shop.HOME_DEAL_FACTOR)
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
