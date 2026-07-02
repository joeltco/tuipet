"""Sleep system vs DVPet: lightsCall neglect, wake auto-relight, morning moods."""
import random

from tuipet.pet import Pet, LIGHTS_MISTAKE_SEC, DAY_LENGTH


def _sleeper(lights):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    p.world_seconds = DAY_LENGTH * 0.95        # night
    p.energy = 5
    p.tick(1.0)                                 # falls asleep (resets the lights counter)
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
    p.energy = p.max_energy                    # fully rested
    p.world_seconds = DAY_LENGTH * 0.4         # morning
    p.tick(1.0)
    assert not p.asleep
    assert p.lights                             # DVPet wake: setLights(true)


def test_morning_roll_can_move_the_mood():
    # across many seeded mornings, at least one good and one bad morning occur
    moods = set()
    for seed in range(30):
        random.seed(seed)
        p = _sleeper(lights=False)
        p.energy = p.max_energy
        p.mood = 0
        p.world_seconds = DAY_LENGTH * 0.4
        p.tick(1.0)
        moods.add((p.mood > 0) - (p.mood < 0))
    assert 1 in moods and -1 in moods and 0 in moods
