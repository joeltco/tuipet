"""Obedience-system canon audit pins (2026-07-06) vs DVPet PhysicalState.

The audit found the stat had NO setObedience semantics (no MaxObedience 150
ceiling, no disposition nudge), no obedienceLapse (discipline never faded),
no checkRefusedOff (an unscolded refusal never expired), and two missing
forced-meal costs.  The factors/adjusted math was already verbatim."""
import random


from tuipet import data
from tuipet.pet import (Pet, MAX_OBEDIENCE, OBEDIENCE_LAPSE_MIN, OBEDIENCE_LAPSE_DEC,
                        OBEDIENCE_FILTH_SCALE, REFUSED_OFF_MIN, REFUSED_OFF_MOOD_INC,
                        REFUSED_OFF_OBED_DEC, OBEDIENCE_CHANGE_SICK_FORCED,
                        OBEDIENCE_CHANGE_INTOL_FORCED, UNDEPRESSED_OBED_INC)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0        # mid-morning, awake
    p.weight = p._base_weight()
    p.mood = 100                       # calm Neutral: no depressed rolls
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# --- setObedience: ceiling + disposition nudge --------------------------------

def test_obedience_caps_at_max_and_floors_at_zero():
    p = _pet(obedience=149, depressed=True, mood=50)
    p.depressed = False
    p._set_obedience(p.obedience + UNDEPRESSED_OBED_INC)
    assert p.obedience == MAX_OBEDIENCE            # 149+33 clamps at 150
    p._set_obedience(-40)
    assert p.obedience == 0

def test_obedience_changes_bend_against_the_disposition():
    """setObedience nudges every CHANGE by -disposition (the mirror image of
    setMood's +disposition): a sunny pet takes each change a point lower, a
    sour one a point higher."""
    sunny = _pet(disposition=1, obedience=50)
    sunny._set_obedience(sunny.obedience + 5)
    assert sunny.obedience == 54
    sour = _pet(disposition=-1, obedience=50)
    sour._set_obedience(sour.obedience + 5)
    assert sour.obedience == 56
    flat = _pet(obedience=50)
    flat._set_obedience(flat.obedience + 5)
    assert flat.obedience == 55


# --- obedienceLapse ------------------------------------------------------------

def test_obedience_fades_on_the_disposition_cadence():
    """Dec 2 every 120 game-min neutral / 180 sunny / 60 sour -- and the
    setter's own nudge shades the landing (sour -2 lands -1, sunny -2 lands
    -3): the shipped math, pinned as-is."""
    for dispo, net in ((0, -2), (1, -3), (-1, -1)):
        p = _pet(disposition=dispo, obedience=60)
        p._tick_mood_discipline(OBEDIENCE_LAPSE_MIN[dispo])
        assert p.obedience == 60 + net, f"disposition={dispo}"

def test_filth_drains_obedience_on_the_lapse():
    p = _pet(obedience=60, poop=3, poop_sizes=[1, 1, 1])
    p._tick_mood_discipline(OBEDIENCE_LAPSE_MIN[0])
    # the dec event bills the mess too: -2, then FilthScale -1 x 3 piles
    assert p.obedience == 60 - OBEDIENCE_LAPSE_DEC + OBEDIENCE_FILTH_SCALE * 3

def test_the_lapse_holds_short_of_its_cadence():
    p = _pet(obedience=60)
    p._tick_mood_discipline(OBEDIENCE_LAPSE_MIN[0] - 1)
    assert p.obedience == 60


# --- checkRefusedOff ------------------------------------------------------------

def test_an_unscolded_refusal_expires_smug():
    p = _pet(obedience=60, refused=True)
    m0 = p.mood
    p._tick_mood_discipline(REFUSED_OFF_MIN)
    assert not p.refused
    # (the smug mood bump left with the mood system)
    assert p.obedience == 60 - REFUSED_OFF_OBED_DEC

def test_an_open_scold_window_holds_the_refusal():
    p = _pet(obedience=60, refused=True, scold_flag=True)
    p._tick_mood_discipline(REFUSED_OFF_MIN * 3)
    assert p.refused                               # the lesson is still owed


# --- forced-meal obedience costs ------------------------------------------------

def test_a_compliant_pet_sickened_by_a_dirty_meal_resents_it(monkeypatch):
    p = _pet(obedience=50, compliance=True, hunger=1, poop=2, poop_sizes=[1, 1])
    monkeypatch.setattr(type(p), "check_refused", lambda self, **k: False)
    monkeypatch.setattr(random, "randrange", lambda n: 0)      # the sick roll hits
    meat = data.load_foods()[0]
    assert not any(c in p._species_food()[2] for c in (meat.get("category") or "").split(";"))
    p.feed(meat)
    assert p.sick
    assert p.obedience == 50 + OBEDIENCE_CHANGE_SICK_FORCED   # ObedienceChangeSickForced

def test_a_compliant_pet_forced_through_an_intolerant_meal(monkeypatch):
    """ObedienceChangeIntolerantForced -3, sick-or-not.  NB the shipped
    digimon.csv sets FoodIntolerance=None for all 1574 species -- the
    mechanic is engine-real but data-dead, so the pin drives the code path
    with a faked intolerance."""
    p = _pet(obedience=50)
    monkeypatch.setattr(type(p), "_species_food",
                        lambda self: (None, None, ["Meat"]))
    monkeypatch.setattr(random, "random", lambda: 1.0)         # the sick rolls miss
    p._eat_food("Meat", complied=True)
    # -3 lands sick-or-not; the setter nudge is 0 for a flat disposition
    assert p.obedience == 50 + OBEDIENCE_CHANGE_INTOL_FORCED
    q = _pet(obedience=50)
    monkeypatch.setattr(type(q), "_species_food",
                        lambda self: (None, None, ["Meat"]))
    q._eat_food("Meat", complied=False)                        # it chose to eat: no resentment
    assert q.obedience == 50
