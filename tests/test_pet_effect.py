"""What remains of the care-effect suite after the strict-DSprite item cut
(2026-07-17): the Futon careEffect runtime is GONE -- these pins prove the
cut is total, plus the frozen dead-field save contract.
"""
from dataclasses import asdict

from tuipet.pet import Pet


def test_the_care_effect_runtime_is_gone():
    """Strict-DSprite items (2026-07-17): no effect fields, no effect tick,
    no careEffect loader -- the Futon's whole machine left together."""
    p = Pet.from_num(29)
    assert not hasattr(p, "effect_id")
    assert not hasattr(p, "effect_t")
    assert not hasattr(p, "_tick_effect")
    assert not hasattr(p, "_effect_energy_gain")
    assert not hasattr(p, "call_paused")
    from tuipet import data
    assert not hasattr(data, "load_care_effects")


def test_the_staples_never_reach_a_fresh_bag():
    """DSprite's catalog has no furniture: a fresh device starts with an
    empty bag, and the shelf carries no DVPet i:*/f:* keys."""
    p = Pet.new_egg(generation=1, egg_type=0)
    assert p.inventory == {}
    from tuipet import shop
    assert not any(e["key"].startswith(("i:", "f:")) for e in shop.catalog())


def test_old_saves_shed_the_staples_on_load():
    """A stocked bag from a pre-cut save (Toilet 100/Bandage 99/Futon 100)
    loses exactly the dead furniture keys -- everything else survives."""
    from tuipet import persistence
    p = Pet.from_num(29)
    p.inventory = {"i:80": 99, "i:81": 100, "i:82": 100, "i:83": 3,
                   "energy_drink": 2}
    d = asdict(p)
    loaded, _ = persistence.pet_from_save(d, catch_up=False)
    assert loaded is not None
    assert loaded.inventory == {"energy_drink": 2}


def test_medicine_bandage_persist():
    """(med_lapse left with the sickness system, 2026-07-17; bandage_lapse
    outlived injuries as a plain lapse field -- pin the round trip)"""
    pet = Pet.from_num(29)
    pet.bandage_lapse = 12.0
    d = asdict(pet)
    assert d["bandage_lapse"] == 12.0
