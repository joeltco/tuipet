"""Per-town egg market (Joel 2026-07-21: "different towns sell different eggs
-- all shops feel unique" + "eggs using 8x8 sprites, all of them").  Each town
stocks a DISTINCT band of the earnable digitama, shown as the real 8x8 egg
thumbnails (downsampled x2 -- the June 21 grid); ENTER buys one outright.
"""
from tuipet import shop, egg as egg_mod, persistence, data
from tuipet.towneggscreen import TownEggPanel
from tuipet.townscreen import TownPanel, _MENU
from tuipet.pet import Pet


def _pet(bits=5000):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.bits = bits
    return p


def test_towns_stock_distinct_egg_sets():
    a, b, c = (shop.town_egg_stock(0), shop.town_egg_stock(1), shop.town_egg_stock(2))
    assert a and b and c
    assert a != b != c and a != c                      # every town is different
    # never stock a free STARTER (those are already owned)
    rules = data.load_egg_unlock()
    for t in range(6):
        for idx in shop.town_egg_stock(t):
            assert not (rules.get(idx) or {}).get("start")


def test_egg_price_charges_for_earnable_eggs():
    # a starter is free (never stocked); an earnable egg costs bits
    starter = next(i for i in range(egg_mod.count())
                   if (data.load_egg_unlock().get(i) or {}).get("start"))
    earned = shop.town_egg_stock(0)[0]
    assert shop.egg_price(starter) == 0
    assert shop.egg_price(earned) == 800


def test_the_grid_renders_real_8x8_egg_thumbnails():
    pan = TownEggPanel(_pet(), town_id=1)
    buf = pan._grid()
    lit = sum(sum(row) for row in buf)
    assert 40 < lit < 40 * 16                           # real egg pixels, not blank, not solid
    # each stocked egg is the real digitama sprite downsampled to 8x8
    from tuipet.render import downsample
    thumb = downsample(egg_mod.record(pan.stock[0])["frames"][0], 2)
    assert len(thumb) == 8 and len(thumb[0]) == 8


def test_buying_an_egg_spends_bits_and_owns_it(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    p = _pet(bits=2000)
    pan = TownEggPanel(p, town_id=0)
    idx = pan.stock[0]
    pan.i = 0
    pan._buy()
    assert p.bits == 1200                               # 2000 - 800
    assert idx in set(persistence.get_eggs_owned())     # joins the carousel
    # a second buy of the same egg is refused (already owned)
    pan._buy()
    assert p.bits == 1200


def test_buying_refused_without_bits(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    p = _pet(bits=100)
    pan = TownEggPanel(p, town_id=0)
    idx = pan.stock[0]
    pan._buy()
    assert p.bits == 100 and idx not in set(persistence.get_eggs_owned())


def test_town_hub_has_an_eggs_slot_that_mounts_the_market():
    """Shops-look-the-same (Joel 2026-07-22: 'the egg tabs in town shops
    are different than the normal shops'): the Eggs door opens the SHOP's
    own Eggs tab now -- one shop family, one layout -- with this town's
    digitama band as ordinary shelf rows."""
    from tuipet import shop
    assert any(m[0] == "eggs" for m in _MENU)
    t = TownPanel(_pet(), town_id=2)
    t.cursor = next(i for i, m in enumerate(_MENU) if m[0] == "eggs")
    t.key("enter")
    assert type(t.sub).__name__ == "ShopPanel"
    assert t.sub.town == 2                              # this town's stock
    assert t.sub._tabs()[t.sub.tab] == "Eggs"           # opens ON the band
    rows = t.sub._rows()
    assert rows and all(e.get("egg_idx") is not None for e in rows)
    assert {e["egg_idx"] for e in rows} == set(shop.town_egg_stock(2))
    # ESC leaves the market back to the town menu
    t.sub = None
    t._sub_done(None)
    assert t.sub is None
