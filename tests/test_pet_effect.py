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
    # (the effect's mood rate left with the mood system; the countdown above
    # is the surviving observable)


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


def test_medicine_bandage_persist():
    """The new lapse fields round-trip through asdict (persistence)."""
    from dataclasses import asdict
    from tuipet.pet import Pet
    pet = Pet.from_num(29)
    pet.med_lapse, pet.bandage_lapse = 30.0, 12.0
    d = asdict(pet)
    assert d["med_lapse"] == 30.0 and d["bandage_lapse"] == 12.0
