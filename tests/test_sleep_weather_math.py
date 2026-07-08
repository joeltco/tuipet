"""Sleep/weather math audit (2026-07): canon re-verification vs
PhysicalState.sleepDecay / setAwakeLapse / checkNapEnergy / incSleepMinutes /
hungerDecay / checkTemp / getAdjustedDayTemp / setDayTemp / checkWeather /
calcWeather + config.csv column 1.

Verified matching: the whole weather transition machine line-for-line
(WeatherChangeChance IS 7 -- the old docstring claimed a deviation that
never existed), calcWeather's warm/cold variants, the temp factors
(2/3/5/7/10 + per-habitat night 10 / morning 3), the seasonal day-temp
roll (randint inclusive per habitat), the ideal-band mood numbers, the
sleep-pressure clock and the lights-neglect mistake.  ChangeToPrefTemp
foods are data-empty (noted).

Fixed (canon divergences):
 * NAP SIGN INVERSION: a nap PAYS DOWN sleepLapse (the old += encoded the
   opposite), and a nap held past ChangeNapToSleepMinutes (+restless x10)
   BECOMES the night (pressure clears, nap=false).
 * The wake clock ignored the species AwakeLapseInc (93 corpus babies
   sleep 16x shorter) and never modeled the lights-on stall
   (LightsOnAwakeLapseUnchangedChance 50%: lit rest is poor rest).
 * Sleep/nap energy paid DIRECTLY per jitter roll, misreading NapEnergyMin
   (a cadence) as an amount; canon routes through the incSleepMinutes /
   checkNapEnergy ACCUMULATORS, with NegativeEnergyGain 6 for a drained
   pet.
 * Asleep hunger was frozen; canon drains it to the SleepMinHungerDecay
   floor (3) -- one heart overnight, then it holds.
 * The sick fever/chills lurch (checkTemp: 1% +-30 per check) was
   unported."""
import random

from tuipet.pet import Pet


def _adult(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _asleep(p):
    p.sleep_lapse = p.sleep_limit
    p.tick(1.0)
    assert p.asleep
    return p


def test_babies_wake_sixteen_times_faster():
    from tuipet import data
    baby = data.load_requirements().get(1, {})
    assert baby.get("awake_inc", 1) == 16      # the loader reads the species column
    adult = data.load_requirements().get(100, {})
    assert adult.get("awake_inc", 1) in (1, 2)


def test_lights_on_stalls_the_wake_clock():
    random.seed(0)
    lit = _asleep(_adult())
    lit.lights = True
    dark = _asleep(_adult())
    dark.lights = False
    random.seed(5)
    for _ in range(120):
        lit.tick(1.0)
    random.seed(5)
    for _ in range(120):
        dark.tick(1.0)
    assert lit.awake_lapse < dark.awake_lapse  # ~half the lit minutes stall


def test_drained_pet_recovers_faster_asleep():
    random.seed(2)
    drained = _asleep(_adult())
    drained.energy = -10
    e0 = drained.energy
    for _ in range(70):                        # past one SleepMinutesToEnergyGain crossing
        drained.tick(1.0)
        if drained.energy > e0:
            break
    assert drained.energy - e0 >= 6            # NegativeEnergyGain, not the species 3


def test_asleep_hunger_floors_at_three():
    random.seed(3)
    p = _asleep(_adult(hunger=4))
    p.lights = False                           # a dark room: no lights-neglect noise
    for _ in range(2600):                      # the calorie pipeline takes ~1100 game-min
        p.tick(1.0)
        if not p.asleep:
            p.sleep_lapse = p.sleep_limit      # keep it down all night
            p.tick(1.0)
    # one heart overnight, then the floor holds -- hunger never reaches the
    # 0 that a starvation mistake needs (piles still accrue filth mistakes
    # over a 2600-min neglect marathon; that is the poop system's business)
    assert p.hunger == 3


def test_sick_temperature_lurches():
    random.seed(1)
    p = _adult(sick=True, sick_length=9999.0, temp=50.0)
    p.sleep_limit = 9e9
    swings = 0
    last = p.temp
    for _ in range(600):
        p.tick(1.0)
        if abs(p.temp - last) >= 25:           # a +-30 lurch dwarfs the 0.05 drift
            swings += 1
        last = p.temp
    assert swings >= 3                         # ~2% per check over 600 checks


def test_healthy_temperature_never_lurches():
    random.seed(1)
    p = _adult(sick=False, temp=50.0)
    p.sleep_limit = 9e9
    last = p.temp
    for _ in range(400):
        p.tick(1.0)
        assert abs(p.temp - last) < 25
        last = p.temp
