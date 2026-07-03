"""Sleep system vs DVPet: lightsCall neglect, wake auto-relight, morning moods."""
import random

from tuipet.pet import Pet, LIGHTS_MISTAKE_SEC, DAY_LENGTH


def _sleeper(lights):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    p.energy = 5
    p.sleep_lapse = p.sleep_limit              # pressure clock rolls over (canon sleep())
    p.tick(1.0)                                # falls asleep (resets the lights counter)
    assert p.asleep
    p.lights = lights
    return p


def test_sleeping_with_lights_on_is_a_care_mistake():
    p = _sleeper(lights=True)
    m0 = p.care_mistakes
    for _ in range(int(LIGHTS_MISTAKE_SEC) + 2):
        p.tick(1.0)
    assert p.care_mistakes == m0 + 1
    for _ in range(int(LIGHTS_MISTAKE_SEC) + 2):   # postponed: once per sleep
        p.tick(1.0)
    assert p.care_mistakes == m0 + 1


def test_lights_off_sleep_is_blameless():
    p = _sleeper(lights=False)
    m0 = p.care_mistakes
    for _ in range(int(LIGHTS_MISTAKE_SEC) + 2):
        p.tick(1.0)
    assert p.care_mistakes == m0


def test_wake_restores_the_lights():
    random.seed(3)
    p = _sleeper(lights=False)
    p.awake_lapse = p.awake_limit              # slept its fill (setAwakeLapse rollover)
    p.tick(1.0)
    assert not p.asleep
    assert p.lights                             # DVPet wake: setLights(true)


def test_morning_roll_can_move_the_mood():
    # across many seeded mornings, at least one good and one bad morning occur
    moods = set()
    for seed in range(30):
        random.seed(seed)
        p = _sleeper(lights=False)
        p.mood = 0
        p.awake_lapse = p.awake_limit
        p.tick(1.0)
        moods.add((p.mood > 0) - (p.mood < 0))
    assert 1 in moods and -1 in moods and 0 in moods


# ---- the pressure cycle (sleep()/setSleepLapse/setAwakeLapse/checkNap) -------

def test_sleep_length_scales_with_energy_debt():
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.max_energy = p.energy = 24               # species init overrides ctor kwargs
    p._fall_asleep()
    assert p.awake_limit == 360.0              # full bar: the 6h minimum
    p2 = Pet(num=100, stage="Champion", attribute="Vaccine")
    p2.max_energy, p2.energy = 24, -24
    p2._fall_asleep()
    assert p2.awake_limit == 900.0             # deep debt: capped at 15h
    assert p2.sleep_limit == 1440.0 - 900.0    # next awake stretch shrinks to match


def test_babies_nap_constantly():
    from tuipet import data
    baby = next(n for n, r in data.load_requirements().items()
                if r.get("sleep_lapse_inc", 1) == 9)
    p = Pet(num=baby, stage="Fresh")
    assert p._sleep_inc() == 9                 # pressure races: ~2h awake stretches


def test_lights_out_starts_a_nap_that_lights_end():
    random.seed(5)
    p = Pet(num=100, stage="Champion", attribute="Vaccine")   # adult: pressure inc 1
    p.world_seconds = 10 * 60.0
    p.sleep_lapse = 200.0                      # mid-cycle: nowhere near bedtime
    p.lights = False                           # the player turns in early
    p.tick(1.0)
    assert p.asleep and p.nap
    assert p.awake_lapse == p.awake_limit - 201   # the nap only runs the earned pressure
    p.toggle_lights()                          # lights back ON
    assert p.lights and not p.asleep and not p.nap


def test_near_bedtime_lights_out_is_real_sleep():
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.sleep_lapse = p.sleep_limit - 10         # inside the sleepNotNap edge (90min)
    p.lights = False
    p.tick(1.0)
    assert p.asleep and not p.nap              # real sleep, not a nap
