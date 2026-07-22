"""careBonusOnReset — the whole-life report card (care-bonus audit 2026-07-05).

Canon grades the DEPARTED at the next generation's start and the result seeds
the new egg's evol_bonus.  Order matters: the Digimemory etch runs first and
SPENDS the bonus, so an etched life grades from zero + the card.  Legs (config
col 0): clean-final-stage +1 / else -mistakes; final mood Happy +1, non-Neutral
-1 (the DERIVED word since the meter left); lifetime win rate >=90 +1; whole
days past the growth curve (negative when short-lived); stage extras Champion
+1-not-Failed +1@attr175 +1@battles>30, Ultimate +2/225/50, Mega +3/300/75;
clamp >= 0.  (The obedience legs left with the discipline system -- the
pinned-0 meter docked EVERY life -1; MED audit 2026-07-19.)"""
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
    p.battles, p.wins = 100, 95
    p.age_seconds = p._growth_period() + 3 * 86400
    p.evol_bonus = 0                # the etch spent it
    # clean +1, Happy +1, winrate +1, 3 days +3, mega +3, attr 350>=300 +1,
    # battles>75 +1  (the obedience legs left with the discipline system).
    # The Happy leg: under the old remaining-life rule this pet was an
    # ACCIDENTAL elder (age 266280 > lifespan-window) and "elderly" pinned
    # the mood word Neutral; the age-based elder line (DSprite mortality
    # 2026-07-22) reads 3 days old -- a perfectly kept pet grades Happy.
    assert p.final_care_grade() == 11


def test_a_real_mega_life_no_longer_grades_zero():
    """H2 (gameplay audit 2026-07-19): _growth_period summed Mega's 9e9
    "never auto-evolves" sentinel, so int((age - 9e9)/day) buried every real
    Mega at max(0, ...) = 0 -- the best life in the game always seeded +0."""
    p = Pet(num=296, name="Elder", stage="Mega", attribute="Vaccine",
            vaccine=140, data_power=120, virus=90, obedience=800)
    p.world_seconds = 12 * 60.0
    p.age_seconds = 432000.0        # a full natural Mega lifespan (5 real days)
    assert p._growth_period() < 1e5                     # the sentinel stays out
    assert p.final_care_grade() > 0


def test_longevity_speaks_the_memorial_day():
    """H2's other end: dividing by the 1440 game-min day paid +175..+295 for
    ANY natural life, swamping the card's +-1 legs.  The longevity leg counts
    the same 86400s day the memorial's "Lived N days" shows."""
    p = _pet()
    p.age_seconds = p._growth_period() + 2 * 86400      # 2 shown days past the curve
    two = p.final_care_grade()
    p.age_seconds = p._growth_period()
    assert two == p.final_care_grade() + 2


def test_mistakes_and_misery_drag_it_to_the_floor():
    q = _pet(obedience=20, care_mistakes=8, battles=4, wins=0)
    q.mood = -200
    q.age_seconds = 200.0
    q.evol_bonus = 2
    assert q.final_care_grade() == 0             # clamped, never negative


def test_each_leg_moves_the_grade():
    base = _pet(age_seconds=_pet()._growth_period())    # zero longevity days
    g0 = base.final_care_grade()
    # the obedience meter is PINNED (discipline system gone): any stored
    # value must move nothing -- the old <50 leg docked every graded life
    # (MED audit 2026-07-19)
    for dead_meter in (0, 100):
        same = _pet(age_seconds=base.age_seconds, obedience=dead_meter)
        assert same.final_care_grade() == g0
    slob = _pet(age_seconds=base.age_seconds, care_mistakes=3)
    assert slob.final_care_grade() == max(0, g0 - 4)    # -3 mistakes, -1 lost clean bonus


def test_the_seed_rides_to_the_next_generation():
    persistence.bank_bonus_seed(7)
    assert persistence.take_bonus_seed() == 7
    assert persistence.take_bonus_seed() == 0            # one seed, one egg


def test_a_perfectly_kept_pet_finally_reads_happy():
    """M1 (MED audit 2026-07-19): the derived mood stopped at Neutral, so the
    Happy tier -- the good birthday, the battle power doubling, the happy
    idle, the grade's +1 -- was unreachable for the life of the app.  Happy =
    condition tier 3 with nothing else wrong, the bright-walk-pose bar."""
    kept = _pet()                       # defaults: full hunger/effort/energy
    assert kept.status_word() == "ok" and kept.condition() == 3
    assert kept.current_mood() == "Happy"
    tired = _pet(energy=0)
    assert tired.current_mood() == "Neutral"     # tier drops, no free Happy
    sick = _pet(sick=True)
    assert sick.current_mood() == "Unhappy"      # unwell still trumps gauges


def test_the_happy_leg_pays_the_grade():
    base = _pet(age_seconds=_pet()._growth_period(), energy=0)   # Neutral
    kept = _pet(age_seconds=base.age_seconds)                    # Happy
    if kept.current_mood() == "Happy":           # geriatric ages read elderly
        assert kept.final_care_grade() == base.final_care_grade() + 1
    else:
        young = _pet()
        assert young.current_mood() == "Happy"
