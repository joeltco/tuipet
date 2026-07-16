"""The clock-unit law, pinned (cadence audit 2026-07-14).

tuipet's clock maps ONE GAME MINUTE onto ONE REAL SECOND (DAY_LENGTH=1440s =
1440 game minutes).  Canon config.csv cadences are in GAME MINUTES, so a
`*Min=N` constant ports to N REAL SECONDS -- never N x 60.  Converting with
REAL minutes has now shipped FIVE bugs: TEMP_RATE, WEATHER_CHECK_SEC, and the
three neglect-pressure cadences below.

Two constants are DELIBERATE exceptions and must stay that way -- they are
documented in pet.py and pinned here so a future audit cannot "correct" them:
  * the care-MISTAKE timers keep a fair human response window (a literal port
    gives you TEN REAL SECONDS to answer an alarm before a permanent mistake);
  * FilthSickMin pairs with a bound that is already divided by 60 -- rolling
    60x less often against a 60x smaller bound is the SAME expected rate.
"""
import inspect

from tuipet import pet as P


def test_the_clock_maps_a_game_minute_to_a_real_second():
    assert P.DAY_LENGTH == 1440.0          # 1440 game minutes in a game day


def test_canon_cadences_are_ported_as_real_seconds():
    """Each of these is `canon *Min` (game minutes) used against a real-second
    accumulator, so the value must equal the canon number.  (The weather
    cadences left with the weather system; BASIC VPET 2026-07-16.)"""
    assert P.FILTH_MOOD_DEC_MIN == 5.0     # FilthMoodDecMin=5   (was 300 = 5 game HOURS)
    assert P.LIGHTS_MISTAKE_SEC == 60.0    # MinutesToMistakeLights=60
    assert P.SICK_LAPSE_MIN == 29          # SickLapseMin=29
    assert P.DEPRESSED_LAPSE_MIN == 59.0   # DepressedLapseMin=59
    assert P.GIFT_CHANCE_MIN == 57.0       # GiftChanceMin=57
    assert P.REFUSED_OFF_MIN == 10.0       # RefusedOffMin=10


def test_the_neglect_pressures_run_at_the_canon_cadence():
    """Filth mood, the held-poop nag and the care-call drain were all x60 too
    slow, so neglect barely hurt.  They are literals in the tick; pin the
    source so a regression is loud."""
    src = inspect.getsource(P)
    assert "self._poop_wait_t >= 1.0" in src, "PoopWaitMin=1 game-min"
    assert "self._call_drain_t >= 1.0" in src, "CallMinutesCheckMin=1 game-min"
    assert "self._sick_pen_t >= SICK_LAPSE_MIN" in src, "SickLapseMin=29, not 60"


def test_the_deliberate_exceptions_stay_deliberate():
    """These two must NOT be 'fixed' into the canon literal."""
    src = inspect.getsource(P)
    # the care-mistake response window: a literal port = 10 real seconds
    assert "self._hunger_call_t >= 600.0" in src
    assert "self._str_call_t >= 600.0" in src
    # FilthSickMin pairs with an already-/60 bound
    assert "self._filth_sick_t >= 60.0" in src
    assert P.FILTH_SICK_BOUND == 200


def test_good_care_is_never_punished_by_the_faster_pressure():
    """The canon cadences must bite the NEGLECTFUL owner, not the attentive
    one -- that is the whole test of whether the fix is fair."""
    import random
    random.seed(4)
    p = P.Pet(num=29, name="A", stage="Rookie", attribute="Vaccine", obedience=500)
    p.world_seconds = 8 * 60.0
    p.stage_seconds = -9e8                 # freeze evolution; watch the care record
    for _ in range(int(P.DAY_LENGTH)):
        if p.hunger == 0:
            p.feed()
        if p.poop:
            p.clean()
        if p.asleep and p.lights:
            p.toggle_lights()
        elif not p.asleep and not p.lights:
            p.toggle_lights()
        p.tick(1.0)
        p.world_seconds += 1.0
    assert p.care_mistakes == 0, "an attentive owner must take no care mistakes"
    # mood holds NEUTRAL, not positive: the ambient ideal-temp comfort tick
    # (+3/29s) left with the weather system (BASIC VPET 2026-07-16), so an
    # idle well-kept pet no longer drifts happy for free -- happiness now
    # comes only from active care (liked meals, play, praise)
    assert p.mood >= 0 and not p.dead
