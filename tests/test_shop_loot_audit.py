"""The shop + loot audit, 2026-10-14 (Joel: "a full blown logical shop and
loot audit. Grow capsules should be rare ... Daily sales, etc." -> "Fix all").
Each test pins one ruling; each fails on the code before it."""
import calendar
import datetime
import os
import sys

from tuipet import adventure as A, shop
from tuipet.pet import Pet

D = datetime.date(2026, 10, 14)
TOWNS = range(len(A.MAPS))


def _buyer(bits=10 ** 9):
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.bits = bits
    return p


def _row(rows, key):
    return next((r for r in rows if r["key"] == key), None)


def test_the_capsule_is_one_a_day_across_every_counter_deal_or_not():
    """CRITICAL: a spent capsule deal fell back to unlimited 100b boxes worth
    ~487b each."""
    p = _buyer()
    assert shop.CATALOG["capsule_a"].price == 1500
    assert not shop.deal_ok("capsule_a")
    home = _row(shop.home_stock(D, p), "capsule_a")
    assert home["left"] == 1
    assert shop.town_buy(p, home, today=D)[1] == "confirm"
    assert _row(shop.home_stock(D, p), "capsule_a")["left"] == 0
    assert shop.town_buy(p, home, today=D)[1] == "error"
    for t in TOWNS:                                  # and no town sells a second
        r = _row(shop.town_stock(t, D, p), "capsule_a")
        assert r is None or r["left"] == 0
    assert p.inventory.get("capsule_a") == 1


def test_grow_capsules_are_never_sold_or_gifted_only_won():
    v = shop.CATALOG["grow_capsule"]
    assert v.price is None
    days = [D + datetime.timedelta(i) for i in range(30)]
    assert all("grow_capsule" not in shop.home_band(d) for d in days)
    assert all(shop.home_deal_key(d) != "grow_capsule" for d in days)
    assert all(_row(shop.town_stock(t, D), "grow_capsule") is None for t in TOWNS)
    assert "grow_capsule" in Pet._GIFT_BANNED
    won = [i for i, m in enumerate(A.MAPS) if "grow_capsule" in m["reward"]]
    assert won == [6, 22]                            # maps 7 and 23, first clear


def test_one_grow_capsule_per_stage():
    p = Pet.new_egg(egg_type=0)
    p._hatch_into_fresh()
    p.inventory = {"grow_capsule": 3}
    p.use_item("grow_capsule")
    assert p.inventory["grow_capsule"] == 2
    p.use_item("grow_capsule")
    assert p.inventory["grow_capsule"] == 2          # refused, kept


def test_relics_are_rare_dear_and_one_a_day():
    for k in shop.RELICS:
        v = shop.CATALOG[k]
        assert v.price == 6000 and v.tier == "rare" and k in shop.GLOBAL_DAILY
        assert k in Pet._GIFT_BANNED
    rookie = [t for t in TOWNS if A.MAPS[t]["tier"] in ("Rookie", "Champion")]
    assert all(_row(shop.town_stock(t, D), k) is None
               for t in rookie for k in shop.RELICS)
    assert all(_row(shop.town_stock(t, D), "x_antibody") is None for t in rookie)


def test_the_battle_wards_burn_on_the_road_and_in_the_arena():
    """A "24-hour" Vitamin G lasted unlimited runs behind the paused menu."""
    p = Pet(num=399, stage="Mega", attribute="Vaccine")
    p.ward_lapse = p.tonic_lapse = p.vitamin_lapse = 1440.0
    for _ in range(24):
        p.record_battle(True)
    assert p.ward_lapse == p.tonic_lapse == p.vitamin_lapse == 0.0
    run = A.Adventure(_buyer(), A.MAPS[0])
    run.pet.ward_lapse = 10.0
    for _ in range(40):
        run.travel()
        if run.done:
            break
    assert run.pet.ward_lapse < 10.0


def test_the_care_erasers_work_once_a_life():
    p = Pet.new_egg(egg_type=0)
    p._hatch_into_fresh()
    p.energy = p.max_energy
    p.inventory = {"cold_compress": 2, "miracle_drink": 2}
    p.care_mistakes = 2
    p.use_item("cold_compress")
    p.use_item("cold_compress")
    assert p.care_mistakes == 1 and p.inventory["cold_compress"] == 1
    p.care_mistakes = 3
    p.use_item("miracle_drink")
    p.care_mistakes = 3
    p.use_item("miracle_drink")
    assert p.care_mistakes == 3 and p.inventory["miracle_drink"] == 1


def test_bought_power_is_one_chip_a_day_and_capped_per_life():
    p = _buyer()
    mega = next(t for t in TOWNS if A.MAPS[t]["tier"] == "Mega")
    chip = _row(shop.town_stock(mega, D, p), "vaccine_chip")
    assert shop.town_buy(p, chip, today=D)[1] == "confirm"
    assert _row(shop.town_stock(mega, D, p), "vaccine_chip")["left"] == 0
    day2 = D + datetime.timedelta(1)
    g = _row(shop.town_stock(mega, day2, p), "vaccine_chip_g")
    assert shop.town_buy(p, g, today=day2)[1] == "error"     # 15 + 30 > 30
    assert p.bought_power == {"vaccine": 15}
    for k in ("hp_chip", "hp_chip_g", "omni_chip_g"):          # boss rewards only
        assert shop.CATALOG[k].price is None


def test_deals_are_a_quarter_off_and_only_everyday_goods():
    for d in (D + datetime.timedelta(i) for i in range(40)):
        assert shop.deal_ok(shop.home_deal_key(d))
    for t in TOWNS:
        for r in shop.town_stock(t, D):
            if r["deal"]:
                assert shop.deal_ok(r["key"])
                assert r["price"] == shop.deal_price(r["base_price"])


def test_one_deal_ration_across_every_counter():
    """Town hopping must not multiply one item's discount."""
    p = _buyer()
    key, n = None, 0
    for t in TOWNS:
        for r in shop.town_stock(t, D, p):
            if r["deal"] and key in (None, r["key"]):
                key = r["key"]
                while True:
                    cur = _row(shop.town_stock(t, D, p), key)
                    if not cur["deal"] or cur["left"] <= 0:
                        break
                    assert shop.town_buy(p, cur, today=D)[1] == "confirm"
                    n += 1
    assert key is not None and n <= shop.tier_stock(key)


def test_towns_price_their_own_shelves():
    prices = {shop.town_price(t, "steak", 2000) for t in TOWNS}
    assert len(prices) > 1 and min(prices) >= 2000 and max(prices) <= 2600
    assert shop.town_price(3, "shortcut", 2000) == 2000      # road tools at home price


def test_an_absent_good_resells_for_half():
    assert (shop.TOWN_DEMAND_NUM, shop.TOWN_DEMAND_DEN) == (1, 2)


def test_eggs_cost_ten_thousand_and_one_a_day(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    p = _buyer(30000)
    a, b = [i for i in shop.town_egg_stock(0)][:2]
    assert shop.egg_price(a) == 10000
    assert shop.town_egg_buy(p, a)[1] == "reward"
    assert shop.town_egg_buy(p, b)[1] == "error" and p.bits == 20000


def test_the_prices_that_undercut_their_betters_moved():
    c = shop.CATALOG
    assert c["shortcut"].price > c["life_recovery"].price
    assert c["energy_drink"].price > c["tuna"].price
    assert c["cheese_burger"].price > c["fish"].price
    assert c["food_pill"].price > c["fish"].price
    assert c["slim_drink"].price > c["ball"].price * 5
    assert c["trampoline"].price < c["skateboard"].price * 2


def test_a_forfeit_pays_no_purse_and_paid_duels_cap_at_three_an_hour():
    from tuipet import lobbybout
    src = open(lobbybout.__file__, encoding="utf-8").read()
    assert "no purse for a forfeit" in src
    assert lobbybout.BoutMixin.PAID_DUELS_PER_HOUR == 3


def test_the_raid_weekend_bonus_follows_the_raid_not_the_claim(tmp_path):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    import server
    server.RAID_PATH = str(tmp_path / "raid.json")
    server.RAID = server._load_raid()
    server._raid_rotate(now=1000.0)
    server._raid_hit("joel", 10, None, now=1001.0)
    end = server.RAID["boss"]["end"]
    server._raid_rotate(now=end + 1)
    rec = server.RAID["history"][-1]
    wed = calendar.timegm((2026, 10, 14, 12, 0, 0))
    sat = calendar.timegm((2026, 10, 17, 12, 0, 0))
    rec["ended"] = wed
    base = server._raid_award("joel")["bits"]
    r = server._raid_claim("joel", rec["id"], now=sat)        # held to Saturday
    assert r["ok"] and r["bits"] == base
