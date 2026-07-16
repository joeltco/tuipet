"""Sleep-system canon audit pins (2026-07-06) vs DVPet PhysicalState.

Most of the system was already verbatim from the bedtime/lines/mood arcs
(pressure clock, sleepNotNap edge, nap pay-down + the nap-to-night conversion
with its `napEnergyInc - 1` residue, the MoreSleepChance jitter, the lit
stall, wake rolls, disturbs, the item Sleep flag).  Found: the nap was
INSTANT on lights-off -- canon waits out toNapSleepLapse/calcToSleepNapLapse
first (energy-shaded; canon's real anti-farm for the +10 nap mood); sick/inj
naps run a fixed hour; and a pet on the edge of sleep never tantrums."""
import random

from tuipet.pet import (Pet, TO_NAP_HIGH_ENERGY, TO_NAP_LOW_ENERGY,
                        TO_NAP_OBEDIENCE_FACTOR)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p.mood = 100
    p.sleep_lapse = 100.0              # mid-cycle: nowhere near bedtime
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# --- calcToSleepNapLapse --------------------------------------------------------

def test_the_doze_off_wait_is_energy_and_temperament_shaded():
    perky = _pet(energy=20, max_energy=24, obedience=0)
    assert perky._calc_to_nap() == TO_NAP_HIGH_ENERGY + 1     # +1: not well-drilled
    drained = _pet(energy=0, max_energy=24, obedience=0)
    assert drained._calc_to_nap() == TO_NAP_LOW_ENERGY + 1
    drilled = _pet(energy=0, obedience=TO_NAP_OBEDIENCE_FACTOR)
    assert drilled._calc_to_nap() == TO_NAP_LOW_ENERGY        # the +1 drops
    restless = _pet(energy=0, obedience=0, restless=1)
    assert restless._calc_to_nap() == TO_NAP_LOW_ENERGY + 2   # +restless +1

def test_lights_off_does_not_nap_instantly():
    p = _pet(energy=20, max_energy=24)   # perky: the long 41-minute wait
    p.lights = False
    for _ in range(30):
        p.tick(1.0)
    assert not p.asleep                  # still blinking in the dark
    for _ in range(20):
        p.tick(1.0)
        if p.asleep:
            break
    assert p.asleep and p.nap            # ...then it folds

def test_the_light_coming_back_resets_the_wait():
    p = _pet(energy=0, obedience=0)      # wait 21
    p.lights = False
    for _ in range(15):
        p.tick(1.0)
    assert not p.asleep
    p.lights = True
    p.tick(1.0)                          # the light resets the counter
    p.lights = False
    for _ in range(15):
        p.tick(1.0)
    assert not p.asleep                  # a fresh 21 is owed


# --- checkNap's nap length ------------------------------------------------------

def test_a_sick_pets_nap_runs_a_fixed_hour():
    p = _pet(energy=0, obedience=0, sick=True, sick_length=300.0)
    p.lights = False
    for _ in range(30):
        p.tick(1.0)
        if p.asleep:
            break
    assert p.asleep and p.nap
    assert p.awake_lapse == p.awake_limit - 60.0   # awakeLimit - minutesHour

def test_a_healthy_nap_repays_the_earned_pressure():
    p = _pet(energy=0, obedience=0)
    p.lights = False
    for _ in range(30):
        p.tick(1.0)
        if p.asleep:
            break
    assert p.asleep and p.nap
    assert p.awake_lapse == p.awake_limit - p.sleep_lapse


