"""LINES_SPEC arc 5 — invariants over EVERY curated line, and the hatch
canonicalization that retires the fuzzy engine for new pets.

These are the safety net for tool-generated data: each invariant holds for all
47 lines or the curator is broken."""
import pytest

from tuipet import data, egg, lines
from tuipet.pet import Pet

STAGES = ["Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"]

# edges ver1 declares beyond the corpus graph (LINES_SPEC §3, by design;
# the Betamon road joined 2026-07-07 -- DM20 canon, humulos chart)
DECLARED_EDGES = {(29, 102), (29, 95), (102, 220),
                  (1455, 37), (37, 102), (37, 95), (37, 90), (90, 220)}


def _all_lines():
    return lines.load_lines()


def test_every_member_is_a_real_form_at_its_stage():
    _, by_num = data.load_sprites()
    for lid, line in _all_lines().items():
        for num, row in line["members"].items():
            assert num in by_num, (lid, num)
            assert not data.is_placeholder(num), (lid, num)
            assert by_num[num]["stage"] == row["stage"], (lid, num)


def test_every_edge_is_real_or_declared():
    evo = data.load_evolutions()
    for lid, line in _all_lines().items():
        for num, row in line["members"].items():
            for p in row["parents"]:
                assert num in evo.get(p, []) or (p, num) in DECLARED_EDGES, \
                    (lid, p, num)


def test_every_line_has_one_root_and_monotonic_stages():
    for lid, line in _all_lines().items():
        assert line["root"] is not None, lid
        roots = [r["num"] for r in line["members"].values() if not r["parents"]]
        assert roots == [line["root"]], lid    # exactly one parentless row: the root
        for num, row in line["members"].items():
            si = STAGES.index(row["stage"])
            for p in row["parents"]:
                assert STAGES.index(line["members"][p]["stage"]) == si - 1, \
                    (lid, p, num)              # parents are exactly one stage down


class _C:
    def __init__(self, num, lid, cm=0, tr=0, of=0):
        self.num, self.line_id = num, lid
        self.care_mistakes, self.stage_trainings, self.overeat = cm, tr, of
        self.stage_battles, self.battle_log, self.mega_kills = 0, [], 0
        self.vaccine = self.data_power = self.virus = 0
        self.full_health = 5


def test_growth_stages_always_have_a_road():
    """At Fresh/InTraining/Rookie every counter state must land on SOME child —
    a young pet never dead-ends. (Champion+ gates like WIN/KO6/AREA are
    intentional waits, exempt.)"""
    for lid, line in _all_lines().items():
        for num, row in line["members"].items():
            if row["stage"] not in ("Fresh", "InTraining", "Rookie"):
                continue
            if num not in line["children"]:
                continue
            for cm in (0, 3):
                for tr in (0, 16):
                    for of in (0, 3):
                        got = lines.select_line(_C(num, lid, cm, tr, of))
                        assert got is not None, (lid, num, cm, tr, of)


def test_every_line_reaches_mega():
    for lid, line in _all_lines().items():
        assert any(r["stage"] == "Mega" for r in line["members"].values()), lid


def test_every_egg_hatch_canonicalizes_to_a_line():
    for i in range(egg.count()):
        for t in egg.hatch_targets(i):
            root, lid = lines.canonical_root(t)
            assert lid, (i, t)                 # no egg produces a corpus pet anymore
            assert lines.load_lines()[lid]["root"] == root


def test_hatching_any_egg_binds_its_line():
    import random
    for idx in (0, 2, 7, 27, 34, 46, 47):      # named + achievement + mystery eggs
        random.seed(idx)
        p = Pet.new_egg(egg_type=idx)
        p._hatch_into_fresh()
        assert p.line_id and lines.active(p), idx
        assert p.num == lines.load_lines()[p.line_id]["root"]


def test_hand_curated_lines_survived_the_curator():
    L = _all_lines()
    assert [r["num"] for r in L["ver1"]["children"][29]] == [93, 102, 95, 124, 116]
    assert len(L["verX"]["members"]) == 15


def test_canon_hints_landed():
    _, by_num = data.load_sprites()
    def names(lid):
        return {by_num[n]["name"] for n in _all_lines()[lid]["members"]}
    assert {"Gabumon", "Elecmon", "Garurumon"} <= names("ver2")
    assert {"Nyaromon", "Salamon", "Meicoomon", "Meicrackmon", "Rasielmon"} <= names("verE")
    assert {"Zubamon", "Hackmon", "Zubaeagermon", "BaoHackmon"} <= names("sakumon")
    assert {"Dracomon", "Coredramon"} <= names("petitmon")


def test_licenses_priced_by_ceiling():
    rules = data.load_egg_unlock()
    for r in rules.values():
        assert r["price"] != 2000, r["name"]   # the flat legacy tier is gone
