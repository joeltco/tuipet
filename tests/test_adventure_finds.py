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
    assert p.inventory.get(key, 0) == before + 1       # in the bag AT ONCE --
    #                                                    the beats that follow
    #                                                    are pure presentation
    assert pan._find is None and pan._scene is not None


def test_the_discover_sequence_plays_out_and_resumes_the_march(monkeypatch):
    """The restored old-build investigateLeft playbook: ENTER on a glint walks
    the mon OUT to the left goal, digs under suspense dots, unseals the "Dug
    up X!" verdict (with the reward chime) at the reveal, carries the find
    back, and puts the mon back on the road -- input locked throughout (no
    skips: own-game law)."""
    from tuipet.adventurescreen import (INV_WALK_T, INV_REVEAL_T, INV_END_T)
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    pan = AdventurePanel(_pet(), zone=_find_zone())
    _to_travelling(pan)
    _spot(pan)
    pan.key("enter")
    saw_dots = saw_reveal = False
    chimed = False
    for _ in range(INV_END_T + 2):
        pan.anim()
        assert pan.text()                              # every beat renders clean
        if pan._scene is None:
            break
        t = pan._scene["t"]
        pan.key("escape")                              # locked: ESC must NOT go home
        assert pan._trans is None and pan._scene is not None
        if INV_WALK_T <= t < INV_REVEAL_T:
            saw_dots = saw_dots or "." in pan.strip()
        if t >= INV_REVEAL_T:
            saw_reveal = saw_reveal or "Dug up" in pan.strip()
        chimed = chimed or pan.sfx == "reward"
    assert saw_dots and saw_reveal and chimed
    assert pan._scene is None and pan.travelling       # back on the road


def test_the_glint_wears_the_attention_bounce(monkeypatch):
    """Waiting at a glint, the mon plays the DiscoverCall attention bounce
    (happy poses) instead of a mute stand -- restored old-build behavior."""
    from tuipet import menu
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    pan = AdventurePanel(_pet(), zone=_find_zone())
    _to_travelling(pan)
    _spot(pan)
    calls = []
    real = menu.paint
    monkeypatch.setattr(menu, "paint",
                        lambda pl, *a, **k: (calls.append((pl, k)), real(pl, *a, **k))[1])
    pan.frame_i = 0
    pan.text()
    pan.frame_i = 6                                    # the other bounce beat
    pan.text()
    (pl1, k1), (pl2, k2) = calls
    assert pl1[0][0] != pl2[0][0]                      # pose flips (5 <-> 7)
    assert k1.get("overlay")                           # the "!" rides the beat


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
