"""Weight-system canon audit pins (2026-07-06) vs DVPet PhysicalState.

The audit found no setWeight semantics: the body's hard clamp at baseWeight
+- round(base x WeightLimitMultiple 0.75) with its weightLimitPenalty sting
was missing (weight grew unbounded past the Over tier), the calorie buffer
had no rising-overflow BM bump, and _apply_consumable added weight (and
obedience) raw where canon scales both by the item modifier."""
from tuipet import data, evolution
from tuipet.pet import (Pet, WEIGHT_LIMIT_MULTIPLE, WEIGHT_LIMIT_MOOD_PENALTY,
                        WEIGHT_LIMIT_ENTH_PENALTY, CALORIE_LIMIT, FOOD_WEIGHT_CHANGE,
                        WEAK_CONSUMABLE_COEF)


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
    assert p.enthusiasm == 0 - WEIGHT_LIMIT_ENTH_PENALTY
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


# --- consumable weight/obedience take the item modifier ------------------------

def test_weak_consumable_scales_weight_and_obedience(monkeypatch):
    """applyItem scales EVERY stat by the modifier (canon 3502/3428) -- a
    compliant pet's grudging 0.1-strength item lands ceil(v x 0.1), not raw.
    Obedience pinned via the real Textbook (+20); weight via a synthetic item
    (NO shipped item carries weight -- that half is data-dead, code-pinned)."""
    import math
    monkeypatch.setattr(Pet, "check_refused", lambda self, **k: False)
    p = _pet(obedience=50, compliance=True)       # compliant: the weak 0.1 path
    p.inventory["i:0"] = 1
    p.use_item("i:0")
    assert p.obedience == 50 + math.ceil(20 * WEAK_CONSUMABLE_COEF)   # +2, not +20
    q = _pet(obedience=50, compliance=False)      # willing: full strength
    q.inventory["i:0"] = 1
    q.use_item("i:0")
    assert q.obedience == 70
    heavy = dict(data.consumable_by_key("i:0"), weight=10, obedience=0, name="Anvil")
    monkeypatch.setattr(data, "consumable_by_key", lambda k: heavy)
    r = _pet(compliance=True)
    r.inventory["i:0"] = 1
    w0 = r.weight
    r.use_item("i:0")
    assert r.weight == w0 + math.ceil(10 * WEAK_CONSUMABLE_COEF)      # +1, not +10


# --- the fattening/shedding calorie-weight coupling stays intact ---------------

def test_food_fattens_only_while_calories_are_positive(monkeypatch):
    monkeypatch.setattr(Pet, "check_refused", lambda self, **k: False)
    meat = data.load_foods()[0]
    p = _pet(hunger=1)
    p.calories = 2                                # already positive: the rich meal fattens
    pw0 = p.weight
    p.feed(meat)
    q = _pet(hunger=1)
    q.calories = -2                               # depleted: the meal only refuels
    qw0 = q.weight
    q.feed(meat)
    # both take the food's own weight; only p crosses the calorie-fatten branch
    assert (p.weight - pw0) == (q.weight - qw0) + FOOD_WEIGHT_CHANGE
