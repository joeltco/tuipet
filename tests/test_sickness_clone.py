"""The DSprite sickness, rebuilt (2026-07-17).  Joel asked "dsprite didnt
have sickness?" mid-removal -- it DID: one flag, caught per game-minute from
filth or overweight, cured ONLY by the pill, with a per-minute death whisper
while it stands.  The classic machine (spell lengths, worsening, contagion,
counters, the 6h malady death) stayed removed; these pin the CLONE's rules.
"""
import random

import pytest

from tuipet.pet import (Pet, SICK_POOP_P, SICK_OVERWEIGHT_P, DEATH_SICK_P)


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_filth_sickens_at_the_clone_rate(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: SICK_POOP_P * 0.99)
    p = _pet(poop=2)
    p._tick_mortality(1.0)                        # one game-minute
    assert p.sick
    q = _pet(poop=0)
    q._tick_mortality(1.0)                        # a clean room never rolls
    assert not q.sick


def test_the_road_mess_cannot_sicken_a_traveler(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.0)
    p = _pet(poop=3, away=True)
    p._tick_mortality(1.0)
    assert not p.sick                             # countFilth reads 0 away


def test_overweight_steps_add_clone_risk(monkeypatch):
    p = _pet()
    bw = p._base_weight()
    p.weight = bw * 2                             # excess = bw -> two 0.5*bw steps
    hit = 2 * SICK_OVERWEIGHT_P
    monkeypatch.setattr(random, "random", lambda: hit * 0.99)
    p._tick_mortality(1.0)
    assert p.sick


def test_sickness_never_heals_on_its_own():
    """No spell timer: the flag stands through days of ticks -- the pill is
    the one cure (the clone's rule; the classic sickLapse left)."""
    p = _pet(sick=True)
    random.seed(4)
    for _ in range(600):
        p._tick_recovery(1.0)
    assert p.sick


def test_the_pill_cures_and_tops_up():
    p = _pet(sick=True, strength=1, energy=0, weight=20)
    p.feed_pill()
    assert not p.sick and p.strength == 2 and p.energy > 0
    # ...and a WELL pet with full gauges refuses it
    q = _pet(strength=4)
    q.energy = q.max_energy
    assert "doesn't need it" in q.feed_pill()
    # ...but a sick one with full gauges still takes the cure
    r = _pet(sick=True, strength=4)
    r.energy = r.max_energy
    r.feed_pill()
    assert not r.sick


def test_the_death_whisper_only_stands_while_sick(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: DEATH_SICK_P * 0.99)
    p = _pet(sick=True)
    assert p._tick_mortality(1.0) is True
    assert p.dead and p.death_cause == "sickness"
    q = _pet()                                     # well: the same roll is silent
    monkeypatch.setattr(random, "random", lambda: 0.0)
    q.poop = 0
    assert not q._tick_mortality(1.0) and not q.dead


def test_sick_reads_everywhere_the_clone_showed_it():
    p = _pet(sick=True)
    assert p.status_word() == "sick"
    assert p.current_mood() == "Unhappy"
    assert p.needs_care()
    assert not p.dead


def test_a_revival_never_comes_back_sick():
    p = _pet(sick=True)
    p.dead = True
    p.save_from_death()
    assert not p.sick                              # the clone's revival fix


def test_the_epitaph_tells_a_sickness_death():
    from tuipet.deathscreen import DeathPanel
    p = _pet()
    p._die("sickness")
    pan = DeathPanel(p)
    seen = ""
    for _ in range(120):
        pan.anim()
        seen += pan.strip()
    assert "of sickness" in seen
