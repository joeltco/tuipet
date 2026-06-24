"""The Futon care-effect lifecycle (careEffect.csv): apply, per-cadence rate gains,
end-on-sleep, expiry, and the care-call suppression flag.

Drives `_tick_effect` directly to isolate the effect engine from the rest of the
life-sim, plus one integration check through `use_item`.
"""
import pytest

from tuipet import data
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
    pet = Pet(num=-1, stage="Rookie")
    pet.mood = 0
    pet.effect_id, pet.effect_t = eid, float(eff["duration"])
    pet._eff_acc, pet._eff_asleep = 0.0, pet.asleep

    pet._tick_effect(60)
    assert pet.effect_t == eff["duration"] - 60, "duration should count down by dt"
    if eff["mood"][0] > 0:
        assert pet.mood > 0, "a positive mood rate should raise mood at the 60-tick cadence"


def test_effect_expires():
    eid, eff = _an_effect()
    pet = Pet(num=-1, stage="Rookie")
    pet.effect_id, pet.effect_t = eid, 5.0
    pet._eff_acc, pet._eff_asleep = 0.0, pet.asleep
    pet._tick_effect(10)                     # past the remaining 5s
    assert pet.effect_id == -1 and pet.effect_t == 0.0


def test_call_paused_reflects_data():
    eid, eff = _an_effect()
    pet = Pet(num=-1, stage="Rookie")
    pet.effect_id, pet.effect_t = eid, float(eff["duration"])
    assert pet.call_paused() == bool(eff["pause_call"])
    pet.effect_id = -1
    assert pet.call_paused() is False


def test_end_on_sleep_change():
    eid, eff = _an_effect()
    if not eff["end_on_sleep"]:
        pytest.skip("this effect does not end on sleep change")
    pet = Pet(num=-1, stage="Rookie")
    pet.asleep = False
    pet.effect_id, pet.effect_t = eid, float(eff["duration"])
    pet._eff_acc, pet._eff_asleep = 0.0, False
    pet.asleep = True                        # dozes off -> effect should end
    pet._tick_effect(0.1)
    assert pet.effect_id == -1


def test_effect_name():
    eid, eff = _an_effect()
    pet = Pet(num=-1, stage="Rookie")
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
