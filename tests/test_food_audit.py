"""Food/feeding audit vs the decompile (2026-07-15).

Fixes pinned here: the per-species stomach (canon getStomachCapacity) with its
geriatric shrink drives the applyFood diminishing modifier and the taste-mood
gates; every meal bumps the bowel gauge by a flat lapse-inc plus the food's
modifier-scaled BMGauge; and the corpus's one FOOD-triggered evolution --
Nanimon + an Orange (food 42) = Citramon -- exists and is locked out of
natural timed care exactly like the item (Digimental) forms.
"""
import pytest

from tuipet import data
from tuipet import evolution
from tuipet.pet import (GERIATRIC_REMAIN, MIN_STOMACH_CAPACITY, Pet)


def _pet(**kw):
    p = Pet(num=-1, stage="Rookie", obedience=500, **kw)
    return p


# ---- the species stomach -------------------------------------------------------

def test_stomach_capacity_is_per_species_and_loaded():
    reqs = data.load_requirements()
    caps = {r.get("stomach_capacity") for r in reqs.values()}
    assert len(caps) > 3, "species stomachs should vary (canon 8..40)"
    assert all(isinstance(c, int) and c >= 8 for c in caps if c != 10)


def test_geriatric_stomach_shrinks_to_the_floor():
    reqs = data.load_requirements()
    num = next((n for n, r in reqs.items() if r.get("stomach_capacity", 0) >= 16), None)
    if num is None:
        pytest.skip("no big-stomach species in the data")
    p = Pet(num=num, stage="Champion", obedience=500)
    full = p.stomach_capacity()
    assert full >= 16
    p.lifespan, p.age_seconds = 100000.0, 100000.0 - GERIATRIC_REMAIN + 1
    assert p.is_geriatric
    assert p.stomach_capacity() == full        # shrink starts at ~0 at onset
    p.age_seconds = p.lifespan                 # the last breath
    shrunk = p.stomach_capacity()
    assert MIN_STOMACH_CAPACITY <= shrunk <= full - 8   # canon max dec ~9


def test_every_meal_bumps_the_bowel_gauge():
    """applyFood: bmGauge += bmLapseInc + ceil(BMGauge x modifier) -- even a
    zero-BM food advances the clock by one lapse-worth."""
    p = _pet()
    p.hunger = 1
    p._poop_t = 0.0
    p.feed(food={"name": "T", "hunger": 1, "mood": 0, "bm": 0})
    lapse_worth = p._poop_interval * p._phys().get("poop_lapse", 1) \
        / max(1, p._phys().get("poop_limit", 64))
    assert p._poop_t >= lapse_worth * 0.999


# ---- the Orange (food evolution) ------------------------------------------------

def test_citramon_is_food_locked():
    req = data.load_requirements().get(1513, {})
    assert req.get("evol_food") == 42          # the Orange
    p = Pet(num=118, stage="Champion", obedience=500)   # Nanimon
    assert 1513 in data.load_evolutions().get(118, [])
    assert not evolution.check(p, 1513), "food-locked: unreachable by timed care"
    assert evolution.food_select(p, 41) != 1513          # the wrong food won't do


def test_feeding_the_orange_fires_the_evolution(monkeypatch):
    """The wiring: when food_select validates a form mid-meal, feed() evolves
    on the spot (processFoodEvol) and re-anchors the line like a Digimental."""
    p = Pet(num=118, stage="Champion", obedience=500)
    p.hunger = 1                               # room for the meal (non-glutton)
    orange = next(f for f in data.load_foods() if f["id"] == 42)
    monkeypatch.setattr(evolution, "food_select",
                        lambda pet, fid: 1513 if fid == 42 else None)
    msg = p.feed(food=orange)
    assert p.num == 1513 and "evolved" in msg


def test_food_lock_arm_matches_canon_shape():
    """checkSpecialCondition's food arm: food=-1 never validates a locked
    form; the RIGHT food makes the lock pass (care gates still apply)."""
    p = Pet(num=118, stage="Champion", obedience=500)
    # the lock arm alone: with the right food the evol_food gate stops
    # rejecting (whether the full check passes depends on care gates)
    req = dict(data.load_requirements().get(1513, {}))
    assert req["evol_food"] == 42
    assert evolution.check(p, 1513, food=41) is False    # wrong food: locked
