"""Sleep system vs DVPet: lightsCall neglect, wake auto-relight, morning moods."""
import random

from tuipet.pet import Pet, LIGHTS_MISTAKE_SEC


def _sleeper(lights, num=1, stage="Rookie"):
    p = Pet(num=num, stage=stage, attribute="Vaccine")
    p.energy = 5
    p.sleep_lapse = p.sleep_limit              # pressure clock rolls over (canon sleep())
    p.tick(1.0)                                # falls asleep (resets the lights counter)
    assert p.asleep
    p.lights = lights
    return p


def test_sleeping_with_lights_on_is_a_care_mistake():
    # an ADULT sleeper: babies (AwakeLapseInc 16) now canonically wake before
    # the lights-neglect threshold can land
    p = _sleeper(lights=True, num=100, stage="Champion")
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
    for _ in range(5):
        p.tick(1.0)
    assert not p.asleep                        # the doze-off WAIT holds it up first
    for _ in range(40):
        p.tick(1.0)
        if p.asleep:
            break
    assert p.asleep and p.nap
    # the nap only runs the pressure earned by the moment it dozed off
    assert p.awake_lapse == p.awake_limit - p.sleep_lapse
    p.toggle_lights()                          # lights back ON
    assert p.lights and not p.asleep and not p.nap


def test_near_bedtime_lights_out_is_real_sleep():
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.sleep_lapse = p.sleep_limit - 80         # inside the sleepNotNap edge (90min)
    p.lights = False
    for _ in range(45):                        # ride out the doze-off wait
        p.tick(1.0)
        if p.asleep:
            break
    assert p.asleep and not p.nap              # real sleep, not a nap
