"""Evolution.java's per-stage ARRIVAL setters (egg/hatch audit 2026-07-06):
fresh()/inTraining()/rookie() SET the newcomer's state on top of digivolve --
the missing fresh() obedience 75 was the deepest root of the misbehaving-
babies era (canon babies are born TRUSTING; the 0 was pre-hatch defaultData)."""
from tuipet.pet import (Pet, IN_TRAINING_SLEEP_LAPSE)


def _egg():
    p = Pet.new_egg(egg_type=0)
    p.world_seconds = 10 * 60.0
    return p


def test_a_hatchling_is_born_trusting_grumpy_and_hungry():
    p = _egg()
    p.hatching = True
    p._hatch_t = 0.0
    assert p.advance_hatch(0.1)                    # the egg hatches
    assert p.stage == "Fresh"
    # (the trusting-birth obedience left with the discipline system)
    # (the grumpy birth mood left with the mood system)
    assert p.hunger == 0 and p.strength == 0       # born hungry, no effort yet
    assert p.energy == p.max_energy                # full of beans


def test_intraining_arrival_is_the_toddler_rebellion():
    p = Pet(num=2, stage="Fresh", attribute="Vaccine")
    p.world_seconds = 10 * 60.0
    p.asleep, p.lights = True, False
    p.evolve_to(12)                                # any InTraining form
    assert p.stage == "InTraining"
    # (the obedience knock-back left with the discipline system)
    assert not p.asleep and p.lights                    # wakes, lights on
    assert p.sleep_lapse == IN_TRAINING_SLEEP_LAPSE == 360


