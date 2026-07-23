"""Adventure rebuild — TRANSPORT items (phase 11, 2026-07-20).

Pins the in-run road items: a Town Transport (Birdra) jumps to the town and
rests (lives + energy); a Danger Transport (Garuda) dashes toward the boss and
gets ambushed on arrival; a Life Recovery (gameplay polish 2026-07-22) refills
the hearts where the pet stands.  All are bag items spent mid-march (press T);
Zone/Continent warps are obsolete (the zone picker replaced worldmap warping).
"""
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
    p.add_item("town_transport")
    pan = AdventurePanel(p, zone=_zone())
    _to_travelling(pan)
    pan.key("t")
    pan.key("escape")
    assert pan._transport is None
    assert p.inventory.get("town_transport", 0) == 1         # nothing spent


def test_a_town_warp_opens_the_town_doors():
    """Joel 2026-07-23: "shoukdnt town transports allow us to go to the
    shop, etc?"  A warp that lands ON town ground now raises the SAME
    visit-or-walk-on prompt a walked-in arrival gets -- ENTER opens the
    hub (shop/eggs/sell/cup doors), SPACE walks on.  Before this, the
    warp played its rest beat and marched straight past the town it
    paid a ticket to reach."""
    p = _pet()
    p.add_item("town_transport")
    pan = AdventurePanel(p, zone=_zone())
    _to_travelling(pan)
    pan.key("t")
    pan.key("enter")                              # warp: the rest beat plays
    while pan._rest_t > 0:
        pan.anim()
    assert pan._town_prompt                       # the doors are open
    assert "visit" in pan.strip()                 # the walk-in prompt, reused
    pan.key("enter")
    assert type(pan.sub).__name__ == "TownPanel"
    assert pan.sub.town_id == pan.adv.town_at(pan.adv.loc)


def test_a_warp_from_past_the_town_rests_in_place_without_doors():
    """Forward-only warping means a pet already PAST the span rests where
    it stands -- there is no town ground under it, so no prompt."""
    p = _pet()
    p.add_item("town_transport")
    z = _zone()
    pan = AdventurePanel(p, zone=z)
    _to_travelling(pan)
    pan.adv.loc = z["town_legs"][-1][1] + 1       # beyond the last span
    pan.key("t")
    pan.key("enter")
    while pan._rest_t > 0:
        pan.anim()
    assert not pan._town_prompt                   # rested in place, march on
