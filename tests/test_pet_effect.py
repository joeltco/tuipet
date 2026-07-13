"""The Futon care-effect lifecycle (careEffect.csv): apply, per-cadence rate gains,
end-on-sleep, expiry, and the care-call suppression flag.

Drives `_tick_effect` directly to isolate the effect engine from the rest of the
life-sim, plus one integration check through `use_item`.
"""
import pytest

from tuipet import data
from tuipet import weather as wx
from tuipet.pet import Pet
from conftest import futon_item


def _an_effect():
    eff = data.load_care_effects()
    if not eff:
        pytest.skip("no care effects loaded")
    eid = next(iter(eff))
    return eid, eff[eid]


def test_effect_decrements_and_gains():
    eid, eff = _an_effect()
    pet = Pet(num=-1, stage="Rookie", obedience=500)
    pet.mood = 0
    pet.effect_id, pet.effect_t = eid, float(eff["duration"])
    pet._eff_acc, pet._eff_asleep = 0.0, pet.asleep

    pet._tick_effect(60)
    assert pet.effect_t == eff["duration"] - 60, "duration should count down by dt"
    if eff["mood"][0] > 0:
        assert pet.mood > 0, "a positive mood rate should raise mood at the 60-tick cadence"


def test_effect_expires():
    eid, eff = _an_effect()
    pet = Pet(num=-1, stage="Rookie", obedience=500)
    pet.effect_id, pet.effect_t = eid, 5.0
    pet._eff_acc, pet._eff_asleep = 0.0, pet.asleep
    pet._tick_effect(10)                     # past the remaining 5s
    assert pet.effect_id == -1 and pet.effect_t == 0.0


def test_call_paused_reflects_data():
    eid, eff = _an_effect()
    pet = Pet(num=-1, stage="Rookie", obedience=500)
    pet.effect_id, pet.effect_t = eid, float(eff["duration"])
    assert pet.call_paused() == bool(eff["pause_call"])
    pet.effect_id = -1
    assert pet.call_paused() is False


def test_end_on_sleep_change():
    eid, eff = _an_effect()
    if not eff["end_on_sleep"]:
        pytest.skip("this effect does not end on sleep change")
    pet = Pet(num=-1, stage="Rookie", obedience=500)
    pet.asleep = False
    pet.effect_id, pet.effect_t = eid, float(eff["duration"])
    pet._eff_acc, pet._eff_asleep = 0.0, False
    pet.asleep = True                        # dozes off -> effect should end
    pet._tick_effect(0.1)
    assert pet.effect_id == -1


def test_effect_name():
    eid, eff = _an_effect()
    pet = Pet(num=-1, stage="Rookie", obedience=500)
    pet.effect_id = eid
    assert pet.effect_name() == eff["name"]
    pet.effect_id = -1
    assert pet.effect_name() == ""


def test_use_item_applies_effect(live_pet):
    """Using the Futon item lays out the care buff and consumes the item."""
    key, e = futon_item()
    if not key:
        pytest.skip("no care-effect item (Futon) in this build")
    pet = live_pet
    pet.inventory[key] = 1
    msg = pet.use_item(key)
    assert pet.effect_id == e["effect_id"]
    assert pet.effect_t > 0
    assert pet.inventory.get(key, 0) == 0, "item should be consumed"
    assert pet.name in msg or "settle" in msg.lower()


# --- PauseTemp: the futon pins the temperature (DVPet checkEveryTemp) -------
def _futon_pet():
    """A pet in the climate-controlled home (Hard Disk, weather_chance=0) so
    _update_weather's target is the deterministic ideal-band midpoint."""
    eid, eff = _an_effect()
    if not eff["pause_temp"]:
        pytest.skip("this effect does not pause temperature")
    pet = Pet(num=-1, stage="Rookie", obedience=500)
    pet.habitat = pet.home_habitat = 0
    assert pet.habitat_obj()["weather_chance"] <= 0
    return pet, eid, eff


def test_futon_pins_the_temperature():
    """Canon checkEveryTemp skips the WHOLE temp lapse under pauseTemp: a pet
    tucked in cold STAYS at that temperature -- it neither warms toward the
    day's target nor drifts colder (the pre-fix bug: a comfy pet could turn
    freezing UNDER its futon because only the mood check was paused)."""
    pet, eid, eff = _futon_pet()
    pet.temp = 10.0                          # well below freezing (32)
    pet.effect_id, pet.effect_t = eid, float(eff["duration"])
    pet._update_weather(60)
    assert pet.temp == 10.0, "an active futon must pin the temperature"
    assert pet.is_freezing(), "the futon maintains temperature; it is not a heater"
    pet.effect_id, pet.effect_t = -1, 0.0    # expiry: the lapse resumes
    pet._update_weather(60)
    assert pet.temp > 10.0, "temperature drift must resume once the effect ends"


def test_futon_pauses_the_sick_temperature_swings():
    """checkTemp's fever/chill lurches live INSIDE the paused lapse."""
    pet, eid, eff = _futon_pet()
    pet.temp = 50.0
    pet.sick = True
    pet.effect_id, pet.effect_t = eid, float(eff["duration"])
    for _ in range(300):                     # plenty of 1%-chance rolls
        pet._update_weather(1)
    assert pet.temp == 50.0, "sick fever/chill swings pause under the futon too"


def test_temp_mood_consequences_are_not_paused_by_the_futon():
    """Canon checkIdealTempMoodChange has NO pauseTemp gate: the pet keeps
    feeling the temperature it was tucked in at (a comfy pet locks in the
    comfort bonus; the old code wrongly skipped this under the futon)."""
    pet, eid, eff = _futon_pet()
    pet.temp = sum(pet.ideal_temp) / 2       # mid ideal band
    pet.mood = 0
    pet.effect_id, pet.effect_t = eid, float(eff["duration"])
    pet._comfort_t = 0.0
    pet._temperature_effects(wx.IDEAL_TEMP_MOOD_SEC)
    assert pet.mood > 0, "the ideal-temp mood check must keep running under the futon"


# --- bandage / medicine indicators (DVPet getBandage / getMed) --------------
def test_heal_lights_medicine_and_bandage_then_they_wear_off():
    """The Medical flows light the medicine/bandage indicators (feedMed/
    applyBandage -> medLapse/bandageLapse), which then wear off.  Treatment is
    incremental now, so each press treats ONE ailment (sick outranks injury)."""
    from tuipet.pet import Pet, MEDICINE_HOURS, BANDAGE_HOURS
    pet = Pet.from_num(29)
    pet.stage = "Rookie"
    pet.obedience = 500                     # out-roll the medicine refusal
    pet.sick = True
    pet.sick_length = 5.0                   # under one dose's worth
    pet.inj_length = 5.0
    assert not pet.has_medicine() and not pet.has_bandage()

    pet.heal()                              # the med first (Medical: Use Med)
    assert not pet.sick, "the dose finished the short illness"
    assert pet.has_medicine() and pet.med_lapse == MEDICINE_HOURS
    pet.heal()                              # then the bandage on the next press
    assert not pet.is_injured()
    assert pet.has_bandage() and pet.bandage_lapse == BANDAGE_HOURS

    for _ in range(int(max(MEDICINE_HOURS, BANDAGE_HOURS))):
        pet.tick(1.0)                       # DVPet medLapseMin/bandageLapseMin == 1 game-min
    assert not pet.has_medicine() and not pet.has_bandage(), "indicators wear off"


def test_medicine_bandage_persist():
    """The new lapse fields round-trip through asdict (persistence)."""
    from dataclasses import asdict
    from tuipet.pet import Pet
    pet = Pet.from_num(29)
    pet.med_lapse, pet.bandage_lapse = 30.0, 12.0
    d = asdict(pet)
    assert d["med_lapse"] == 30.0 and d["bandage_lapse"] == 12.0
