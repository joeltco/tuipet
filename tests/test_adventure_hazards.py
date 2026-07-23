"""Adventure polish — HAZARD DODGES (arcade arc, 2026-07-21).

Pins the ambush: a marched step may spring one of the zone's own wilds
(town ground is safe), the "!" telegraphs, SPACE inside the window ducks it
clean, eating it costs the small engine-applied energy toll — and the march
resumes either way (the beat never hangs).
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES, HAZARD_ENERGY
from tuipet.adventurescreen import (AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T,
                                    HZ_TELE_T, HZ_LUNGE_T, HZ_END_T)
from tuipet.pet import Pet

HZ_TOTAL = HZ_TELE_T + HZ_LUNGE_T + HZ_END_T


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _wild_zone():
    return next(z for z in ZONES if z["randoms"])


def _at_the_ambush(monkeypatch):
    """March until the ambush springs; returns the panel mid-telegraph."""
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 1.0)
    pan = AdventurePanel(_pet(), zone=_wild_zone())
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 60):
        pan.anim()
        if pan._hazard is not None:
            return pan
    raise AssertionError("no ambush sprang")


def test_the_engine_rolls_the_zones_own_wilds_and_towns_are_safe(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 1.0)
    z = _wild_zone()
    a = Adventure(_pet(), zone=z)
    r = a.travel()
    assert isinstance(r, tuple) and r[0] == "hazard"
    assert r[1] in z["randoms"]                        # a REAL zone wild pounces
    a.loc = z["town_legs"][0][0]
    assert a._in_town(a.loc) and a._roll_hazard() is None   # town ground is safe


def test_a_space_press_ducks_it_clean(monkeypatch):
    """SPACE inside the LUNGE window banks the duck (dodge rework
    2026-07-23: the telegraph is a WAIT beat now): no toll, the confirm
    ring at impact, and the march resumes when the beat ends."""
    pan = _at_the_ambush(monkeypatch)
    p = pan.pet
    e0 = p.energy
    assert "wait for it" in pan.strip()                # the telegraph teaches
    while pan._hazard["t"] < HZ_TELE_T:                # into the lunge
        pan.anim()
    assert "NOW" in pan.strip()                        # the window announces
    pan.key("space")
    assert pan._hazard["dodged"]
    for _ in range(HZ_TOTAL + 2):
        if pan._hazard is None:
            break
        pan.anim()
        assert pan.text()                              # every beat renders clean
        if pan._hazard and pan._hazard["t"] == HZ_TELE_T + HZ_LUNGE_T:
            assert pan.sfx == "confirm"                # the clean duck-under
    assert pan._hazard is None and pan.travelling      # back on the march
    assert p.energy == e0                              # dodged: no toll


def test_eating_the_pounce_costs_the_small_toll(monkeypatch):
    """No press: the pounce lands -- the ENGINE takes HAZARD_ENERGY off the
    tank, the hit stings, and the march still resumes (never a fight, never
    a hang)."""
    pan = _at_the_ambush(monkeypatch)
    p = pan.pet
    e0 = p.energy
    stung = False
    for _ in range(HZ_TOTAL + 2):
        if pan._hazard is None:
            break
        pan.key("escape")                              # blocked: the beat plays out
        assert pan._trans is None
        pan.anim()
        assert pan.text()
        stung = stung or pan.sfx == "attackHit"
    assert stung
    assert pan._hazard is None and pan.travelling
    assert p.energy == e0 - HAZARD_ENERGY              # the toll, engine-applied
    assert pan.sub is None                             # an ambush is not a fight


def test_a_late_press_is_no_duck(monkeypatch):
    """SPACE after impact changes nothing -- the window is the game."""
    pan = _at_the_ambush(monkeypatch)
    for _ in range(HZ_TELE_T + HZ_LUNGE_T + 1):        # ride past the impact
        pan.anim()
    assert pan._hazard["hit"]
    pan.key("space")                                   # too late
    assert not pan._hazard["dodged"]


def test_a_telegraph_press_is_too_soon_and_spends_the_duck(monkeypatch):
    """The anti-mash rule (dodge rework 2026-07-23, Joel: 'the whole space
    to dodge thing... its sloppy as fuck'): SPACE is also the hurry-the-
    march key, so the old anywhere-in-1.6s bank let the mash win dodges
    by accident.  One press per ambush now — during the telegraph it's
    TOO SOON, the duck is spent, and the pounce lands."""
    pan = _at_the_ambush(monkeypatch)
    p = pan.pet
    e0 = p.energy
    assert pan._hazard["t"] < HZ_TELE_T                # still telegraphing
    pan.key("space")                                   # the bled-in mash press
    assert pan._hazard.get("spent") and not pan._hazard["dodged"]
    assert "too soon" in pan.strip().lower()
    pan.key("space")                                   # frantic second press:
    assert not pan._hazard["dodged"]                   #   the duck stays spent
    for _ in range(HZ_TOTAL + 2):
        if pan._hazard is None:
            break
        pan.anim()
    assert pan.travelling
    assert p.energy == e0 - HAZARD_ENERGY              # the pounce landed
