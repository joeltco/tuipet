"""Adventure rebuild — TRAVEL DRAIN (phase 6, 2026-07-20).

Pins the march's toll: each leg tires (energy), burns the calorie buffer (weight
trims toward the species base) and tops the effort gauge -- so a run comes home
spent.  The drain lands on marched STEPS only, not on encounter/boss legs.
"""
import pytest

from tuipet import adventure
from tuipet.adventure import (Adventure, WALK_DRAIN_EVERY, TRAVEL_EFFORT_CAP,
                              INTERACTIVE_STEPS)
from tuipet.adventurescreen import AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _bossless():
    return {"name": "Testfield", "scene": "greenhills",
            "steps": INTERACTIVE_STEPS, "randoms": [], "bosses": []}


def test_marching_tires_the_pet(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    p = _pet()
    p.strength = 1
    e0 = p.energy
    a = Adventure(p, zone=_bossless())
    for _ in range(a.total):
        a.travel()
    assert p.energy == e0 - a.total // WALK_DRAIN_EVERY   # one tick every N legs
    assert p.strength == TRAVEL_EFFORT_CAP               # walking tops the effort gauge


def test_marching_trims_weight_toward_base_never_below(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    p = _pet()
    p._set_weight(p._base_weight() + 6)
    w0 = p.weight
    a = Adventure(p, zone=_bossless())
    for _ in range(a.total):
        a.travel()
    assert p._base_weight() <= p.weight < w0             # trimmed, floored at base


def test_energy_floors_at_zero(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    p = _pet()
    p._set_energy(2)
    a = Adventure(p, zone=_bossless())
    for _ in range(a.total):
        a.travel()
    assert p.energy == 0                                 # never negative


def test_encounter_legs_do_not_drain(monkeypatch):
    # force every leg to be an encounter -> no step advances, so no drain
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)
    p = _pet()
    e0, s0 = p.energy, p.strength
    a = Adventure(p, zone=_bossless())
    for _ in range(6):
        a._immunity = 0
        r = a.travel()
        assert isinstance(r, tuple) and r[0] == "encounter"
        a.resolve(True)                                  # win, keep rolling encounters
    assert p.energy == e0 and p.strength == s0 and a.loc == 0   # nothing marched, nothing drained


def test_the_energy_reads_live_on_the_road_card(monkeypatch):
    """The tank rode the strip as a bare '⚡N' until v0.5.328 thinned that
    line to its keys; it is a labelled row on the ROAD CARD now."""
    from conftest import road_card
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    pan = AdventurePanel(_pet())
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.travelling:
            break
    assert f"Energy {pan.pet.energy}" in road_card(pan)   # live while marching
    assert "⚡" not in pan.strip()                        # ...and OFF the strip


def test_the_energy_floor_law_spend_vs_knock():
    """D3 ruling 2026-07-23 -- THE ENERGY FLOOR LAW: a SPEND floors at
    zero, a KNOCK pushes past it.  Marching (pinned above) and battling
    are exertion the pet chooses to pay -- an empty tank can't fund them;
    a hazard pounce is DAMAGE, the one road source of negative energy,
    and negative energy is what plants the pet's feet."""
    p = _pet()
    p._set_energy(3)
    p.record_battle(True)                        # a battle SPENDS...
    assert p.energy == 0                         # ...flooring at empty
    a = Adventure(p, zone=_bossless())
    a.hazard_hit()                               # a pounce KNOCKS...
    assert p.energy == -adventure.HAZARD_ENERGY  # ...past empty, unfloored


def test_an_empty_tank_already_fights_worse():
    """D2 ruling 2026-07-23 (keep, now pinned): the energy audit's
    "fighting at 0 has no consequence" was the board overstating --
    Side._condition bills the energy meter into every hit roll, a full
    ten-point swing between a fresh tank and an empty one (and the coach
    line calls it out)."""
    from tuipet.battle import Side
    p = _pet()
    foe = Side.wild(p.num)
    p._set_energy(p.max_energy)
    fresh = Side.of_pet(p).hit_chance(foe)
    p._set_energy(0)
    empty = Side.of_pet(p).hit_chance(foe)
    assert fresh - empty == pytest.approx(0.1)   # the meter's real bill


def test_the_wound_line_is_named_when_you_cross_it(monkeypatch):
    """ROAD ITEM AUDIT 2026-07-31 (Joel: "fix 2 somehow, your call").

    Energy READ as decorative on the road: the floor law keeps every drain at
    0 and `stop_travel_prob` only plants a pet at -1 or below, which nothing
    but an unducked hazard pounce reaches.  But `record_battle` calls a body
    "bad" under BATTLE_MIN_ENERGY and rolls the injury table at bad_nv (10% a
    bout) instead of good_nv (0.3%) -- and measured over 600 runs, HALF of all
    road fights happen under that line.  Nothing named it.  No number moved;
    the road SAYS it, once per crossing, on the transient-verdict channel the
    transports already use."""
    from tuipet.petbase import BATTLE_MIN_ENERGY
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_pet())
    pan._trans, pan._landed, pan.travelling = None, True, True
    pan.pet._set_energy(BATTLE_MIN_ENERGY + 2)
    pan.anim()
    assert not pan._note                                # above the line: silent
    pan.pet._set_energy(BATTLE_MIN_ENERGY - 1)
    pan.anim()
    assert "wounds come easy" in pan._note and pan._note_t > 0
    # ...ONCE.  a tank sliding further down must not re-nag every frame
    pan._note, pan._note_t = "", 0
    for e in (4, 3, 0, -1):
        pan.pet._set_energy(e)
        pan.anim()
    assert not pan._note
    # a rest lifts it back over in silence, and a fresh fall speaks again
    pan.pet._set_energy(BATTLE_MIN_ENERGY + 4)
    pan.anim()
    assert not pan._note
    pan.pet._set_energy(BATTLE_MIN_ENERGY - 1)
    pan.anim()
    assert "wounds come easy" in pan._note
    # THE CELL LAW: the note branch appends the hearts (a 36-char first draft
    # measured 40/40 -- no margin)
    from rich.cells import cell_len
    from rich.text import Text
    from tuipet.adventurescreen import STRIP_W
    pan.adv.lives = 1
    assert cell_len(Text.from_markup(pan.strip()).plain) <= STRIP_W - 4


def test_a_pet_that_left_home_spent_does_not_open_with_the_nag(monkeypatch):
    """The latch arms at the state the run STARTS in: setting out already
    under the line is not a crossing, and the road must not greet it with a
    verdict it did nothing to earn."""
    from tuipet.petbase import BATTLE_MIN_ENERGY
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    p = _pet()
    p._set_energy(BATTLE_MIN_ENERGY - 3)
    pan = AdventurePanel(p)
    pan._trans, pan._landed, pan.travelling = None, True, True
    for _ in range(20):
        pan.anim()
    assert "wounds come easy" not in (pan._note or "")
