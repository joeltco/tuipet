"""careBonusOnReset — the whole-life report card (care-bonus audit 2026-07-05).

Canon grades the DEPARTED at the next generation's start and the result seeds
the new egg's evol_bonus.  Order matters: the Digimemory etch runs first and
SPENDS the bonus, so an etched life grades from zero + the card.  Legs (config
col 0): clean-final-stage +1 / else -mistakes; final mood Happy +1, non-Neutral
-1; obedience >75 +1, <50 -1; lifetime win rate >=90 +1; whole days past the
growth curve (negative when short-lived); stage extras Champion +1-not-Failed
+1@attr175 +1@battles>30, Ultimate +2/225/50, Mega +3/300/75; clamp >= 0."""
import random

from tuipet.pet import Pet, BONUS_STAGE, BONUS_INC_OBEDIENCE, BONUS_DEC_OBEDIENCE
from tuipet import persistence


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=60)
    p.world_seconds = 12 * 60.0
    p.mood = 0                      # Neutral: no mood leg unless a test sets it
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_config_parity():
    assert (BONUS_INC_OBEDIENCE, BONUS_DEC_OBEDIENCE) == (75, 50)
    assert BONUS_STAGE == {"Champion": (0, 175, 30),
                           "Ultimate": (2, 225, 50), "Mega": (3, 300, 75)}


def test_the_full_report_card_adds_up():
    random.seed(3)
    p = Pet(num=296, name="Elder", stage="Mega", attribute="Vaccine",
            vaccine=140, data_power=120, virus=90, obedience=800)
    p.world_seconds = 12 * 60.0
    p.mood = 280
    p.battles, p.wins = 100, 95
    p.age_seconds = p._growth_period() + 3 * 1440
    p.evol_bonus = 0                # the etch spent it
    # clean +1, happy +1, obedient +1, winrate +1, 3 days +3, mega +3,
    # attr 350>=300 +1, battles>75 +1
    assert p.final_care_grade() == 12


def test_mistakes_and_misery_drag_it_to_the_floor():
    q = _pet(obedience=20, care_mistakes=8, battles=4, wins=0)
    q.mood = -200
    q.age_seconds = 200.0
    q.evol_bonus = 2
    assert q.final_care_grade() == 0             # clamped, never negative


def test_each_leg_moves_the_grade():
    base = _pet(age_seconds=_pet()._growth_period())    # zero longevity days
    g0 = base.final_care_grade()
    happy = _pet(age_seconds=base.age_seconds)
    happy.mood = 280
    assert happy.final_care_grade() == g0 + 1
    sad = _pet(age_seconds=base.age_seconds)
    sad.mood = -200
    assert sad.final_care_grade() == g0 - 1
    obedient = _pet(age_seconds=base.age_seconds, obedience=100)
    assert obedient.final_care_grade() == g0 + 1
    slob = _pet(age_seconds=base.age_seconds, care_mistakes=3)
    assert slob.final_care_grade() == max(0, g0 - 4)    # -3 mistakes, -1 lost clean bonus


def test_the_seed_rides_to_the_next_generation():
    persistence.bank_bonus_seed(7)
    assert persistence.take_bonus_seed() == 7
    assert persistence.take_bonus_seed() == 0            # one seed, one egg
