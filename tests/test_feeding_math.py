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
import random

from tuipet.pet import Pet, CALORIE_LIMIT
from tuipet import data


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _food(name):
    return next(f for f in data.load_foods() if f["name"] == name)


def test_calories_add_per_food_not_flat_refill():
    rich = next(f for f in data.load_foods() if f.get("calories", 0) >= 3)
    p = _pet(hunger=0, calories=0)
    p.feed(dict(rich, hunger=1))
    assert 0 < p.calories <= CALORIE_LIMIT
    q = _pet(hunger=0, calories=-4)
    q.feed(_food("Meat"))                       # Meat: calories column drives it
    assert q.calories == -4 + _food("Meat").get("calories", 0)


def test_calories_rising_while_positive_fatten():
    rich = next(f for f in data.load_foods() if f.get("calories", 0) >= 2)
    p = _pet(hunger=0, calories=2, weight=20)
    w0 = p.weight
    p.feed(dict(rich))
    base_w = int(rich.get("weight", 1))
    assert p.weight >= w0 + base_w + 1          # +FoodWeightChange on top of the food's own


def test_attribute_and_lifespan_foods_do_something():
    va = next((f for f in data.load_foods() if f.get("vaccine", 0) > 0), None)
    assert va is not None
    p = _pet(hunger=0)
    v0 = p.vaccine
    p.feed(dict(va))
    assert p.vaccine > v0
    lf = next((f for f in data.load_foods() if f.get("seconds", 0) > 0), None)
    assert lf is not None
    q = _pet(hunger=0)
    l0 = q.lifespan
    q.feed(dict(lf))
    assert q.lifespan == l0 + lf["seconds"] / 60.0   # real-sec -> the game scale


def test_dirty_eating_sours_and_sickens():
    p = _pet(hunger=0, poop=3, poop_sizes=[2, 2, 2], mood=100)
    random.seed(0)
    m0 = p.mood
    p.feed(_food("Meat"))
    assert p.mood < m0                          # DirtyEatingMoodDec outweighs Meat's +5
    random.seed(3)
    hits = 0
    for _ in range(80):
        q = _pet(hunger=0, poop=4, poop_sizes=[2] * 4)
        q.feed(_food("Meat"))
        hits += q.sick
    assert hits > 8                             # 8% x 4 piles = ~32% per meal


def test_clean_room_meals_never_roll_sickness():
    random.seed(1)
    for _ in range(60):
        p = _pet(hunger=0, poop=0)
        p.feed(_food("Meat"))
        assert not p.sick


def test_double_dose_costs_one_game_hour():
    p = _pet(sick=True, sick_length=5.0)
    p.med_lapse = 10.0                          # the indicator still runs
    life0 = p.lifespan
    msg = p._feed_med()
    assert "poison" in msg
    assert p.lifespan == life0 - 60.0           # 3600 REAL-sec / 60, not 3600 game-sec


def test_feed_taste_branches_take_canon_shape():
    """feed()'s taste branches (feed/food audit 2026-07-06): the glutton shade
    rides every branch, fullness GATES the pleasant moods, and a full pet fed
    its DISLIKED meal pays the double dip plus the spirit hit."""
    from tuipet.pet import (FAV_FOOD_MOOD, FOOD_MOOD, FAV_FOOD_ENTH,
                            GLUTTON_FEED_MOOD, DISLIKED_FOOD_OBEDIENCE)
    # hungry + favourite + glutton: +10 +1 shade, spirit +1
    p = _pet(hunger=1, glutton=1, mood=0, enthusiasm=0)
    p.favorite_food = "Meat"
    p._eat_food("Meat")
    assert p.mood == FAV_FOOD_MOOD + GLUTTON_FEED_MOOD and p.enthusiasm == FAV_FOOD_ENTH
    # FULL + favourite (non-glutton): the fav joy is gone, but the SPECIES
    # stomach (canon getStomachCapacity; food audit 2026-07-15) still has
    # room at 4 hearts, so the small food mood lands (canon's elif branch)
    q = _pet(hunger=4, glutton=0, mood=0, enthusiasm=0)
    q.favorite_food = "Meat"
    q._eat_food("Meat")
    assert q.mood == FOOD_MOOD and q.enthusiasm == 0
    # FULL + disliked, forced: the double dip + the spirit hit + obedience
    r = _pet(hunger=4, glutton=0, mood=0, enthusiasm=0, obedience=50)
    r.disliked_food = "Veg"
    r._eat_food("Veg", complied=True)
    assert r.mood <= -2 * FAV_FOOD_MOOD          # two dips (taste decs may add)
    assert r.enthusiasm <= -FAV_FOOD_ENTH        # -(1) - forced(1) before boundary fx
    assert r.obedience == 50 + DISLIKED_FOOD_OBEDIENCE
    # hungry + neutral + picky eater: +2 -1 shade
    s = _pet(hunger=1, glutton=-1, mood=0)
    s._eat_food("Fish")
    assert s.mood == FOOD_MOOD - 1
