"""Toilet training — DVPet doPoop's SelfToilet branch, poopToilet, item uses.

Canon (config col 0): ONE toilet use while InTraining trains it; from Rookie on
(obedience >= 50) the pet takes ITSELF to a stocked toilet at poop time -- no
filth ever.  Items carry USES (quantity IS uses): a Toilet purchase = 100
flushes (UsesPerItem), a Port. Potty = 1; the device starts with 100
(StartingUses -> tuipet: generation 1 only).  poop(true) keeps the relief mood
+ weight shed, skips the pile.  Audit 2026-07-05."""
import random

from tuipet.pet import (Pet, MIN_TOILET_USES_TO_TRAIN, TOILET_TRAINED_OBED_MIN,
                        STAGE_CAN_AUTO_TOILET, TOILET_URGENT_FRAC)
from tuipet import persistence


def _pet(stage="Champion", **kw):
    p = Pet(num=102, name="D", stage=stage, attribute="Virus", obedience=500)
    p.world_seconds = 12 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_config_parity():
    assert MIN_TOILET_USES_TO_TRAIN == 1 and TOILET_TRAINED_OBED_MIN == 50
    assert STAGE_CAN_AUTO_TOILET == ("Rookie", "Champion", "Ultimate", "Mega")
    assert TOILET_URGENT_FRAC == 0.8


def test_trained_pet_self_toilets_no_filth_and_spends_a_flush():
    q = _pet(toilet_trained=1)
    q.inventory["i:82"] = 2
    m0 = q.mood
    q._poop_t = q._poop_interval + 0.5
    q._tick_body(1.0)
    assert q.poop == 0 and q.inventory["i:82"] == 1        # in the bowl, one flush
    assert getattr(q, "_toilet_event", None) == "i:82"     # the app plays poopToilet
    # (the relief mood left with the mood system)
    q._toilet_event = None
    q.inventory.pop("i:82")                                # bowl empty ->
    q._poop_t = q._poop_interval + 0.5
    q._tick_body(1.0)
    assert q.poop == 1                                     # ...back to the floor


def test_training_and_obedience_both_gate_the_self_visit():
    untrained = _pet()                                     # trained=0
    untrained.inventory["i:82"] = 5
    untrained._poop_t = untrained._poop_interval + 0.5
    untrained._tick_body(1.0)
    assert untrained.poop == 1 and untrained.inventory["i:82"] == 5
    disobedient = _pet(toilet_trained=1, obedience=10)     # below the 50 bar
    disobedient.inventory["i:82"] = 5
    disobedient._poop_t = disobedient._poop_interval + 0.5
    disobedient._tick_body(1.0)
    assert disobedient.poop == 1


def test_first_generation_starts_with_a_stocked_toilet():
    p1 = Pet.new_egg(egg_type=1)                           # canon StartingUses=100
    assert p1.inventory.get("i:82") == 100
    p2 = Pet.new_egg(generation=2, egg_type=1)
    assert "i:82" not in p2.inventory                      # once per save, not per gen


def test_toilet_trained_survives_the_save_round_trip():
    import json
    p = _pet(toilet_trained=1)
    d = json.loads(json.dumps(persistence.to_save_dict(p)))
    back, _ = persistence.pet_from_save(d, catch_up=False)
    assert back.toilet_trained == 1
