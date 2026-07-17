"""Training-system canon pins (PhysicalState.exercise / setExercise / fatigue /
ClockTic.onExerciseFinish; training audit 2026-07-06).

Fixtures pin the rolls they don't exercise: (the sickness rolls left) --
monkeypatched to no-ops where a stray catch would muddy an assertion, and the
fatigue roll is forced (randrange -> 0) or silenced (-> 99) as the test needs.
"""
import random

from tuipet.pet import (Pet, RANK_TRAIN_FAIL, RANK_TRAIN_FORCED,
                        RANK_CHANGE_FATIGUE, RANK_FATIGUE_FORCED)


def _pet(**kw):
    p = Pet(num=4, name="T", stage="Rookie", attribute="Vaccine")
    p.hunger = 4
    p.calories = 0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _quiet(monkeypatch):
    """(the _check_sick/_check_worse_sick quieting left with the sickness
    system -- BASIC VPET 2026-07-17: nothing rolls illness any more)"""


# (test_battle_wins_feed_perfect_wins left with the classic battle -- 0.5 BATTLE 2026-07-17)


