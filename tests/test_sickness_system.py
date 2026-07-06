"""Sickness/injury canon audit pins (2026-07-06) vs DVPet PhysicalState.

Found: the fresh-injury rolls were paraphrases ("overweight -> 50%" for
drills, "loss -> 30%" for battles) -- canon runs a weight x vitamin matrix
vs a 1000 bound plus additive mods (age, fatigue, exhaustion, home, +50 on a
battle LOSS) after EVERY drill and EVERY battle; worse-injury lacked the
additive term and travel wrongly used the exercise table (canon rides the
battle one); the sick rolls ignored the habitat/geriatric BOUND shaping and
the fatigue target pad; intolerant food rolled fresh x2 instead of
worse+fresh once each; injuries didn't sap energy; sick pets didn't burn
nutrition or race the bowels; and incMistake carried no sickness risks."""
import math
import random

from tuipet.pet import (Pet, INJ_EXERCISE, INJ_BATTLE, WORSE_INJ_BATTLE,
                        WORSE_INJ_EXERCISE, SICK_CHANCE_BOUND, SICK_COMPAT_CHANGE,
                        SICK_GERIATRIC_FACTOR, FATIGUE_MOD, INJURY_ENERGY_DEC,
                        BATTLE_INJ_LOSS)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p.mood = 100
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _flat_home(monkeypatch):
    monkeypatch.setattr(Pet, "_compat_inj_change", lambda self: 0)


# --- the fresh-injury matrix ----------------------------------------------------

def test_a_healthy_vitamined_pet_never_injures_on_a_drill(monkeypatch):
    _flat_home(monkeypatch)
    monkeypatch.setattr(random, "randrange", lambda n: 0)      # the hottest roll
    p = _pet(energy=5, vitamin_lapse=60.0)                     # healthy weight + vitamin
    p._check_exercise_injury()
    assert not p.is_injured()                                  # good_v = 0: literally never
    q = _pet(energy=5)
    q.weight = q._base_weight() + round(q._base_weight() * 0.6)   # Over, no vitamin
    q._check_exercise_injury()
    assert q.is_injured()                                      # bad_nv = 10 catches roll 0

def test_a_battle_loss_pads_the_injury_roll(monkeypatch):
    _flat_home(monkeypatch)
    monkeypatch.setattr(random, "randrange", lambda n: INJ_BATTLE["good_nv"] + 10)
    won = _pet(energy=5)
    won._check_battle_injury(won=True)
    assert not won.is_injured()                                # 13 >= 3: safe on a win
    lost = _pet(energy=5)
    lost._check_battle_injury(won=False)
    assert lost.is_injured()                                   # 13 < 3 + 50 on a loss

def test_travel_worsening_rides_the_battle_table(monkeypatch):
    """checkWorseTravelInj = calcWorseBattleInj(a, walk): bad_nv 15 vs the
    exercise table's 10 -- a roll of 12 splits them."""
    _flat_home(monkeypatch)
    monkeypatch.setattr(random, "randrange", lambda n: 12)
    for kind, worsened in (("exercise", False), ("travel", True)):
        p = _pet(energy=5, inj_length=100.0)
        p.weight = p._base_weight() + round(p._base_weight() * 0.6)   # Over, no vitamin
        l0 = p.inj_length
        p._check_worse_injury(kind)
        assert (p.inj_length > l0) is worsened, kind


# --- the sick-roll bounds -------------------------------------------------------

def test_old_age_thins_the_sick_bound(monkeypatch):
    seen = []
    monkeypatch.setattr(random, "randrange", lambda n: seen.append(n) or (n - 1))
    p = _pet()
    p._check_sick(10)
    young_bound = seen[-1]
    old = _pet()
    old.age_seconds = old.lifespan * 2                # deep geriatric
    assert old.is_geriatric
    old._check_sick(10)
    assert seen[-1] == young_bound - SICK_GERIATRIC_FACTOR

def test_fatigue_pads_the_worse_sick_target(monkeypatch):
    monkeypatch.setattr(random, "randrange", lambda n: FATIGUE_MOD)    # roll 10
    fresh = _pet(sick=True, sick_length=100.0)
    l0 = fresh.sick_length
    fresh._check_worse_sick(1)                        # target 1: 10 >= 1, safe
    assert fresh.sick_length == l0
    worn = _pet(sick=True, sick_length=100.0, fatigue_length=30.0)
    l0 = worn.sick_length
    worn._check_worse_sick(1)                         # target 1+10: 10 < 11, worsens
    assert worn.sick_length > l0


# --- intolerant food, fresh injuries' side effects, mistakes, the sick lapse -----

def test_intolerant_food_rolls_worse_and_fresh_once_each(monkeypatch):
    calls = []
    monkeypatch.setattr(Pet, "_check_worse_sick",
                        lambda self, t: calls.append(("worse", t)) or False)
    monkeypatch.setattr(Pet, "_check_sick",
                        lambda self, t: calls.append(("sick", t)) or False)
    monkeypatch.setattr(Pet, "_species_food", lambda self: (None, None, ["Meat"]))
    p = _pet()
    p._eat_food("Meat")
    assert calls == [("worse", 50), ("sick", 50)]

def test_a_fresh_injury_saps_a_bar_of_energy():
    p = _pet(energy=5)
    p._injure()
    assert p.energy == 5 - INJURY_ENERGY_DEC
    assert p.is_injured()

def test_a_mistake_while_fatigued_whispers_sickness(monkeypatch):
    monkeypatch.setattr(random, "randrange", lambda n: 0)
    p = _pet(fatigue_length=30.0, mood=0)             # not Happy: no mood slam branch
    p._inc_mistake()
    assert p.sick                                     # AnyMistakeWhileFatigued 1/1 caught roll 0

def test_an_awake_sick_pet_burns_macros_and_races_the_bowels():
    p = _pet(sick=True, sick_length=9000.0, nutr_protein=5, nutr_mineral=5, nutr_vitamin=5)
    t0 = getattr(p, "_poop_t", 0.0)
    p._tick_recovery(60.0)
    assert (p.nutr_protein, p.nutr_mineral, p.nutr_vitamin) == (4, 4, 4)
    assert getattr(p, "_poop_t", 0.0) > t0            # SickLapsePenaltyBM
    q = _pet(sick=True, sick_length=9000.0, asleep=True, nutr_protein=5)
    q._tick_recovery(60.0)
    assert q.nutr_protein == 5                        # the penalty is awake-only
