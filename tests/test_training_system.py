"""Training-system canon pins (PhysicalState.exercise / setExercise / fatigue /
ClockTic.onExerciseFinish; training audit 2026-07-06).

Fixtures pin the rolls they don't exercise: _check_worse_sick / _check_sick are
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
    monkeypatch.setattr(Pet, "_check_worse_sick", lambda self, t=0: False)
    monkeypatch.setattr(Pet, "_check_sick", lambda self, t=0: False)


def test_hp_drill_fatigue_sours_all_three(monkeypatch):
    """exercise(None): the HP drill's at-cap collapse decs Vaccine AND Data AND
    Virus (canon fans the None attribute out to all three)."""
    _quiet(monkeypatch)
    monkeypatch.setattr(random, "randrange", lambda n: 0)
    monkeypatch.setattr(random, "randint", lambda a, b: a)
    p = _pet(compliance=False, strength=4)
    p.apply_training(3, 0, game="hp")
    assert all(p.attr_ranks[a] == -RANK_CHANGE_FATIGUE
               for a in ("Vaccine", "Data", "Virus"))


def test_refatigue_adds_on_and_compounds(monkeypatch):
    """fatigue() while ALREADY down: the rest ADDS ON (never resets shorter) and
    the misery compounds -- obedience -5 on top of the base hits."""
    _quiet(monkeypatch)
    monkeypatch.setattr(random, "randint", lambda a, b: 10)
    p = _pet(fatigue_length=40)
    p._fatigue()
    assert p.fatigue_length == 50                               # 40 + 10, accumulated
    p2 = _pet(fatigue_length=0)
    p2._fatigue()
    assert p2.fatigue_length == 10                              # fresh: set, not added
    # (the compounding obedience bill left with the discipline system)


def test_fatigue_sours_the_hour():
    """timeRanks dec RankChangeFatigue: the collapse sours the time of day it
    happened in (raw onto the tuned scale, like the sicken sours)."""
    p = _pet()
    ph = p.day_phase
    before = p.time_pref.get(ph, 0)
    p._fatigue()
    assert p.time_pref[ph] == before - RANK_CHANGE_FATIGUE


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
