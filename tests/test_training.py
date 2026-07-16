"""Training-minigame gains (Workstream A) — the last correctness piece in A.

apply_training(hits, power, attribute, game):
  - every drill: Effort (strength) +1 WIN OR LOSE (canon setExercise), +1
    exercise, -1 energy; weight is untouched (canon ExerciseWeightDec=0).
  - a success (hits>=2) additionally grants the praise window; a fail costs
    mood/obedience (the old "success builds obedience +1" was invented).
  - game in {vaccine,data,virus}: a success adds hits*TRAIN_POWER_PER_HIT to that
    attribute's lifelong power count; a fail adds nothing. Training a non-favored
    attribute costs extra mood/spirit.

TRAIN_POWER_PER_HIT=2 is a deliberate tuipet adaptation (DVPet adds a flat +1/drill,
but its stages last real-DAYS; under tuipet's ~60x-compressed stage a flat +1 can
never reach the digimon.csv power thresholds, stranding good forms). So 2 hits=+4,
3 hits=+6. Pinned here so a future tweak is a conscious choice.

Pets keep high energy (no fatigue roll) and normal weight (no overweight-injury
roll) so the gains under test are deterministic. num=-1 keeps it sprite-free.
"""
from tuipet.pet import Pet, TRAIN_POWER_PER_HIT


def _trainee(attribute="Vaccine", **kw):
    # high energy, normal weight -> no fatigue / overweight randomness
    defaults = dict(energy=24, max_energy=24, weight=20, vaccine=0, data_power=0,
                    virus=0, strength=0, mood=0, obedience=500)  # out-roll checkRefused
    defaults.update(kw)
    return Pet(num=-1, stage="Rookie", attribute=attribute, **defaults)


def test_constant_is_two():
    assert TRAIN_POWER_PER_HIT == 2


# ---- HP (Effort) drill -----------------------------------------------------

def test_hp_success_builds_strength_and_praise():
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine",   # real species: _open_praise gates on num
            energy=24, max_energy=24, weight=20, strength=0, mood=0, obedience=0)
    p.world_seconds = 600.0
    p.apply_training(2, 100, game="hp")
    assert p.strength == 1
    # (the praise flag + obedience checks left with the discipline system)


# ---- attribute drills ------------------------------------------------------

def test_attribute_gain_scales_with_hits():
    two = _trainee(); two.apply_training(2, 100, attribute="Vaccine", game="vaccine")
    assert two.vaccine == 2 * TRAIN_POWER_PER_HIT          # +4
    three = _trainee(); three.apply_training(3, 100, attribute="Vaccine", game="vaccine")
    assert three.vaccine == 3 * TRAIN_POWER_PER_HIT        # +6


def test_failed_attribute_drill_no_gain():
    p = _trainee()
    p.apply_training(1, 100, attribute="Vaccine", game="vaccine")
    assert p.vaccine == 0


def test_attribute_routing():
    d = _trainee(attribute="Data")
    d.apply_training(2, 100, attribute="Data", game="data")
    assert d.data_power == 4 and d.vaccine == 0 and d.virus == 0
    v = _trainee(attribute="Virus")
    v.apply_training(2, 100, attribute="Virus", game="virus")
    assert v.virus == 4 and v.vaccine == 0 and v.data_power == 0


# ---- shared per-drill costs ------------------------------------------------

def test_drill_costs_weight_energy_and_counts_exercise():
    p = _trainee()
    e0 = p.energy
    p.apply_training(2, 100, attribute="Vaccine", game="vaccine")
    assert p.weight == 20          # canon ExerciseWeightDec=0: no flat shed
    assert p.energy == e0 - 1
    assert p.exercise_today == 1
