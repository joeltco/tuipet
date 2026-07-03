"""Heal/medicine vs DVPet feedMed / applyBandage / feedVitamin / applyConsumable."""
from tuipet.pet import (Pet, SICK_LAPSE_MIN, INJ_LAPSE_MIN, MEDICINE_HOURS,
                        BANDAGE_HOURS, MAX_SICK_LENGTH, CURED_MOOD_BONUS)
from tuipet import data


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_medicine_shortens_the_illness_incrementally():
    p = _pet()
    p.sick = True
    p.sick_length = 5 * SICK_LAPSE_MIN
    msg = p.heal()
    assert p.sick and p.sick_length == 3 * SICK_LAPSE_MIN   # CureLapseChange -2
    assert p.med_lapse == MEDICINE_HOURS
    assert "helps" in msg


def test_final_dose_cures():
    p = _pet()
    p.sick = True
    p.sick_length = 2 * SICK_LAPSE_MIN
    msg = p.heal()
    assert not p.sick and p.sick_length == 0
    assert "worked" in msg


def test_double_dose_is_poison():
    p = _pet()
    p.sick = True
    p.sick_length = 5 * SICK_LAPSE_MIN
    p.med_lapse = MEDICINE_HOURS               # the indicator still runs
    life0, poop0 = p.lifespan, p.poop
    msg = p.heal()
    assert "poison" in msg
    # BadMedLifeDec 3600 REAL-sec -> 60 on the game-min scale (audit 2026-07:
    # the old 3600 game-sec pin encoded a 60x-too-harsh scaling bug)
    assert p.lifespan == life0 - 60.0
    assert p.poop == poop0 + 1                 # startPoop: it comes right up
    assert p.sick_length == 5 * SICK_LAPSE_MIN  # no healing from a bad dose


def test_bandage_heals_incrementally_and_refuses_a_second_wrap():
    p = _pet()
    p._injure() if hasattr(p, "_injure") else None
    p.injuries, p.inj_length = 1, 5 * INJ_LAPSE_MIN
    p.bandage_lapse = 0.0
    p.heal()
    assert p.inj_length == 3 * INJ_LAPSE_MIN   # HealLapseChange -2
    assert p.bandage_lapse == BANDAGE_HOURS
    msg = p.heal()                             # still wrapped
    assert "already bandaged" in msg
    assert p.inj_length == 3 * INJ_LAPSE_MIN


def test_sick_outranks_injury_for_the_button():
    p = _pet()
    p.sick, p.sick_length = True, 2 * SICK_LAPSE_MIN
    p.injuries, p.inj_length = 1, 2 * INJ_LAPSE_MIN
    p.heal()                                   # Medical: the med first
    assert not p.sick and p.inj_length == 2 * INJ_LAPSE_MIN


def test_elixir_is_the_instant_cure():
    p = _pet()
    p.sick, p.sick_length = True, 9 * SICK_LAPSE_MIN
    elixir = next(e for e in data.home_shop_pool() if e["name"] == "Elixir")
    p.inventory[elixir["key"]] = 1
    p.use_item(elixir["key"])
    assert not p.sick and p.sick_length == 0.0


def test_bad_vitamin_overdose():
    import random
    random.seed(0)
    p = _pet()
    p.vitamin_lapse = 30.0                     # the last dose still runs
    life0, m0 = p.lifespan, p.mood
    p.feed_vitamin()
    # BadVitaminLifeDec -- plus SickLifeDec (180) when the overdose roll sickens
    # (the canon burn economy, audit 2026-07)
    assert p.lifespan == life0 - 7200.0 - (180.0 if p.sick else 0.0)
    assert p.mood < m0


# ---- toys (applyItemNoObedience: interest + personality mood) ----------------

def test_toys_bore_the_pet_with_diminishing_returns():
    p = _pet()
    ball = data.consumable_by_key("i:3")             # Ball: mood 50, diminishing
    assert ball["diminishing"] and ball["interest_change"] == 1
    p.inventory["i:3"] = 10
    gains = []
    for _ in range(4):
        m0 = p.mood
        p.use_item("i:3")
        gains.append(p.mood - m0)
    assert gains[0] > gains[-1]                      # 1 - interest/5 scale bites
    assert p.item_interest == 4


def test_full_boredom_skips_the_scale():
    # canon quirk: at interest 5 the modifier (1 - 5/5 = 0) fails the >0 guard
    # and the toy lands at FULL strength again
    p = _pet(item_interest=5)
    p.inventory["i:3"] = 1
    m0 = p.mood
    p.use_item("i:3")
    assert p.mood - m0 >= 50


def test_interest_decays_faster_for_sunny_pets():
    p = _pet(item_interest=3, disposition=1)
    for _ in range(41):
        p.tick(1.0)
    assert p.item_interest == 2                      # ItemInterestLowTimer 40
    p2 = _pet(item_interest=3, disposition=-1)
    for _ in range(41):
        p2.tick(1.0)
    assert p2.item_interest == 3                     # sour pets stay bored (80)


def test_personality_mood_shapes_the_toy():
    dumbbell = data.consumable_by_key("i:7")         # dispo -1, restless +1
    grump = _pet(disposition=-1, restless=1)         # a match: +20 extra
    sunny = _pet(disposition=1, restless=-1)         # a clash: -20
    grump.inventory["i:7"] = sunny.inventory["i:7"] = 1
    g0, s0 = grump.mood, sunny.mood
    grump.use_item("i:7")
    sunny.use_item("i:7")
    # +-20 personality spread, +-1 each from setMood's disposition nudge
    assert (grump.mood - g0) - (sunny.mood - s0) == 38
