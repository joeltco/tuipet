"""Evolution/battle math audit (2026-07): canon re-verification vs the decompile.

Verified matching (no code change): calcAttackPower signs, checkStatTotal,
BaseAttack/MaxHealth tables, initiative speed formula + tie coin-flip,
checkFinish, all fulfilled() R-rates vs config rows 534-565, calcDeviation
gate-for-gate (incl. the raw-vs-fraction quirk), the prob roll shape, the
zero-affinity matrices claim.

Fixed (canon divergences):
 * getDNA() is CONSUME-ONCE -- a met DNA charge forgives exactly ONE failed
   gate, not all of them (tuipet's bypass was far stronger than the device).
 * JogressOptional=TRUE (classic): Jogress forms ARE reachable by normal timed
   care; Failed forms compete normally; Fusion stays handshake-only;
   Mode/Death/Xros keep their own triggers.
 * Only an INDUCED X requirement demands the antibody -- 180 Natural-marked
   corpus forms were wrongly locked; and digivolving INTO a Natural/Induced
   form now grants the Permanent X state (Evolution.digivolve).
 * The antibody no longer skips the probability roll (not canon)."""
import random

import pytest

from tuipet.pet import Pet
from tuipet import evolution


def _req(**over):
    """A fully-open requirement template; tests constrain specific gates."""
    none = ("None", 0)
    base = {
        "battles": none, "disturb": none, "overeat": none, "sick": none,
        "injured": none, "obedience": none, "wins": none, "mistakes": none,
        "incarnations": none, "level_fought": none, "level_fought_min": 0,
        "data": [none, none], "vaccine": [none, none], "virus": [none, none],
        "time": "None", "weight": "None", "mood": "None", "major_food": "None",
        "temp_req": None, "habitat_req": -1, "dna": {},
        "evol_item": -1, "special": "None", "xantibody": "None",
        "prob": 100, "probBound": 100, "priority": 0.0,
    }
    base.update(over)
    return base


DNA_MET = {"DragonsRoar": ("GreaterThan", -1)}     # any charge percentage passes


@pytest.fixture()
def pet():
    p = Pet(num=900001, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p.vaccine, p.data_power, p.virus = 50, 30, 20
    return p


def _install(monkeypatch, reqs):
    table = dict(reqs)
    monkeypatch.setattr(evolution.data, "load_requirements", lambda: table)


def test_dna_no_longer_forgives_failed_gates(monkeypatch, pet):
    """The gate-forgiveness (canon getDNA()'s consume-once excuse) left with
    the DNA slim (BASIC VPET 2026-07-16): a failed care gate is a failed
    gate, charge or no charge -- the charge still bends selection via the
    fulfilled-score bonus and arms divergence."""
    one = _req(battles=("GreaterThan", 5), dna=DNA_MET)
    zero = _req(dna=DNA_MET)
    _install(monkeypatch, {2: one, 3: zero, pet.num: _req()})
    assert evolution.check(pet, 2) is False       # no forgiveness
    assert evolution.check(pet, 3) is True        # nothing to forgive


def test_special_types_follow_the_optional_flags(monkeypatch, pet):
    _install(monkeypatch, {1: _req(special="Jogress"), 2: _req(special="Fusion"),
                           3: _req(special="Mode"), 4: _req(special="Death"),
                           5: _req(special="Failed"), pet.num: _req()})
    assert evolution.check(pet, 1) is True        # JogressOptional=TRUE (classic)
    assert evolution.check(pet, 2) is False       # FusionOptional=FALSE: handshake only
    assert evolution.check(pet, 3) is False       # tModeChange only
    assert evolution.check(pet, 4) is False       # dying only
    assert evolution.check(pet, 5) is True        # Failed forms compete normally
    for n in (1, 2, 3, 4, 5):
        assert evolution.check(pet, n, connecting=True) is True   # the waive idiom holds


def test_only_induced_x_forms_need_the_antibody(monkeypatch, pet):
    _install(monkeypatch, {1: _req(xantibody="Natural"), 2: _req(xantibody="Induced"),
                           pet.num: _req()})
    assert pet.x_antibody == "None"
    assert evolution.check(pet, 1) is True        # Natural: care alone reaches it
    assert evolution.check(pet, 2) is False       # Induced: the antibody is the key
    pet.x_antibody = "Temporary"
    assert evolution.check(pet, 2) is True


def test_the_antibody_no_longer_skips_the_probability_roll(monkeypatch, pet):
    random.seed(0)
    _install(monkeypatch, {1: _req(xantibody="Induced", prob=0, probBound=10**9),
                           pet.num: _req()})
    pet.x_antibody = "Permanent"
    hits = sum(evolution.check(pet, 1) for _ in range(50))
    assert hits == 0                              # prob 0 loses the roll, antibody or not


def test_becoming_an_x_form_makes_the_state_permanent():
    from tuipet import data
    natural = next((n for n, r in data.load_requirements().items()
                    if r.get("xantibody") in ("Natural", "Induced")
                    and not data.is_placeholder(n)), None)
    assert natural is not None
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    assert p.x_antibody == "None"
    p.evolve_to(natural)
    assert p.x_antibody == "Permanent"            # Evolution.digivolve's grant


def test_stat_total_is_never_dna_bypassed(monkeypatch, pet):
    starving = _req(vaccine=[("GreaterThan", 500), ("None", 0)], dna=DNA_MET)
    _install(monkeypatch, {1: starving, pet.num: _req()})
    assert evolution.check(pet, 1) is False       # checkStatTotal stands alone


def test_prob_roll_matches_canon_shape(monkeypatch, pet):
    random.seed(3)
    _install(monkeypatch, {1: _req(prob=50, probBound=100), pet.num: _req()})
    hits = sum(evolution.check(pet, 1) for _ in range(4000))
    # canon: prob > nextInt(bound) -> P(win) = prob/bound = 0.5 (pet has no boost)
    assert abs(hits / 4000 - 0.5) < 0.04
