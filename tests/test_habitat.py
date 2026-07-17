"""Habitat vs DVPet Habitat.java + PhysicalState checkTime /
checkEnergyIncFromPerfectConditions / setExercise fatigue."""
import random
from tuipet.pet import Pet, DAY_LENGTH


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine", energy=24, max_energy=24,
            obedience=500)
    p.weight = p._base_weight()
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_day_phase_follows_the_habitat_daylight_triple():
    p = _pet()
    tri = p.habitat_obj()["times"]["Spring"]        # [morning, noon, night]
    m, n, night = tri
    hr = DAY_LENGTH / 24
    p.world_seconds = (m + 0.5) * hr
    assert p.day_phase == "dawn"
    p.world_seconds = (n + 0.5) * hr
    assert p.day_phase == "day"
    p.world_seconds = (night - 0.5) * hr
    assert p.day_phase == "dusk"                    # isSunset: the last Noon hour
    p.world_seconds = (night + 0.5) * hr
    assert p.day_phase == "night"


def test_winter_reads_the_fall_triple():
    # checkTime's Winter case reads getFallTime -- a DVPet quirk kept as canon
    p = _pet()
    p.world_seconds = 39 * DAY_LENGTH + 10 * (DAY_LENGTH / 24)  # day 39 = first Winter day (13-day seasons), 10:00
    assert p.season == "Winter"
    fall = p.habitat_obj()["times"]["Fall"]
    assert (p.day_phase == "dawn") == (fall[0] <= 10 < fall[1])


def test_energy_save_only_at_the_favourite_time():
    p = _pet()
    p.time_pref = {ph: 0 for ph in p.time_pref}     # no favourite -> never saves
    saves = 0
    for _ in range(300):
        p.energy = 10
        p._set_energy(9)
        saves += p.energy == 10
    assert saves == 0


def test_energy_save_fires_under_perfect_conditions():
    random.seed(0)
    p = _pet(mood=300)                              # Happy
    p.time_pref = {ph: 0 for ph in p.time_pref}
    p.time_pref[p.day_phase] = 50                   # NOW is its favourite time
    p.weather = "Clear"
    lo, hi = p.ideal_temp
    p.temp = (lo + hi) / 2
    saves = 0
    for _ in range(300):
        p.energy = 10
        p._set_energy(9)
        saves += p.energy == 10
    # range 10 -2 -1 -1 = 6 -> ~1/6 of drops bounce back
    assert 20 <= saves <= 90


