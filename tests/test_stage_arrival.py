"""Evolution.java's per-stage ARRIVAL setters (egg/hatch audit 2026-07-06):
fresh()/inTraining()/rookie() SET the newcomer's state on top of digivolve --
the missing fresh() obedience 75 was the deepest root of the misbehaving-
babies era (canon babies are born TRUSTING; the 0 was pre-hatch defaultData)."""
from tuipet.pet import (Pet, FRESH_MOOD, FRESH_OBEDIENCE, IN_TRAINING_OBEDIENCE, IN_TRAINING_SLEEP_LAPSE,
                        ROOKIE_OBED_GOOD, ROOKIE_OBED_DEFAULT, ROOKIE_OBED_BAD)


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
    assert p.obedience == FRESH_OBEDIENCE == 75    # born trusting
    # (the grumpy birth mood left with the mood system)
    assert p.hunger == 0 and p.strength == 0       # born hungry, no effort yet
    assert p.energy == p.max_energy                # full of beans
    assert (p.nutr_protein, p.nutr_mineral, p.nutr_vitamin) == (6, 6, 6)


def test_intraining_arrival_is_the_toddler_rebellion():
    p = Pet(num=2, stage="Fresh", attribute="Vaccine")
    p.world_seconds = 10 * 60.0
    p.obedience = 75
    p.asleep, p.lights = True, False
    p.evolve_to(12)                                # any InTraining form
    assert p.stage == "InTraining"
    assert p.obedience == IN_TRAINING_OBEDIENCE == 50   # knocked back down
    assert not p.asleep and p.lights                    # wakes, lights on
    assert p.sleep_lapse == IN_TRAINING_SLEEP_LAPSE == 360
    q = Pet(num=2, stage="Fresh", attribute="Vaccine")
    q.world_seconds = 10 * 60.0
    q.obedience = 10
    q.evolve_to(12)
    assert q.obedience == 10                       # only re-set when ABOVE the cap


def test_rookie_arrival_grades_the_childhood():
    for moods, want in ((dict(Happy=5, Neutral=1), ROOKIE_OBED_GOOD),
                        (dict(Neutral=5, Happy=1), ROOKIE_OBED_DEFAULT),
                        (dict(Unhappy=5), ROOKIE_OBED_BAD),
                        (dict(Happy=3, Neutral=3), ROOKIE_OBED_BAD)):   # a TIE is Mood.None -> bad
        p = Pet(num=12, stage="InTraining", attribute="Vaccine")
        p.world_seconds = 10 * 60.0
        p.obedience = 99
        for k, v in moods.items():
            p.daily_mood[k] = v
        p.evolve_to(25)                            # any Rookie form
        assert p.obedience == want, (moods, p.obedience)
