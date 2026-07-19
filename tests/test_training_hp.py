"""Trained battle HP + the exercise() nuances (checkAndIncPerfectWins,
checkExerciseTime, mood+=enthusiasm, checkWorseSick, ExerciseCalorieDec)."""
import random
from tuipet.pet import (Pet, DAY_LENGTH, STARTING_HEALTH_POINTS, PERFECT_WINS_LIMIT,
                        CALORIE_LIMIT)
from tuipet import persistence


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine", energy=24, max_energy=24,
            weight=20, obedience=500)
    p.weight = p._base_weight()      # Healthy: keep the 50% overweight-injury roll out
    p.strength = 0                   # off the Effort cap: no canon fatigue roll
    p.age_seconds = 2 * DAY_LENGTH
    p.world_seconds = 10 * 60.0      # mid-day under the canon daylight bands
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_hatchling_hp_and_age_ladder():
    p = _pet()
    assert p.full_health == STARTING_HEALTH_POINTS == 5
    p.age_seconds = 0.5 * DAY_LENGTH
    assert p.max_health() == 10                     # MaxHealthDefault
    p.age_seconds = 5 * DAY_LENGTH
    assert p.max_health() == 15
    p.age_seconds = 14 * DAY_LENGTH
    assert p.max_health() == 30                     # MaxHealthUltra tier


# (test_hp_drill_wins_grow_full_health left with the classic training system -- 0.5 TRAINING 2026-07-17)


def test_hp_growth_clamps_to_the_age_cap():
    p = _pet()
    p.age_seconds = 0.5 * DAY_LENGTH
    p.full_health = 10                              # already at the under-1d cap
    p.perfect_wins = PERFECT_WINS_LIMIT - 1
    note = p._check_perfect_wins()
    assert p.full_health == 10 and note == ""       # counted, clamped (forceInc canon)


# (test_battle_uses_trained_hp left with the classic battle -- 0.5 BATTLE 2026-07-17)


# (test_old_saves_grandfather_stage_hp left with the classic battle -- 0.5 BATTLE 2026-07-17)




def test_the_drill_carries_no_dead_remnants_and_the_999_canon_stands():
    """Drill audit 2026-07-19: the bar's font lives ONLY in strikefx since
    v0.5.67 (training's copy fed nothing), the energy gate lives only in
    petbattle -- and the battles>=999 auto-mega is v0.4.12 verbatim, kept."""
    import inspect
    from tuipet import training, strikefx
    src = inspect.getsource(training)
    assert not hasattr(training, "_FONT_3X5") and hasattr(strikefx, "_FONT_3X5")
    assert not hasattr(training, "ENERGY_NEED")
    assert "999" in src                          # the canon veteran rule stays
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", battles=999)
    p.world_seconds, p.hunger, p.energy, p.strength = 600.0, 3, 20, 2
    pan = training.TrainingPanel(p)
    pan.bar = 0                                  # far outside the window
    pan._lock()
    assert pan.grade == "mega"                   # the maxed veteran never whiffs
