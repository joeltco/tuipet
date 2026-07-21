"""Adventure rebuild — FINDS / investigate (phase 9, 2026-07-20).

Pins the loot roll: a marched step may spot a find from the zone's own loot
table (rand_items/rand_foods); the player digs it into the bag or walks on;
towns are safe rest, not scavenging (no finds).
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES
from tuipet.adventurescreen import AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _find_zone():
    return next(z for z in ZONES if z["find_keys"])


def _to_travelling(pan):
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.travelling:
            return


def _spot(pan):
    for _ in range(60):
        pan.anim()
        if pan._find is not None:
            return pan._find
    raise AssertionError("no find spotted")


def test_every_real_zone_has_a_loot_pool_of_named_consumables():
    from tuipet import shop
    for z in ZONES:
        assert z["find_keys"]                          # 26/26 have loot
        for k in z["find_keys"]:
            # CATALOG keys -- real, bag-renderable, use_item-usable loot
            assert shop.entry(k) and shop.entry(k)["name"]


def test_a_find_comes_from_the_zone_pool_after_the_step(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    z = _find_zone()
    a = Adventure(_pet(), zone=z)
    r = a.travel()
    assert isinstance(r, tuple) and r[0] == "find"
    assert r[1] in z["find_keys"]                      # from THIS zone's loot
    assert a.loc == 1                                  # the leg advanced; the find is a bonus


def test_towns_have_no_finds(monkeypatch):
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    z = _find_zone()
    a = Adventure(_pet(), zone=z)
    a.loc = z["town_legs"][0][0]
    assert a._in_town(a.loc)
    assert a._roll_find() is None                      # resting ground, not loot


def test_digging_a_find_drops_it_in_the_bag(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    p = _pet()
    pan = AdventurePanel(p, zone=_find_zone())
    _to_travelling(pan)
    key = _spot(pan)
    assert "glint" in pan.strip().lower()              # the dig/pass prompt
    before = p.inventory.get(key, 0)
    pan.key("enter")                                   # dig
    assert p.inventory.get(key, 0) == before + 1       # in the bag
    assert pan._find is None and "Dug up" in pan.strip()


def test_passing_a_find_leaves_it_and_the_bag_alone(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    p = _pet()
    pan = AdventurePanel(p, zone=_find_zone())
    _to_travelling(pan)
    key = _spot(pan)
    before = p.inventory.get(key, 0)
    pan.key("space")                                   # walk on
    assert pan._find is None
    assert p.inventory.get(key, 0) == before           # nothing taken


def test_find_chance_zero_never_spots(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    a = Adventure(_pet(), zone=_find_zone())
    assert all(a.travel() != "find" for _ in range(a.total - 1))  # up to the boss gate
