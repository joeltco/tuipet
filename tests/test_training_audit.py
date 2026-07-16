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


def test_worsening_extends_one_lapse_exactly():
    p = _pet()
    p.inj_length = 100.0
    p._worsen_injury()
    assert p.inj_length == 100.0 + INJ_LAPSE_MIN   # setInjLength(_injLength + 1)


def test_worsening_sours_the_hour_and_the_attribute():
    p = _pet()
    p.inj_length = 100.0
    ph = p.day_phase
    before_hour = p.time_pref.get(ph, 0)
    p.attr_ranks["Virus"] = 50                     # room below the clamp
    p._worsen_injury(attr="Virus", complied=True)
    assert p.time_pref[ph] == before_hour - RANK_TIME_SICK
    assert p.attr_ranks["Virus"] == 50 - (RANK_WORSE_INJ_ATTR
                                          + RANK_WORSE_INJ_FORCED)


def test_worse_sick_sours_the_hour_too():
    p = _pet()
    p.sick, p.sick_length = True, 100.0
    ph = p.day_phase
    before = p.time_pref.get(ph, 0)
    p._worsen_sick()
    assert p.time_pref[ph] == before - RANK_TIME_SICK
    assert p.sick_length > 100.0                    # still +1 lapse
