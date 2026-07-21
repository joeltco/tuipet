"""Adventure rebuild — TRAVEL DRAIN (phase 6, 2026-07-20).

Pins the march's toll: each leg tires (energy), burns the calorie buffer (weight
trims toward the species base) and tops the effort gauge -- so a run comes home
spent.  The drain lands on marched STEPS only, not on encounter/boss legs.
"""
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
    p = _pet()
    p._set_weight(p._base_weight() + 6)
    w0 = p.weight
    a = Adventure(p, zone=_bossless())
    for _ in range(a.total):
        a.travel()
    assert p._base_weight() <= p.weight < w0             # trimmed, floored at base


def test_energy_floors_at_zero(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
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


def test_the_energy_pip_rides_the_march_strip(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    pan = AdventurePanel(_pet())
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.travelling:
            break
    assert "⚡" in pan.strip()                            # energy shown while marching
