"""Adventure rebuild — TRANSPORT items (phase 11, 2026-07-20).

Pins the two in-run warps: a Town Transport (Birdra) jumps to the town and
rests (lives + energy); a Danger Transport (Garuda) dashes toward the boss and
gets ambushed on arrival.  Both are bag items spent mid-march (press T);
Zone/Continent warps are obsolete (the zone picker replaced worldmap warping).
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES, MAX_LIVES
from tuipet.adventurescreen import AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _zone():
    return next(z for z in ZONES if z["town_legs"] and z["randoms"])


def _to_travelling(pan):
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.travelling:
            return


def test_held_transports_lists_only_run_warps():
    p = _pet()
    p.add_item("town_transport")            # Town Transport (Birdra) -- run warp
    p.add_item("i:31")            # Continent Transport (Wha) -- obsolete in-run
    a = Adventure(p, zone=_zone())
    assert a.held_transports() == ["town_transport"]       # only the run-usable one


def test_town_transport_jumps_to_the_town_and_rests():
    p = _pet()
    p.add_item("town_transport")
    p._set_energy(4)
    z = _zone()
    a = Adventure(p, zone=z)
    a.lives = 1
    town_lo = z["town_legs"][0][0]
    e_before = p.energy
    assert a.use_transport("town_transport") == "town-warp"
    assert a.loc >= town_lo                       # jumped forward to the town
    assert a.lives == MAX_LIVES                   # rested: lives full
    assert p.energy > e_before                    # ...and energy back
    assert p.inventory.get("town_transport", 0) == 0        # the ticket is spent


def test_danger_transport_dashes_to_the_boss_and_ambushes():
    p = _pet()
    p.add_item("disaster_transport")            # Disaster Transport (Garuda)
    a = Adventure(p, zone=_zone())
    r = a.use_transport("disaster_transport")
    assert isinstance(r, tuple) and r[0] == "encounter"   # an ambush
    assert a.loc >= a.total - 3                    # dashed near the boss gate
    assert p.inventory.get("disaster_transport", 0) == 0


def test_obsolete_or_unheld_transports_do_nothing():
    p = _pet()
    p.add_item("i:28")            # Zone Transport -- obsolete
    a = Adventure(p, zone=_zone())
    assert a.use_transport("i:28") is None        # not a run warp
    assert a.use_transport("town_transport") is None        # not held
    assert a.use_transport("f:9") is None         # a food, not a transport


def test_the_panel_opens_the_menu_on_T_and_uses_the_warp():
    p = _pet()
    p.add_item("town_transport")
    pan = AdventurePanel(p, zone=_zone())
    _to_travelling(pan)
    assert "T" in pan.strip()                      # the hint shows while holding one
    pan.key("t")
    assert pan._transport == ["town_transport"]             # the menu opened
    assert "Town Transport" in pan.strip()
    pan.key("enter")                               # use it
    assert pan._transport is None
    assert pan._rest_t > 0                          # the town-warp rest beat
    assert p.inventory.get("town_transport", 0) == 0


def test_a_danger_warp_from_the_panel_opens_a_fight():
    p = _pet()
    p.add_item("disaster_transport")
    pan = AdventurePanel(p, zone=_zone())
    _to_travelling(pan)
    pan.key("t")
    pan.key("enter")                               # use Disaster Transport
    assert type(pan.sub).__name__ == "BattlePanel" and pan.sub.wild
    assert pan._transport is None


def test_the_menu_cancels_on_esc():
    p = _pet()
    p.add_item("town_transport")
    pan = AdventurePanel(p, zone=_zone())
    _to_travelling(pan)
    pan.key("t")
    pan.key("escape")
    assert pan._transport is None
    assert p.inventory.get("town_transport", 0) == 1         # nothing spent
