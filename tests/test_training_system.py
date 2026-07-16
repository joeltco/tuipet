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


def test_failed_drill_sours_the_trained_attribute(monkeypatch):
    """changeTrainingRank(attr, TrainFail + forced): a whiffed drill sours its
    attribute by 3, by 5 when the pet only trained because compliance was spent;
    a clean success sours nothing."""
    _quiet(monkeypatch)
    monkeypatch.setattr(random, "randrange", lambda n: n - 1)   # fatigue never rolls
    p3 = _pet(compliance=False, strength=0)
    p3.apply_training(3, 50, "Data", game="data")               # clean success
    warm = p3.attr_ranks["Data"]                                # the stage-scaled warm alone
    assert warm > 0                                             # warmed, never soured
    p = _pet(compliance=False, strength=0)
    p.apply_training(0, 0, "Data", game="data")                 # fail, not complied
    assert p.attr_ranks["Data"] == warm - RANK_TRAIN_FAIL
    p2 = _pet(compliance=True, strength=0)
    p2.apply_training(0, 0, "Data", game="data")                # fail, complied
    assert p2.attr_ranks["Data"] == warm - RANK_TRAIN_FAIL - RANK_TRAIN_FORCED


def test_the_gauge_filling_push_rolls_fatigue(monkeypatch):
    """setExercise: the fatigue roll fires when newExercise (= old + 1) reaches
    the limit -- the 3->4 push that FILLS the gauge rolls, 2->3 does not.  The
    3-arg fatigue sours the drill that broke it (+2 more when forced) and a
    forced push costs obedience -3."""
    _quiet(monkeypatch)
    monkeypatch.setattr(random, "randrange", lambda n: 0)       # every chance hits
    monkeypatch.setattr(random, "randint", lambda a, b: a)
    base = _pet(compliance=False, strength=0)
    base.apply_training(3, 50, "Virus", game="virus")
    warm = base.attr_ranks["Virus"]                             # the stage-scaled warm alone
    p = _pet(compliance=True, strength=3, obedience=50)
    p.apply_training(3, 50, "Virus", game="virus")
    assert p.is_fatigued()                                      # 3->4 rolled
    # incAttRank's warm, then the fatigue sour 3+2 (no fail sour: it succeeded;
    # the success+complied changeTrainingRank adds RankChangeTrainForced 2)
    assert p.attr_ranks["Virus"] == warm - (RANK_CHANGE_FATIGUE + RANK_FATIGUE_FORCED) - RANK_TRAIN_FORCED
    assert p.obedience < 50                                     # obedienceChangeFatigueForced
    p2 = _pet(compliance=False, strength=2)
    p2.apply_training(3, 50, "Virus", game="virus")
    assert not p2.is_fatigued()                                 # 2->3 never rolls


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
    p = _pet(obedience=100, fatigue_length=40)
    p._fatigue()
    assert p.fatigue_length == 50                               # 40 + 10, accumulated
    assert p.obedience == 100 - 5                               # alreadyFatiguedObedienceDec
    p2 = _pet(obedience=100, fatigue_length=0)
    p2._fatigue()
    assert p2.fatigue_length == 10                              # fresh: set, not added
    assert p2.obedience == 100                                  # fresh pays no obedience


def test_fatigue_sours_the_hour():
    """timeRanks dec RankChangeFatigue: the collapse sours the time of day it
    happened in (raw onto the tuned scale, like the sicken sours)."""
    p = _pet()
    ph = p.day_phase
    before = p.time_pref.get(ph, 0)
    p._fatigue()
    assert p.time_pref[ph] == before - RANK_CHANGE_FATIGUE


def test_disliked_drill_refuses_harder():
    """refused(Attribute): the emergent disliked drags the obey line -20 -- a
    roll that would just pass on a neutral drill fails on the hated one."""
    p = _pet(compliance=False, enthusiasm=2)
    p.disliked_attr = "Virus"
    p.obedience = 0
    hits = {True: 0, False: 0}
    random.seed(7)
    for _ in range(300):
        hits[p.check_refused(attr="Virus")] += 1
        p.scold_flag, p.scold_window = False, 0
    refused_disliked = hits[True]
    p.disliked_attr = ""
    hits = {True: 0, False: 0}
    random.seed(7)
    for _ in range(300):
        hits[p.check_refused(attr="Virus")] += 1
        p.scold_flag, p.scold_window = False, 0
    assert refused_disliked > hits[True]                        # -20 bites


def test_willing_favourite_with_standing_refusal_spoils():
    """refused(): obeying the FAVOURITE drill while an unresolved refusal stands
    SPOILS the pet -- spoil() pays obedience -10 / mood +10 and clears it."""
    p = _pet(compliance=False, enthusiasm=5, obedience=80)
    p.favorite_attr = "Vaccine"
    p.scold_flag, p.scold_window = True, 0      # an unresolved refusal stands
    m0 = p.mood
    assert not p.check_refused(attr="Vaccine")  # it does its favourite anyway
    assert p.obedience == 70 and not p.scold_flag


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
