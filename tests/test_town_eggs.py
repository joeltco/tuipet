"""Themed TOWN egg shops (Joel 2026-07-09: spread eggs across shops by theme)."""
from tuipet import egg as egg_mod


def _maxed_prog():
    return {"album": set(range(1, 400)), "wins": 999, "mega_kills": 99, "max_gen": 99,
            "max_stage": 99, "xanti_ever": True, "maps": set(range(30)),
            "tourneys": set(range(300)), "last_field": "None", "last_attr": "None",
            "last_elem": "None", "last_mood": 9, "last_obed": 9, "last_xanti": True,
            "connections": 99}


def test_eggs_spread_across_themed_town_shops():
    prog, owned = _maxed_prog(), set()
    per_town = {t: set(i for i, _ in egg_mod.eggs_for_town(t, prog, owned)) for t in range(26)}
    assert sum(1 for v in per_town.values() if v) >= 20        # most towns stock eggs
    assert len({frozenset(v) for v in per_town.values()}) >= 5  # varied selections, not uniform


def test_every_buyable_egg_is_sold_in_some_town():
    prog, owned = _maxed_prog(), set()
    buyable = {i for i, _ in egg_mod.buyable_eggs(prog, owned)}
    covered = set().union(*(set(i for i, _ in egg_mod.eggs_for_town(t, prog, owned))
                            for t in range(26)))
    assert buyable, "no buyable eggs to place"
    assert buyable <= covered, "orphaned eggs not sold anywhere: %s" % (buyable - covered)


def test_home_counter_sells_no_buyable_eggs():
    from tuipet.shopscreen import ShopPanel
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 12 * 60.0
    sp = ShopPanel(p)
    while sp._tabs()[sp.tab] != "egg":
        sp.key("right")
    assert sp._rows() == []       # buyable eggs live in the town shops now
