"""Adventure rebuild — TOWNS (phase 7, 2026-07-20).

Pins the mid-zone rest waypoint: passing a town refills adventure lives and
some energy, suppresses encounters on its ground, fires ONCE per span, and the
panel pauses to rest there.  Town spans come from data.load_maps z['towns']
mapped onto the ~40 interactive legs.
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES, MAX_LIVES, TOWN_REST_ENERGY
from tuipet.adventurescreen import (AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T,
                                    TRAVEL_TICKS, TOWN_HOLD)
from tuipet.pet import Pet


def _pet(num=100):
    return Pet(num=num, stage="Champion", attribute="Vaccine", obedience=500)


def _town_zone():
    return next(z for z in ZONES if z["town_legs"])


def test_every_real_zone_ships_a_town_waypoint():
    assert all(z["town_legs"] for z in ZONES)          # 26/26 have a rest stop
    for z in ZONES:
        for a, b, _tid in z["town_legs"]:
            assert 0 <= a <= b < adventure.INTERACTIVE_STEPS   # inside the crossing


def test_reaching_the_town_refills_lives_and_energy(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    z = _town_zone()
    p = _pet()
    a = Adventure(p, zone=z)
    a.lives = 1                                         # entered battered
    town_lo = z["town_legs"][0][0]
    hit = False
    for _ in range(a.total):
        e_before = p.energy
        r = a.travel()
        if r == "town":
            hit = True
            assert a.loc == town_lo
            assert a.lives == MAX_LIVES                 # lives refilled
            assert p.energy >= e_before                 # energy topped, not lost
            break
    assert hit


def test_the_town_fires_only_once_per_span(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    z = _town_zone()
    a = Adventure(_pet(), zone=z)
    towns = sum(1 for _ in range(a.total) if a.travel() == "town")
    assert towns == len(z["town_legs"])                # one rest per town, not per leg


def test_town_ground_suppresses_encounters(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)   # every leg would fight
    z = _town_zone()
    a = Adventure(_pet(), zone=z)
    a.loc = z["town_legs"][0][0]
    assert a._in_town(a.loc)
    assert a._roll_encounter() is None                 # ...but the town is safe


def test_the_panel_stops_at_the_town_to_visit_or_walk_on(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_pet())
    # march until the panel stands at the town waypoint
    stopped = False
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 40):
        pan.anim()
        if pan._town_prompt:
            stopped = True
            assert "town" in pan.strip().lower() and "visit" in pan.strip().lower()
            break
        if pan._fighting_boss:
            break
    assert stopped                                     # it stopped at the town
    # ENTER opens the hub; SPACE walks on
    pan.key("enter")
    assert type(pan.sub).__name__ == "TownPanel" and pan._town_sub
    pan.key("escape")                                  # leave the hub
    assert pan.sub is None and not pan._town_prompt


def test_the_town_hub_opens_the_shop_and_leaves():
    """T1 town hub (2026-07-20): a visitable stop -- the real ShopPanel (same
    layout as home) rides as a child; Leave / ESC returns to the road."""
    from tuipet.townscreen import TownPanel
    t = TownPanel(_pet(), town_id=0)
    assert "TOWN" in t.text().plain and "Shop" in t.text().plain
    # ENTER on Shop opens the REAL home ShopPanel (reused, not a rebuild)
    t.key("enter")
    assert type(t.sub).__name__ == "ShopPanel"
    assert t.text() is t.sub.text() or t.strip() == t.sub.strip()   # delegates to it
    # closing the shop returns to the town menu (not out of the town)
    t.sub = None
    t._sub_done(None)
    assert t.sub is None
    # move to Leave, ENTER -> back to the road
    from tuipet.townscreen import _MENU
    t.cursor = next(i for i, m in enumerate(_MENU) if m[0] == "leave")
    assert t.key("enter") == ("done", None)
    # ESC from the menu also leaves
    assert TownPanel(_pet(), 0).key("escape") == ("done", None)


def test_the_town_sell_slot_opens_the_bag():
    """T2 Sell (2026-07-20): the real ShopPanel bag (use / sell back), same
    layout as the home bag -- reused, not rebuilt."""
    from tuipet.townscreen import TownPanel, _MENU
    p = _pet()
    p.add_item("ball")
    t = TownPanel(p, 0)
    t.cursor = next(i for i, m in enumerate(_MENU) if m[0] == "sell")
    t.key("enter")
    assert type(t.sub).__name__ == "ShopPanel"
    assert t.sub.mode == "bag" and t.sub.bag_only     # use/sell only, no buying
