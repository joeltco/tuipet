"""HOW FAST filth sickens a pet — the rate itself, not just the wiring.

Joel, 2026-07-30, playing 0.5.316: "mon is getting sick imedietly after poop?
1 poop? audit how this system is supposed to work, i thought it got sick after
4 poops for too long".  He was right and his mental model was the canon one.

FILTH_SICK_BOUND had shipped as 200 since 2026-07-25, described as
"FilthSickChanceBound 12000 real-min -> /60 game scale".  But the bound is a
probability DENOMINATOR, not a duration: dividing it multiplies the risk.
Canon (config.csv rows 812-814) is FilthSickMin=1, Bound=12000, Chance=1 --
piles/12000 once a minute -- and tuipet's minute is the game-minute, exactly
like every other ported constant on this clock.  At 200 a lone pile sickened
a pet in a MEDIAN 3.3 REAL MINUTES; at 12000 it takes a median 8.3 game-days
and a four-pile sty left uncleaned for a game-day lands ~38%.

These pins are about MAGNITUDE.  The wiring pins (pile scaling, species
multiplier, the away shield) live in test_liveplay_audit.py; a rate bug slips
past all of them, which is how this shipped.

The OVERWEIGHT leg (bottom half) was the same story one step behind: Joel
answered the flag with "fix the overweight one too".  It had no canon rate to
port -- canon punishes bad weight with mood, not illness -- so a step is now
priced at exactly one pile of filth, canon's only continuous sickness source.
"""
import math

from tuipet import petbase
from tuipet.pet import Pet

# one game-minute of dt is one real second at DAY_LENGTH 1440
GAME_MIN_PER_REAL_MIN = 60.0
GAME_MIN_PER_GAME_DAY = 1440.0


def _pet(piles):
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.poop, p.poop_sizes = piles, [2] * piles
    p.hunger = p.strength = 4
    p.weight = p._base_weight()
    return p


def _p_per_game_min(piles, pet=None):
    pet = pet or _pet(piles)
    mult = pet._phys().get("poop_sick_mult", 1.0) or 1.0
    return (petbase.FILTH_SICK_CHANCE * piles) / (petbase.FILTH_SICK_BOUND * mult)


def _chance_within(piles, game_mins):
    return 1.0 - math.exp(-_p_per_game_min(piles) * game_mins)


def test_the_bound_is_canon_and_never_scaled():
    """config.csv FilthSickChanceBound verbatim.  A /60 here is a 60x bug."""
    assert petbase.FILTH_SICK_BOUND == 12000
    assert petbase.FILTH_SICK_CHANCE == 1


def test_one_fresh_pile_is_not_a_death_sentence():
    """The exact complaint: a single pile must not sicken a pet in the minutes
    it takes to notice it.  At the old bound this was 27% and 78%."""
    assert _chance_within(1, GAME_MIN_PER_REAL_MIN) < 0.01
    assert _chance_within(1, 5 * GAME_MIN_PER_REAL_MIN) < 0.05


def test_a_neglected_sty_really_does_sicken():
    """The other half of the audit -- the risk must still be real, or filth
    stops mattering.  Four piles left a whole game-day is a coin-flip-ish
    threat; a week of that is near-certain."""
    day = _chance_within(4, GAME_MIN_PER_GAME_DAY)
    assert 0.25 < day < 0.55, day
    assert _chance_within(4, 7 * GAME_MIN_PER_GAME_DAY) > 0.95


def test_the_lone_pile_takes_canon_days_not_real_minutes():
    """Mean time-to-sick, stated in the units a player lives in."""
    mean_game_min = 1.0 / _p_per_game_min(1)
    assert mean_game_min / GAME_MIN_PER_GAME_DAY > 8.0        # canon: 8.33 days
    # and, in real time, longer than any single sitting
    assert mean_game_min / GAME_MIN_PER_REAL_MIN > 180.0      # > 3 real hours


def test_piles_scale_the_risk_linearly():
    base = _p_per_game_min(1)
    for piles in (2, 3, 4):
        assert math.isclose(_p_per_game_min(piles), base * piles, rel_tol=1e-9)


def test_the_rate_is_the_same_story_the_simulation_tells():
    """Belt and braces: drive the real tick and check the median lands in
    game-DAYS.  Coarse on purpose -- it fails loudly at the old bound
    (median ~200 game-min) without being flaky at the canon one."""
    import random as _r
    _r.seed(1917)
    hits = 0
    trials = 400
    horizon = int(GAME_MIN_PER_GAME_DAY)          # one game-day of ticks
    for _ in range(trials):
        p = _pet(1)
        for _ in range(horizon):
            p._filth_effects(1.0)
            if p.sick:
                hits += 1
                break
    rate = hits / trials
    assert 0.03 < rate < 0.22, rate                # canon expectation ~11%


# ---- the overweight leg, repriced (Joel: "fix the overweight one too") -----

def _heavy(steps):
    """`steps` = floor(excess / (base * 0.5)), so one step is 50% over base."""
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.poop, p.poop_sizes = 0, []
    p.hunger = p.strength = 4
    p.weight = p._base_weight() * (1.0 + 0.5 * steps)
    return p


def _overweight_p(steps):
    p = _heavy(steps)
    bw = p._base_weight()
    live = int((p.weight - bw) // (bw * 0.5)) if bw > 0 and p.weight > bw else 0
    assert live == steps, f"fixture drift: wanted {steps} steps, built {live}"
    return live * petbase.SICK_OVERWEIGHT_P


def test_one_overweight_step_costs_exactly_one_pile_of_filth():
    """The repricing rule, stated once: no canon weight-sickness exists, so a
    step is anchored to canon's only continuous source."""
    assert math.isclose(petbase.SICK_OVERWEIGHT_P,
                        petbase.FILTH_SICK_CHANCE / petbase.FILTH_SICK_BOUND)
    assert math.isclose(_overweight_p(1), _p_per_game_min(1))


def test_a_heavy_pet_is_not_sick_within_the_hour():
    """It shipped at 0.00375/game-min -- a median 4.4 REAL minutes at one
    step, 45x a pile of filth.  A player cannot diet a pet that fast."""
    within_5_real_min = 1.0 - math.exp(-_overweight_p(1) * 5 * GAME_MIN_PER_REAL_MIN)
    assert within_5_real_min < 0.05, within_5_real_min
    mean_game_min = 1.0 / _overweight_p(1)
    assert mean_game_min / GAME_MIN_PER_GAME_DAY > 8.0


def test_obesity_still_costs_something_over_days():
    """Repriced, not removed: two steps over (double base weight) is a real
    threat across a few game-days."""
    two_days = 1.0 - math.exp(-_overweight_p(2) * 2 * GAME_MIN_PER_GAME_DAY)
    assert two_days > 0.25, two_days


def test_the_steps_scale_and_stack_with_filth():
    """Independent rolls: a fat pet in a dirty room carries both risks."""
    assert math.isclose(_overweight_p(2), 2 * _overweight_p(1))
    import random as _r
    _r.seed(2718)
    caught = 0
    for _ in range(300):
        q = _heavy(2)
        q.poop, q.poop_sizes = 3, [2, 2, 2]
        for _ in range(int(GAME_MIN_PER_GAME_DAY)):
            q._filth_effects(1.0)
            q._tick_mortality(1.0)
            if q.sick:
                caught += 1
                break
    rate = caught / 300
    # 5 pile-equivalents for a game-day: ~1 - exp(-5*1440/12000) ~= 45%
    assert 0.25 < rate < 0.65, rate
