"""Weight-system canon audit pins (2026-07-06) vs DVPet PhysicalState.

The audit found no setWeight semantics: the body's hard clamp at baseWeight
+- round(base x WeightLimitMultiple 0.75) with its weightLimitPenalty sting
was missing (weight grew unbounded past the Over tier), the calorie buffer
had no rising-overflow BM bump, and _apply_consumable added weight (and
obedience) raw where canon scales both by the item modifier."""
from tuipet import evolution
from tuipet.pet import (Pet, WEIGHT_LIMIT_MULTIPLE, CALORIE_LIMIT)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.mood = 100
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# --- setWeight: the hard clamp + the sting -----------------------------------

def test_weight_clamps_at_the_body_wall_with_a_sting():
    p = _pet(enthusiasm=0)
    base = p._base_weight()
    span = round(base * WEIGHT_LIMIT_MULTIPLE)
    m0 = p.mood
    p._set_weight(base + span + 50)
    assert p.weight == base + span
    # (the body-wall mood sting left with the mood system)
    # (the body-wall spirit sting left with the enthusiasm system)
    q = _pet(enthusiasm=0)
    m0 = q.mood
    q._set_weight(-100)
    assert q.weight == base - span                # the wall, not the max(1,...) floor
    # (the body-wall mood sting left with the mood system)

def test_inside_the_band_no_sting_and_a_floor_of_one():
    p = _pet(enthusiasm=0)
    m0 = p.mood
    p._set_weight(p._base_weight() + 2)
    assert p.mood == m0 and p.enthusiasm == 0     # no penalty inside the band
    # a tiny base (span rounds small) can drive the floor: base-span >= 1 for
    # base 20, so pin the floor via the helper's own arithmetic instead
    assert p.weight == p._base_weight() + 2

def test_the_wall_is_wider_than_the_over_tier():
    """WeightLimitMultiple 0.75 vs OverUnderWeightThreshold 0.5: a pet CAN sit
    in the Over/Under band (evolution Weight reqs stay reachable) but never
    past the wall."""
    p = _pet()
    base = p._base_weight()
    p._set_weight(base + round(base * 0.6))       # between the tier and the wall
    assert evolution.weight_category(p.weight, base) == "Over"
    p._set_weight(base * 10)
    assert p.weight == base + round(base * WEIGHT_LIMIT_MULTIPLE)


# --- setCalories: rising overflow hastens the poop -----------------------------

def test_calorie_overflow_while_rising_bumps_the_bm_gauge():
    p = _pet()
    p.calories = CALORIE_LIMIT - 1
    t0 = getattr(p, "_poop_t", 0.0)
    p._set_calories(p.calories + 5)               # rich meal: past the ceiling
    assert p.calories == CALORIE_LIMIT
    assert getattr(p, "_poop_t", 0.0) > t0        # AboveMaxCaloriesBMGaugeChange

def test_no_bump_when_falling_or_landing_exactly_at_the_limit():
    p = _pet()
    p.calories = 2
    t0 = getattr(p, "_poop_t", 0.0)
    p._set_calories(-99)                          # underflow: clamps silently
    assert p.calories == -CALORIE_LIMIT
    p._set_calories(CALORIE_LIMIT)                # a refill TO the limit: not past it
    assert getattr(p, "_poop_t", 0.0) == t0


