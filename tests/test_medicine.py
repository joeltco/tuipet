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
    assert p.lifespan == life0 - 3600.0        # BadMedLifeDec
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
    assert p.lifespan == life0 - 7200.0        # BadVitaminLifeDec
    assert p.mood < m0
