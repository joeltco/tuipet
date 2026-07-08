"""DNA charge mechanics (pet.apply_dna).

The strength clamp folds DVPet's setExercise(limit-1) onto tuipet's four-heart
gauge: charging DNA nudges Effort UP toward a ceiling of limit-1 (=3, "DNA
can't top you off"), but it is a CEILING, never a penalty -- a pet already
trained to full 4 keeps its heart (DNA audit 2026-07-08).
"""
from tuipet import data
from tuipet.pet import Pet


def _pet():
    p = Pet(num=-1, stage="Rookie")
    p.field = data.DNA_FIELDS[0]
    p.dna_owned = {f: 10 for f in data.DNA_FIELDS}
    p.dna_applied = {f: 0 for f in data.DNA_FIELDS}
    return p


def test_charge_never_drops_a_maxed_pet():
    p = _pet()
    p.strength = 4                                   # trained to full
    assert p.apply_dna(p.field, 1)
    assert p.strength == 4, "DNA charge must not knock a heart off a maxed pet"


def test_charge_ceils_at_limit_minus_one():
    # from below the ceiling DNA raises you, but only up to 3 -- never to 4
    for start, expected in ((0, 1), (1, 2), (2, 3), (3, 3)):
        p = _pet()
        p.strength = start
        assert p.apply_dna(p.field, 1)
        assert p.strength == expected, (start, p.strength)


def test_bulk_charge_still_ceils_at_three():
    p = _pet()
    p.strength = 0
    assert p.apply_dna(p.field, 5)                   # gain 5, but ceiling holds
    assert p.strength == 3
