"""Taste/rank drift canon audit pins (2026-07-06) -- the standing "rank system
unported" deferral, closed.

Already live before this arc: the FOOD ledger (a faithful simplified port) and
the TIME ledger (Joel's tuned adaptation after the misbehaving-ratchet
incident -- kept, with canon's sicken/injure hour-sours added).  Ported here:
the ATTRIBUTE ledger (drills warm, injuries and forced training sour, +-200
emergence feeding the Happy power bonus and the exercise spirit branches),
the WEAK injury tables keyed on the static species aversion, the food
forced-meal decs, and the PERSONALITY TRACKER (childhood energy/weight/mood
tallies re-rolling the temperament at the Champion evolution)."""
import random

from tuipet import data
from tuipet.pet import (Pet, RANK_LIMIT, RANK_INJ_BATTLE_LOST, RANK_TIME_SICK,
                        PCHAMP_RANK, INJ_EXERCISE, INJ_WEAK_EXERCISE)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p.mood = 100
    p.energy = 10
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# --- the attribute ledger ---------------------------------------------------------

def test_drills_warm_the_attribute_stage_scaled():
    p = _pet()                                    # Champion: no stage bonus
    p._change_attr_rank("Data")                   # neither pref nor aversion for 102?
    base = p.attr_ranks["Data"]
    q = _pet(stage="Fresh")                       # a pup forms tastes +3 faster
    q._change_attr_rank("Data")
    assert q.attr_ranks["Data"] == base + 3

def test_species_preference_biases_the_drift():
    p = _pet()
    pref = p._phys().get("attr_pref")             # Devimon: Virus
    aver = p._phys().get("attr_aversion")
    p._change_attr_rank(pref)
    p._change_attr_rank(aver)
    assert p.attr_ranks[pref] - p.attr_ranks[aver] == 4   # +2 pref vs -2 aversion bias

def test_a_rank_at_the_limit_becomes_the_emergent_favorite():
    p = _pet()
    p.attr_ranks["Data"] = RANK_LIMIT - 1
    p._change_attr_rank("Data")
    assert p.favorite_attr == "Data"
    p._dec_attr_rank("Data", RANK_LIMIT * 2)      # ...and souring to the floor flips it
    assert p.disliked_attr == "Data" and p.favorite_attr == ""

def test_forced_training_sours_the_attribute():
    p = _pet(strength=0, compliance=True)
    p.apply_training(0, 0, attribute="Data", game="data")   # a failed FORCED drill
    # +change_rank (1, Data is neither pref nor aversion... computed) then -2 forced
    assert p.attr_ranks["Data"] < p._rank_stage_inc() + 3   # net below the warm-only path


def test_the_emergent_favorite_feeds_the_power_bonus():
    reqs = data.load_requirements()
    _, by = data.load_sprites()
    num = next(n for n, r in by.items()
               if r["attribute"] not in ("Vaccine", "Data", "Virus")
               and r["stage"] == "Champion")
    p = Pet(num=num, name=by[num]["name"], stage="Champion", attribute=by[num]["attribute"])
    p.favorite_attr = "Data"                      # an emergent taste outranks the seed
    assert p._power_bonus_attr() == "Data"


# (test_falling_ill_sours_the_hour left with the timeRanks system --
# BASIC VPET 2026-07-17)


