"""Life Recovery and road item menu behavior."""
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


def test_obsolete_or_unheld_transports_do_nothing():
    p = _pet()
    p.add_item("i:28")            # Zone Transport -- obsolete
    a = Adventure(p, zone=_zone())
    assert a.use_transport("i:28") is None        # not a run warp
    assert a.use_transport("shortcut") is None        # not held
    assert a.use_transport("f:9") is None         # a food, not a transport


def test_life_recovery_restores_the_hearts_in_place():
    """THE B2 PIN (gameplay polish 2026-07-22): Life Recovery shipped in
    v0.5.114 with a home-use refusal pointing at the road ("use it on the
    road") while the road only knew the two warps -- a 1000b item with no
    code path that consumed it.  Now it heals where the pet stands."""
    p = _pet()
    p.add_item("life_recovery")
    a = Adventure(p, zone=_zone())
    a.lives = 1
    loc = a.loc
    assert "life_recovery" in a.held_transports()
    assert a.use_transport("life_recovery") == "life-recovery"
    assert a.lives == MAX_LIVES                   # hearts back to full
    assert a.loc == loc                           # no warp: healed in place
    assert p.inventory.get("life_recovery", 0) == 0         # spent
    assert "second wind" in a.last


def test_life_recovery_hides_and_refuses_at_full_hearts():
    p = _pet()
    p.add_item("life_recovery")
    a = Adventure(p, zone=_zone())
    assert a.lives == MAX_LIVES
    assert "life_recovery" not in a.held_transports()   # no dead menu row
    assert a.use_transport("life_recovery") is None     # defensive guard
    assert p.inventory.get("life_recovery", 0) == 1     # nothing wasted


def test_the_panel_uses_a_life_recovery_from_the_T_menu():
    p = _pet()
    p.add_item("life_recovery")
    pan = AdventurePanel(p, zone=_zone())
    _to_travelling(pan)
    pan.adv.lives = 1
    pan.key("t")
    assert pan._transport == ["life_recovery"]          # the menu opened
    assert "Life Recovery" in pan.strip()
    pan.key("enter")
    assert pan._transport is None
    assert pan.adv.lives == MAX_LIVES
    assert p.inventory.get("life_recovery", 0) == 0


def test_the_menu_cancels_on_esc():
    p = _pet()
    p.add_item("shortcut")
    pan = AdventurePanel(p, zone=_zone())
    _to_travelling(pan)
    pan.key("t")
    pan.key("escape")
    assert pan._transport is None
    assert p.inventory.get("shortcut", 0) == 1         # nothing spent
