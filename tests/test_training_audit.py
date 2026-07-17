"""Training/exercise audit vs the decompile (2026-07-15).

Near-verbatim already: canExercise's start-of-drill refusal (minEnergy -127
vacuous, documented), exercise()'s unconditional per-drill body (effort +1,
the attribute-enthusiasm branches with the None-sentinel quirks, the time-of-
day ranks, mood += enthusiasm, the worse-sick roll, weight data-dead /
caloric cost, energy -1), onExerciseFinish's success/fail split (praise +
power on success with the documented quality-scaled gain; TrainFail+Forced
rank sours, mood -10 / obedience -1 on failure), the gauge-full fatigue roll
(60/40 nutrition, +-5/axis home), the injury matrices (weight x vitamin,
weak-aversion tables, additive age/fatigue/exhaustion/home) -- all constants
checked against config.csv verbatim.

Three worsen-path divergences fixed and pinned here: worsening an injury now
extends it by ONE recovery lapse (canon setInjLength+1 -- the old line added
a whole fresh random spell, several times too harsh), both worsenings sour
the HOUR they happened in (canon timeRanks dec), and a worsening sours the
attribute that did it (the drilled attr / the opponent's, +forced when
compliance was spent) like canon worsenedInjury/changeBattleRanks.
"""
from tuipet.pet import (INJ_LAPSE_MIN, RANK_TIME_SICK, RANK_WORSE_INJ_ATTR,
                        RANK_WORSE_INJ_FORCED, Pet)


def _pet(**kw):
    kw.setdefault("obedience", 500)
    return Pet(num=100, stage="Champion", attribute="Vaccine", **kw)


# (test_worse_sick_sours_the_hour_too left with the timeRanks system --
# BASIC VPET 2026-07-17)


