"""LINES_SPEC arc 2 — the bedtime clock, call-light mistake unification, the
canon pacing curve, and the sharpened death rules."""
import random

import pytest

from tuipet import lines
from tuipet.pet import Pet


def _line_pet(to_agumon=True):
    random.seed(11)
    p = Pet.new_egg(egg_type=1)
    p._hatch_into_fresh()
    if to_agumon:
        for _ in range(2):
            p.stage_seconds = 9e8
            p._maybe_evolve()
    p.world_seconds = 12 * 60.0          # noon, wide awake
    p.asleep = p.nap = False
    return p


def _corpus_pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 12 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _run(p, minutes):
    for _ in range(int(minutes)):
        p.tick(1.0)


# ---- pacing ---------------------------------------------------------------------

def test_stage_pacing_is_the_canon_curve():
    d = Pet.STAGE_DURATION
    assert Pet.EGG_DURATION == 60
    assert (d["Fresh"], d["InTraining"], d["Rookie"]) == (180, 360, 1440)
    assert (d["Champion"], d["Ultimate"]) == (2160, 2880)
    assert d["Fresh"] < d["InTraining"] < d["Rookie"] < d["Champion"] < d["Ultimate"]


# ---- bedtime clock (line pets) ---------------------------------------------------

def test_line_pet_sleeps_at_its_bedtime_and_wakes_at_seven():
    p = _line_pet()                       # Agumon, bedtime 21:00
    assert lines.bedtime_minutes(p) == 21 * 60
    p.world_seconds = 20 * 60 + 58.0
    _run(p, 4)
    assert p.asleep and not p.nap         # 21:00: down for the night
    p.lights = False
    _run(p, 9 * 60 + 55)                  # just before 7:00 -- checked at 6:5x
    assert p.asleep
    _run(p, 10)
    assert not p.asleep                   # 7:00 sharp
    assert 420 <= p.world_seconds % 1440 < 435


def test_midnight_bedtime_wraps():
    p = _line_pet()
    p.evolve_to(102)                      # Devimon sleeps at 24:00
    assert lines.bedtime_minutes(p) == 0
    p.world_seconds = 23 * 60 + 30.0      # 23:30: still up
    p.asleep = False
    _run(p, 5)
    assert not p.asleep
    _run(p, 30)                           # midnight
    assert p.asleep and not p.nap


def test_lit_sleep_logs_one_mistake_lights_off_avoids_it():
    p = _line_pet()
    p.world_seconds = 20 * 60 + 59.0
    _run(p, 3)
    assert p.asleep and p.lights
    cm0 = p.care_mistakes
    _run(p, 70)                           # a lit hour: the once-per-night mistake
    assert p.care_mistakes == cm0 + 1
    _run(p, 120)
    assert p.care_mistakes == cm0 + 1     # once per night, not per hour
    # a dutiful night: lights off inside the grace -> no mistake
    q = _line_pet()
    q.world_seconds = 20 * 60 + 59.0
    _run(q, 3)
    q.toggle_lights()
    cm0 = q.care_mistakes
    _run(q, 300)
    assert q.care_mistakes == cm0


def test_daytime_lights_off_is_a_nap_not_the_night():
    p = _line_pet()                       # noon
    p.toggle_lights()
    p.tick(1.0)
    assert p.asleep and p.nap
    _run(p, 300)                          # held for 5 game-hours: still just a nap
    assert p.nap                          # never converts to the night outside the window
    p.toggle_lights()
    p.tick(1.0)
    assert not p.asleep                   # lights wake a nap


def test_disturbed_line_pet_resleeps_by_the_clock():
    random.seed(3)
    p = _line_pet()
    p.world_seconds = 21 * 60 + 30.0
    p._tick_bedtime(1.0)
    assert p.asleep
    p.energy = -p.max_energy              # deep in debt: the disturb postpones
    msg = p._disturbed()
    assert not p.asleep and p.disturb == 1
    assert getattr(p, "_bed_postpone_t", 0) > 0
    _run(p, 61)                           # the grumbling window passes inside the night
    assert p.asleep


def test_corpus_pet_keeps_the_pressure_model():
    p = _corpus_pet()
    assert p._in_sleep_window() is None
    p.world_seconds = 21 * 60.0           # a corpus pet has no bedtime
    p.sleep_lapse = 0.0
    p.tick(1.0)
    assert not p.asleep


# ---- call-light unification -------------------------------------------------------

def test_filth_no_longer_counts_as_a_care_mistake():
    p = _corpus_pet(poop=4, poop_sizes=[2, 2, 2, 2])
    cm0 = p.care_mistakes
    p._filth_t = 1800
    p._tick_body(1.0)
    assert p.care_mistakes == cm0         # acts up (scold) but no mistake -- Pen20
    assert p.scold_flag


def test_hunger_call_is_one_mistake_per_call():
    p = _corpus_pet(hunger=0)
    cm0 = p.care_mistakes
    p._tick_hunger(600.0)
    assert p.care_mistakes == cm0 + 1
    p._tick_hunger(600.0)                 # postponed: silence right after
    assert p.care_mistakes == cm0 + 1


# ---- death rules -----------------------------------------------------------------

def test_six_game_hours_of_malady_is_fatal():
    p = _corpus_pet()
    p.sick, p.sick_length = True, 10 ** 9    # never heals (kept sick by worsening)
    for _ in range(360):
        p.tick(1.0)
        if p.dead:
            break
    assert p.dead
    q = _corpus_pet()
    q.sick, q.sick_length = True, 100.0      # a natural spell: heals inside the window
    for _ in range(360):
        q.tick(1.0)
    assert not q.dead and not q.sick


def test_late_stage_five_mistakes_is_fatal_only_past_the_window():
    p = _corpus_pet()
    p.stage = "Ultimate"
    p.care_mistakes, p.stage_seconds = 5, 100.0
    assert not p._tick_mortality(1.0)        # window not open yet
    p.stage_seconds = Pet.LATE_STAGE_WINDOW
    assert p._tick_mortality(1.0) and p.dead
    young = _corpus_pet()                     # Champion: the rule never applies
    young.care_mistakes, young.stage_seconds = 7, 9e8
    assert not young._tick_mortality(1.0)


def test_new_game_dawns_at_eight():
    p = Pet.new_egg(egg_type=1)
    assert p.world_seconds % 1440 == 8 * 60   # never hatch a baby into its bedtime


def test_disturb_postpone_lands_in_the_canon_band():
    """Sleep audit 2026-07-05: a disturbed line pet grumbles for
    DisturbPostpone (10..60) game-minutes before re-sleeping -- pinned across
    seeds so the band can't drift.  (An earlier probe misread ticks/60 as the
    unit and cried instant re-sleep: a tick IS a game-minute.)"""
    import random
    from tuipet.pet import Pet, DISTURB_POSTPONE
    assert DISTURB_POSTPONE == (10, 60)
    for seed in (7, 11, 23):
        random.seed(seed)
        p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=500)
        p.line_id = "ver1"
        p.world_seconds = 23 * 60.0 + 30
        p.hunger = 4
        for _ in range(3 * 60):
            p.tick(1.0)
            p.hunger = 4
        assert p.asleep and not p.nap
        p.energy = 5
        p.hunger = 2
        p.feed()                              # bothering real sleep
        assert not p.asleep
        for i in range(1, 70):
            p.tick(1.0)
            p.hunger = 4
            p.sick = False
            if p.asleep:
                break
        assert DISTURB_POSTPONE[0] <= i <= DISTURB_POSTPONE[1] + 2


def test_full_cared_night_refills_energy_and_dp_without_mistakes():
    """The two-night integration: bedtime -> keeper dims within grace (zero
    mistakes) -> 7:00 wake with energy and the DP meter refilled."""
    import random
    from tuipet.pet import Pet, DAY_MINUTES, DP_MAX
    random.seed(7)
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=500)
    p.line_id = "ver1"
    p.world_seconds = 12 * 60.0
    p.energy, p.hunger, p.dp = 5, 4, 0
    m0 = p.care_mistakes
    for _ in range(int(1.2 * DAY_MINUTES)):
        p.tick(1.0)
        p.hunger = 4
        p.sick = False
        mod = int(p.world_seconds % DAY_MINUTES)
        if p.asleep and p.lights and mod > 10 and (mod > 24 * 30 or mod < 7 * 60):
            p.toggle_lights()                 # dim within the grace
        if not p.asleep and not p.lights:
            p.toggle_lights()
    assert p.care_mistakes == m0              # the ritual done right costs nothing
    assert p.energy >= p.max_energy - 3       # a night's rest refills
    assert p.dp == DP_MAX                     # Pen20: sleep recharges the meter
