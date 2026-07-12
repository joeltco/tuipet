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


def test_every_town_egg_is_sold_in_some_town():
    prog, owned = _maxed_prog(), set()
    town_eggs = {i for i, _ in egg_mod.buyable_eggs(prog, owned)
                 if egg_mod._store_of(i) == "town"}
    covered = set().union(*(set(i for i, _ in egg_mod.eggs_for_town(t, prog, owned))
                            for t in range(26)))
    assert town_eggs, "no town-exclusive eggs to place"
    assert town_eggs <= covered, "orphaned town eggs: %s" % (town_eggs - covered)


def test_home_counter_sells_the_common_eggs():
    from tuipet.shopscreen import ShopPanel
    from tuipet.pet import Pet
    from tuipet import persistence
    persistence._note_max("max_stage", 3)             # reach the milestones
    persistence.map_complete_add(0); persistence.map_complete_add(1)
    for n in range(1, 12):
        persistence.album_add(n)
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 12 * 60.0
    sp = ShopPanel(p)
    while sp._tabs()[sp.tab] != "egg":
        sp.key("right")
    egg_ids = {e["egg_idx"] for e in sp._rows()
               if e.get("egg_idx") is not None and not e.get("locked")}
    prog, owned = persistence.get_progress(), persistence.get_eggs_owned()
    assert egg_ids == {i for i, _ in egg_mod.home_eggs(prog, owned)}
    assert egg_ids and all(egg_mod._store_of(i) == "home" for i in egg_ids)


def test_egg_shelf_matches_the_towns_own_identity():
    """Split-brain regression (audit 2026-07-10): the egg shelf must use the SAME
    town->habitat derivation as the greeting/cup (world.town_compat) -- egg.py
    once anchored on the START of the town range while world.py used the midpoint,
    so Mossford greeted as a forest town while stocking City/metal eggs."""
    from tuipet import data, world
    themes = egg_mod._egg_themes()
    for tid in data.load_towns():
        flds, eles = world.town_compat(tid)
        for i, town_ids in egg_mod._town_egg_map().items():
            fld, ele = themes[i]
            matches = (fld and fld in flds) or (ele and ele in eles)
            assert (tid in town_ids) == bool(matches), \
                "town %d egg %d: shelf disagrees with the town's own biome" % (tid, i)
