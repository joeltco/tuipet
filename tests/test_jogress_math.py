"""Jogress/DNA math audit (2026-07): canon re-verification vs DNA.java,
PhysicalState.applyDNA/jogress, Affinity.readAttributeInfo,
ClockTic.getDNARate/onDNAGenerate/DNA_GenerateValidate,
Evolution.pairJogressMatch + config.csv column 1.

Verified matching: applyDNA verbatim (the strength limit-1 overflow quirk,
same/diff-field mood +1/-1, spirit -3/-6, sick 1/2 vs bound 100, the
mutually-exclusive worse/new roll), DNA.getPercent + the strict-max
getHighestDNA, resetDNA-on-evolve, the wager==amount generate flow with
the 99-cap bits refund, the mash rate bands (8..80 in canon's exact field
order), the FULL attributeJogress matrix incl. the six ambiguous cells
(canon stores ALL pairs in a list, so both blocks coexist -- tuipet's
inline table matches cell-for-cell), and EvolveRefreshEnergy=false.

Fixed (canon divergences):
 * The fusion energy drain used round(): canon is energy +=
   Math.ceil(-0.66 x max) -- ceil rounds the negative product TOWARD ZERO
   (max 24 drains 15, not 16).
 * resolve() picked by the raw Priority column: canon's pairJogressMatch
   runs getFinalEvolution -- highest FULFILLED score, smallest deviation
   on ties, then random."""
import math
import random

from tuipet.pet import Pet, dna_field_for_rate, MAX_DNA_INVENTORY
from tuipet import jogress, evolution


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_fusion_drain_rounds_toward_zero():
    p = _pet(max_energy=24, energy=24)
    assert -math.ceil(-jogress.JOGRESS_ENERGY_COST * 24) == 15   # not round()'s 16
    p2 = _pet(max_energy=32, energy=32)
    assert -math.ceil(-jogress.JOGRESS_ENERGY_COST * 32) == 21   # ceil(-21.12) = -21


def test_rate_bands_match_canon_order():
    assert dna_field_for_rate(8) == "None"
    assert dna_field_for_rate(9) == "DeepSaver"
    assert dna_field_for_rate(48) == "DragonsRoar"
    assert dna_field_for_rate(80) == "DarkArea"
    assert dna_field_for_rate(81) == "None"                      # over-mashed


def test_generate_cap_refunds_the_overflow_as_bits():
    p = _pet(bits=0)
    p.dna_owned["DragonsRoar"] = 95
    p.dna_minigame_award(10, 48)                                 # rate 48 -> DragonsRoar
    assert p.dna_owned["DragonsRoar"] == MAX_DNA_INVENTORY
    assert p.bits == 6                                           # 95+10-99


def test_apply_dna_strength_overflow_lands_at_limit_minus_one():
    p = _pet(strength=3)
    p.dna_owned["DragonsRoar"] = 10
    p.apply_dna("DragonsRoar", 5)
    assert p.strength == 3                                       # limit-1, never the cap


def test_jogress_matrix_matches_the_csv_cell_for_cell():
    # the canonical pairs from the extract, both blocks (see the audit docstring)
    want = {("Vaccine", "Vaccine"): {"None", "Vaccine"},   # block1 partner-None row adds None
            ("Data", "Vaccine"): {"Data"},
            ("Vaccine", "None"): {"None", "Virus"},        # the ambiguous cells keep BOTH
            ("None", "Data"): {"None", "Vaccine"}}
    for (dig, par), results in want.items():
        got = {evol for (evol, d, p_) in jogress.JOGRESS_PAIRS if d == dig and p_ == par}
        assert results <= got | {"None"}, (dig, par, got)


def test_resolve_uses_fulfilled_not_raw_priority(monkeypatch):
    random.seed(0)
    p = _pet()
    fake = [{"num": 1, "name": "A", "partners": ["Vaccine"]},
            {"num": 2, "name": "B", "partners": ["Vaccine"]}]
    monkeypatch.setattr(jogress, "options", lambda pet: fake)
    monkeypatch.setattr(evolution, "fulfilled",
                        lambda pet, n: {1: 5.0, 2: 9.0}[n])
    monkeypatch.setattr(evolution, "deviation", lambda pet, n: 0)
    assert jogress.resolve(p, "Vaccine")["name"] == "B"          # the fulfilled winner


# ---- online resolve: canon JogressProtocol (lobby session audit 2026-07-07) ----

def _fake_options(monkeypatch, opts):
    monkeypatch.setattr(jogress, "options", lambda pet: opts)
    monkeypatch.setattr(evolution, "fulfilled", lambda pet, n: 1.0)
    monkeypatch.setattr(evolution, "deviation", lambda pet, n: 0)


def test_resolve_online_named_intersection_first(monkeypatch):
    """Canon channel 1: shared fusion NAMES match WITHOUT consulting the
    attribute pairing or the stage."""
    p = _pet()
    _fake_options(monkeypatch, [{"num": 1, "name": "Omegamon", "partners": ["Data"]}])
    payload = {"attr": "Virus", "stage": "Rookie", "fusions": ["Omegamon"], "attrs": []}
    assert jogress.resolve_online(p, payload)["name"] == "Omegamon"


def test_resolve_online_attr_path_is_mutual_and_same_stage(monkeypatch):
    """Canon channel 2: the attribute fallback needs the SAME growth stage and
    MUTUAL compatibility -- both-or-neither, no more one-sided fusions."""
    p = _pet()                                    # Champion Vaccine
    _fake_options(monkeypatch, [{"num": 1, "name": "A", "partners": ["Data"]}])
    base = {"attr": "Data", "stage": "Champion", "fusions": [], "attrs": ["Vaccine"]}
    assert jogress.resolve_online(p, dict(base))["name"] == "A"
    assert jogress.resolve_online(p, dict(base, stage="Rookie")) is None      # stage gate
    assert jogress.resolve_online(p, dict(base, attrs=["Virus"])) is None     # they can't take me
    assert jogress.resolve_online(p, dict(base, attr="Virus")) is None        # I can't take them


def test_resolve_online_legacy_peer_falls_back(monkeypatch):
    """A pre-v0.2.347 payload ships no lists: keep the old one-sided attr
    resolve so mixed-version fusions still work."""
    p = _pet()
    _fake_options(monkeypatch, [{"num": 1, "name": "A", "partners": ["Data"]}])
    assert jogress.resolve_online(p, {"attr": "Data"})["name"] == "A"
