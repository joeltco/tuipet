"""Missed-day / birthday vs DVPet setTimeToAge + _mistakeDay + _bonus."""
from tuipet.pet import (Pet, DAY_LENGTH, BONUS_LIFE_INC, BONUS_LIFE_DEC,
                        GOOD_BIRTHDAY_FOOD, BAD_BIRTHDAY_FOOD, NORMAL_BIRTHDAY_FOOD)


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_good_birthday_needs_happy_majority_and_zero_slips():
    p = _pet(mistake_day=0)
    p.daily_mood = {"Happy": 100, "Neutral": 10, "Unhappy": 0, "Depressed": 0}
    life0, bonus0 = p.lifespan, p.evol_bonus
    p._birthday()
    assert p.lifespan == life0 + BONUS_LIFE_INC
    assert p.evol_bonus == bonus0 + 1
    assert p.inventory.get(GOOD_BIRTHDAY_FOOD) == 1            # a Cupcake
    assert p.mistake_day == 0 and sum(p.daily_mood.values()) == 0


def test_one_slip_spoils_the_good_birthday():
    p = _pet(mistake_day=1)
    p.daily_mood = {"Happy": 100, "Neutral": 0, "Unhappy": 0, "Depressed": 0}
    life0 = p.lifespan
    p._birthday()
    assert p.lifespan == life0                                  # normal day
    assert p.inventory.get(NORMAL_BIRTHDAY_FOOD) == 1           # a Cookie


def test_bad_birthday_costs_life_and_bonus():
    p = _pet(mistake_day=3, evol_bonus=2)
    p.daily_mood = {"Happy": 0, "Neutral": 5, "Unhappy": 50, "Depressed": 0}
    life0 = p.lifespan
    p._birthday()
    assert p.lifespan == life0 - BONUS_LIFE_DEC
    assert p.evol_bonus == 1
    assert p.inventory.get(BAD_BIRTHDAY_FOOD) == 1              # consolation Candy


def test_mood_tie_yields_a_normal_day():
    p = _pet(mistake_day=0)
    p.daily_mood = {"Happy": 50, "Neutral": 50, "Unhappy": 0, "Depressed": 0}
    life0 = p.lifespan
    p._birthday()
    assert p.lifespan == life0                                  # getMajority tie -> None
    assert p.inventory.get(NORMAL_BIRTHDAY_FOOD) == 1


def test_birthday_fires_on_the_age_day():
    p = _pet(mood=300)
    p.age_seconds = DAY_LENGTH - 1
    p.tick(2.0)                                                 # crosses day 1
    assert p.last_birthday == 1
    assert p.birthday_note != ""


def test_slips_mark_the_day():
    # (canon gates 2026-07-18: the full-belly feed is a PURE refuse -- the
    # DVPet mistake/weight penalty left; the overeat COUNTER still ticks
    # for the evolution corpus's OF gates)
    p = _pet()
    p._disturbed_dummy = None
    m0, of0 = p.mistake_day, p.overeat
    p.hunger = 4
    p.feed_meat()                                               # the overeat slip
    assert p.overeat == of0 + 1
    assert p.mistake_day == m0


