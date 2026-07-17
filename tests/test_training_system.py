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


def test_battle_wins_feed_perfect_wins(monkeypatch):
    """Battle.battleEnd -> checkAndIncPerfectWins(false): every battle win
    counts toward the next trained-HP point -- gated on HP below the age cap
    (the HP drill's force=TRUE path keeps counting regardless)."""
    _quiet(monkeypatch)
    p = _pet(strength=0)
    cap = p.max_health()                                        # age-0 cap == 10
    p.full_health = cap - 1
    pw0 = p.perfect_wins
    p.record_battle(True, {"num": 5, "name": "F", "stage": "Rookie", "vaccine": 3,
                           "data_power": 1, "virus": 1, "hp": 10, "bits": (1, 1)})
    assert p.perfect_wins == pw0 + 1 and p.full_health == cap
    p.full_health = cap                                         # at the age cap:
    pw1 = p.perfect_wins
    p.record_battle(True, {"num": 5, "name": "F", "stage": "Rookie", "vaccine": 3,
                           "data_power": 1, "virus": 1, "hp": 10, "bits": (1, 1)})
    assert p.perfect_wins == pw1                                # the gate holds
