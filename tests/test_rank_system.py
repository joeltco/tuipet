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


# (test_forced_training_sours_the_attribute left with the classic training system -- 0.5 TRAINING 2026-07-17)


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


