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


def test_five_hp_drill_wins_grow_full_health():
    p = _pet(calories=CALORIE_LIMIT)
    hp0 = p.full_health
    for _ in range(PERFECT_WINS_LIMIT):
        p.apply_training(3, 100, game="hp")
    assert p.perfect_wins == 5
    assert p.full_health == hp0 + 1                 # PerfectWinsHealthInc
    msgs = p.apply_training(3, 100, game="hp")
    assert "HP" not in msgs                         # win 6: counts, no bump yet


def test_hp_growth_clamps_to_the_age_cap():
    p = _pet()
    p.age_seconds = 0.5 * DAY_LENGTH
    p.full_health = 10                              # already at the under-1d cap
    p.perfect_wins = PERFECT_WINS_LIMIT - 1
    note = p._check_perfect_wins()
    assert p.full_health == 10 and note == ""       # counted, clamped (forceInc canon)


def test_battle_uses_trained_hp():
    from tuipet.battle import Battle
    p = _pet(full_health=7)
    b = Battle(p, {"num": 4, "name": "X", "stage": "Rookie", "vaccine": 10,
                   "data_power": 5, "virus": 5, "hp": 8, "bits": (0, 0)})
    assert b.pet_max == 7


def test_old_saves_grandfather_stage_hp():
    p = _pet(stage="Champion")
    d = persistence.to_save_dict(p)
    del d["full_health"]                            # a pre-trained-HP save
    p2, _ = persistence.pet_from_save(d, catch_up=False)
    assert p2.full_health == 15                     # old flat Champion HP kept


def test_hp_chip_food_adds_permanent_hp():
    from tuipet import data
    p = _pet(hunger=0, calories=0)
    chip = next(f for f in data.load_foods() if f["name"] == "HP Chip")
    assert chip["health"] == 1
    hp0 = p.full_health
    p.feed(chip)
    assert p.full_health == hp0 + 1


def test_training_costs_a_calorie_and_couples_mood_to_spirit():
    p = _pet(calories=10, enthusiasm=3)
    m0 = p.mood
    p.apply_training(3, 100, game="hp")
    assert p.calories == 9                          # ExerciseCalorieDec
    # mood: +enthusiasm coupling happened (plus time-of-day noise, small)
    assert p.mood != m0


def test_sick_drill_can_worsen():
    random.seed(0)
    p = _pet()
    p._sicken()
    len0 = p.sick_length
    worsened = False
    for _ in range(400):                            # 1% per drill
        p.calories, p.energy = CALORIE_LIMIT, 24
        p.apply_training(3, 100, game="vaccine", attribute="Vaccine")
        if p.sick_length != len0:
            worsened = True
            break
    assert worsened


def test_fav_time_drill_lifts_mood():
    p = _pet(calories=CALORIE_LIMIT, enthusiasm=0)
    p.time_pref = {ph: 0 for ph in p.time_pref}
    p.time_pref[p.day_phase] = 50                   # NOW is its favourite time
    m0 = p.mood
    p.apply_training(3, 100, game="hp")
    assert p.mood > m0                              # FavExerciseTimeMoodInc wins
