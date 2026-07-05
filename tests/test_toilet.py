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


def test_manual_use_trains_only_at_intraining_and_needs_the_urge():
    random.seed(4)
    p = _pet(stage="InTraining", obedience=200)
    p.inventory["i:82"] = 3
    assert "doesn't need to go" in p.use_item("i:82")     # gauge low: refused
    assert p.inventory["i:82"] == 3                        # ...and refunded
    p._poop_t = 0.9 * p._poop_interval
    msg = p.use_item("i:82")
    assert "no mess" in msg
    assert p.toilet_trained == 1 and p.inventory["i:82"] == 2
    assert p._poop_t == 0.0 and p.poop == 0                # emptied into the bowl
    adult = _pet()                                         # a Champion learns nothing
    adult.inventory["i:82"] = 1
    adult._poop_t = 0.9 * adult._poop_interval
    adult.use_item("i:82")
    assert adult.toilet_trained == 0


def test_trained_pet_self_toilets_no_filth_and_spends_a_flush():
    q = _pet(toilet_trained=1)
    q.inventory["i:82"] = 2
    m0 = q.mood
    q._poop_t = q._poop_interval + 0.5
    q._tick_body(1.0)
    assert q.poop == 0 and q.inventory["i:82"] == 1        # in the bowl, one flush
    assert getattr(q, "_toilet_event", None) == "i:82"     # the app plays poopToilet
    assert q.mood > m0                                     # relief + the item's blessing
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


def test_potty_is_the_fallback_and_buying_adds_uses_per():
    q = _pet(toilet_trained=1)
    q.inventory["i:83"] = 1                                # only the Port. Potty
    q._poop_t = q._poop_interval + 0.5
    q._tick_body(1.0)
    assert q.poop == 0 and "i:83" not in q.inventory       # its single use spent
    # a Toilet purchase = 100 flushes (UsesPerItem), clamped at MaxUses
    from tuipet import data
    e = data.consumable_by_key("i:82")
    assert e["uses_per"] == 100 and e["max_uses"] == 199
    q.bits = 10000
    slot = {"key": "i:82", "stock": 1, "sale": False}
    from tuipet import shop
    q.inventory["i:82"] = 150
    q.buy_slot(slot)
    assert q.inventory["i:82"] == 199                      # clamped, not 250


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
