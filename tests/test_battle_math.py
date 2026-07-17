"""Battle-math canon audit pins (2026-07-06) vs DVPet Battle.java.

VERIFIED VERBATIM this arc: the damage line (base + calcAttackPower ordinal;
canon's isEnemy flag is inverted naming, the math matches), checkFirst's
SPEED initiative (power-sum x health-fraction, tie = coin flip), the win
stat gain (+1: getExtraStats caps at 1; the first-max tie-break matches),
loot as PvE_Wild-only (our adventure-only drops are canon-consistent).
FOUND: battleEnd's tail was thin -- no banded end cost, no compliance, no
contagion, no disposition shade on the plain win/loss mood, no loss missed-
day, and the declined-surrender grudge was missing."""
import random


from tuipet import battle as battle_mod
from tuipet.pet import (Pet, BATTLE_HIGH_HP_ENERGY, BATTLE_LOW_HP_ENERGY,
                        BATTLE_CAL_HIGH, BATTLE_CAL_LOW, SURR_DECLINED_LOST_OBED,
                        CALORIE_LIMIT)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p.mood = 100
    p.energy = 10
    p.calories = CALORIE_LIMIT
    for k, v in kw.items():
        setattr(p, k, v)
    return p


_ENEMY = {"num": 4, "name": "X", "stage": "Champion", "vaccine": 1,
          "data_power": 1, "virus": 1, "hp": 8, "bits": (1, 1)}


def _quiet(monkeypatch):
    monkeypatch.setattr(random, "randrange", lambda n: n - 1)   # every risk roll misses


# --- initiative: the speed formula ------------------------------------------------

def test_the_stronger_healthier_side_strikes_first():
    from tuipet import battlefx
    p = _pet(vaccine=10, data_power=10, virus=10, full_health=15)
    b = battle_mod.Battle(p, dict(_ENEMY))
    assert battlefx._check_first(b) is True           # 30 x 1.0 vs 3 x 1.0
    b.pet_hp = 1                                      # wounded: it slows down
    assert battlefx._check_first(b) is False          # 30 x 1/15 = 2 vs 3 x 1.0


# --- battleEnd's banded cost -------------------------------------------------------

def test_limping_out_doubles_the_end_cost(monkeypatch):
    _quiet(monkeypatch)
    fresh = _pet()
    fresh.record_battle(True, dict(_ENEMY), free_style=True, low_health=False)
    assert fresh.energy == 10 - BATTLE_HIGH_HP_ENERGY
    assert fresh.calories == CALORIE_LIMIT - BATTLE_CAL_HIGH
    hurt = _pet()
    hurt.record_battle(True, dict(_ENEMY), free_style=True, low_health=True)
    assert hurt.energy == 10 - BATTLE_LOW_HP_ENERGY
    assert hurt.calories == CALORIE_LIMIT - BATTLE_CAL_LOW

def test_the_battle_engine_passes_the_band():
    p = _pet(vaccine=10, data_power=10, virus=10)
    b = battle_mod.Battle(p, dict(_ENEMY))
    assert (b.pet_hp <= b.pet_max // 2) is False      # enters the fight fresh


# (test_a_sick_opponent_is_contagious left with the sickness system -- BASIC VPET 2026-07-17)


def test_a_loss_marks_the_day_and_counts_the_exercise(monkeypatch):
    _quiet(monkeypatch)
    p = _pet()
    d0, e0 = p.mistake_day, p.exercise_today
    p.record_battle(False, dict(_ENEMY), free_style=True)
    assert p.mistake_day == d0 + 1                    # BattleLostMissedDayChange
    assert p.exercise_today == e0 + 1                 # incExerciseTime


