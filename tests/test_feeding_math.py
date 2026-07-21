"""Feeding/medicine math audit (2026-07): canon re-verification vs
PhysicalState.feed/applyFood/applyConsumable/feedMed/applyBandage/
checkDirtyEating/checkIntolerantFoodSick + config.csv column 1.

Verified matching: the fullness modifier ((hunger-full)/stomach, 1.0 for
strength foods), the taste-tier mood branches incl. the glutton mods, the
too-full refusal + overeat path, wolf-down pre-meal, nutrition ceil
scaling, intolerance rolls (50/50), the med double-dose structure and the
cured bonus /MaxLength shape, bandage double-wrap, checkMaxHoursBeforeSleep
(a bedtime-only-food gate: data-empty in the corpus, noted).

Fixed (canon divergences):
 * load_foods dropped SEVEN live columns: 39 calorie foods, 3 lifespan
   foods, 7 attribute foods, a sleep food, 2 temp foods had no effect.
 * The calorie buffer was a flat refill; canon ADDS the food's calories
   (a snack buffers less than a feast) and fattens by FoodWeightChange
   when calories rise while already positive.
 * Food weight was unscaled by the fullness modifier.
 * checkDirtyEating was unported: a meal amid filth costs mood -10 and
   rolls sickness per pile (16%/8%).
 * BadMedLifeDec is 3600 REAL-seconds: the port stored 3600 game-seconds
   -- a double dose cost 2.5 game-DAYS instead of one game-hour."""

from tuipet.pet import Pet
from tuipet import data


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _food(name):
    return next(f for f in data.load_foods() if f["name"] == name)


def test_calories_rising_while_positive_fatten():
    rich = next(f for f in data.load_foods() if f.get("calories", 0) >= 2)
    p = _pet(hunger=0, calories=2, weight=20)
    w0 = p.weight
    p.feed(dict(rich))
    base_w = int(rich.get("weight", 1))
    assert p.weight >= w0 + base_w + 1          # +FoodWeightChange on top of the food's own


# (test_dirty_eating_sours_and_sickens left with the sickness system -- BASIC VPET 2026-07-17)


# (test_clean_room_meals_never_roll_sickness left with the sickness system -- BASIC VPET 2026-07-17)


