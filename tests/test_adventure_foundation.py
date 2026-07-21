"""Adventure rebuild — FOUNDATION (2026-07-20).

Pins the skeleton: the menu action, the can_adventure() gate, and the real
canon teleport carried verbatim (leave -> arrive, both directions) that a mode
opens on, stands after, and rides home on ESC.  The march/encounter/boss engine
is a later phase and is deliberately absent here.
"""
from tuipet.adventurescreen import AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T
from tuipet.pet import Pet


def _champ():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def test_the_adventure_action_is_wired_into_the_explore_group():
    from tuipet.app import TuiPetApp
    keys = {b[0]: (b[1], b[2]) for b in TuiPetApp.BINDINGS}
    assert keys["a"] == ("adventure", "Adventure")     # the historic key, free again
    # sits in EXPLORE, ahead of Raid (flagship PvE feature leads the group)
    order = [b[1] for b in TuiPetApp.BINDINGS]
    assert order.index("adventure") < order.index("raid") < order.index("tournament")


def test_the_gate_matches_the_raid_gate_shape():
    assert Pet.new_egg().can_adventure() == "It is still an egg."
    p = _champ(); p.dead = True
    assert "new egg" in p.can_adventure()
    p = Pet(num=1, stage="Fresh", attribute="Vaccine")
    assert "young" in p.can_adventure().lower()
    p = _champ(); p.asleep = True
    assert p.can_adventure() is not None                # a sleeper is disturbed
    assert _champ().can_adventure() is None             # a healthy champ may go


def test_leaving_home_rides_the_teleport_and_lands_on_the_road():
    p = _champ()
    pan = AdventurePanel(p)
    assert pan._trans == {"dir": "in", "phase": "leave", "t": 0}
    # the teleport owns the screen -- input is held until it lands
    assert pan.key("escape") is None and pan._trans is not None
    seen_leave = seen_arrive = False
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        assert pan.text()                               # every frame renders (no markup crash)
        _ = pan.strip()
        if pan._trans:
            seen_leave |= pan._trans["phase"] == "leave"
            seen_arrive |= pan._trans["phase"] == "arrive"
        if pan.auto_close:
            break
    assert seen_leave and seen_arrive                   # both halves of the wipe played
    assert pan._trans is None and pan._landed is True   # standing on the road
    assert pan.auto_close is None                       # arriving does NOT close


def test_esc_rides_the_same_teleport_home_and_auto_closes():
    p = _champ()
    pan = AdventurePanel(p)
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):   # land first
        pan.anim()
        if pan._trans is None:
            break
    pan.key("escape")
    assert pan._trans == {"dir": "out", "phase": "leave", "t": 0}
    closed = None
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 5):
        pan.anim()
        assert pan.text()
        if pan.auto_close:
            closed = pan.auto_close
            break
    assert closed[0] == "done"                          # the homecoming closes the mode
    assert "back" in closed[1].lower()                  # ...carrying the turned-back verdict


def test_the_teleport_fires_its_canon_sound_cues():
    p = _champ()
    pan = AdventurePanel(p)
    heard = set()
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.sfx:
            heard.add(pan.sfx); pan.sfx = None
        if pan.auto_close:
            break
    assert {"strongHit", "attackHit", "attack"} <= heard   # the leave+arrive cues
