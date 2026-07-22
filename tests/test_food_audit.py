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
from tuipet.pet import (AGE_DAY, GERIATRIC_AGE_DAYS, GERIATRIC_REMAIN,
                        MIN_STOMACH_CAPACITY, Pet)


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
    p.age_seconds = GERIATRIC_AGE_DAYS * AGE_DAY + 1   # just past the elder line
    assert p.is_geriatric
    assert p.stomach_capacity() == full        # shrink starts at ~0 at onset
    p.age_seconds = GERIATRIC_AGE_DAYS * AGE_DAY + GERIATRIC_REMAIN   # window's end
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


# (the two food-lock tests left: Citramon UNLOCKED in v0.5.5 (test_shop_clone
# pins the timed-care reachability) -- they only kept passing because the
# now-dropped TIME gate happened to fail for a fresh pet, exposed 2026-07-17)
