"""LINES_SPEC arc 5 — invariants over EVERY curated line, and the hatch
canonicalization that retires the fuzzy engine for new pets.

These are the safety net for tool-generated data: each invariant holds for all
47 lines or the curator is broken."""
import pytest

from tuipet import data, egg, lines
from tuipet.pet import Pet

STAGES = ["Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"]

# edges the DEVICE lines declare beyond the corpus graph (LINES_SPEC §3, by
# design; ver1's Betamon road + the ver2-verE canon rewrite, 2026-07-07 --
# every device line now matches its humulos DM20 chart)
DECLARED_EDGES = {
    (29, 95), (29, 102), (31, 87), (31, 91), (33, 94), (33, 115),
    (34, 101), (34, 136), (34, 140), (35, 94), (35, 114), (35, 148),
    (37, 90), (37, 95), (37, 102), (43, 101), (43, 109), (43, 136),
    (44, 88), (44, 104), (45, 91), (45, 106), (46, 104), (46, 125),
    (90, 220), (97, 195), (98, 191), (101, 195), (102, 220), (104, 210),
    (108, 213), (125, 210), (1455, 37), (1457, 35),
}


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
    # sakumon carries the canon Zuba/Hack uppers (humulos; canon scan 2026-07-08)
    assert [r["num"] for r in L["sakumon"]["children"][161]] == [369]   # Duramon
    assert [r["num"] for r in L["sakumon"]["children"][160]] == [371]   # SaviorHackmon
    assert [r["num"] for r in L["sakumon"]["children"][369]] == [370]   # Durandamon
    assert [r["num"] for r in L["sakumon"]["children"][371]] == [372]   # Jesmon
    # verE keeps its canon battle gate to Meicrackmon
    assert L["verE"]["members"][389]["rule_text"] == "WIN 12/15"


# ---- first-match semantics invariants (canon scan 2026-07-08) ---------------
# The 07-07 sweep verified the GRAPH and missed that first-match ORDER had
# 137 forms shadowed dead (a shared TIME catch-all sorted before the second
# rookie's rows).  These two invariants close that class for good.

def _care_only(rule):
    """Strip battle-ish atoms; None if any alternative is battle-gated."""
    return [[a for a in alt if a[0] not in ("win", "btl", "lv", "ko6", "area")]
            for alt in rule]


def _has_battle(rule):
    return any(a[0] in ("win", "btl", "lv", "ko6", "area")
               for alt in rule for a in alt)


def _matches_care(rule, cm, tr, of):
    vals = {"cm": cm, "tr": tr, "of": of}
    for alt in rule:
        if all(vals[k] >= a and (b is None or vals[k] <= b) for k, a, b in alt):
            return True
    return False


_CARE_SPACE = [(cm, tr, of)
               for cm in (0, 1, 2, 3, 4, 6, 20)
               for tr in (0, 4, 5, 7, 8, 15, 16, 17, 40)
               for of in (0, 1, 2, 3, 9)]


def _live_children(line, parent):
    """Child nums actually winnable under first-match order: a row is dead if
    every care state it could fire on hits an earlier care-only row first
    (battle atoms are satisfiable, but can't beat an earlier care-only match)."""
    rows = line["children"].get(parent, [])
    out = []
    for i, row in enumerate(rows):
        earlier = [r["rule"] for r in rows[:i] if not _has_battle(r["rule"])]
        if any(not alt for rule in earlier for alt in rule):     # earlier TIME row
            continue
        if earlier:
            mine = _care_only(row["rule"])
            reach = [s for s in _CARE_SPACE if _matches_care(mine, *s)]
            if reach and all(any(_matches_care(r, *s) for r in earlier)
                             for s in reach):
                continue
        out.append(row["num"])
    return out


def test_first_match_order_reaches_every_member():
    """Every line member must be winnable through the ordered rule tables —
    a row that exists but can never fire is curated content no player sees."""
    for lid, line in _all_lines().items():
        seen, frontier = {line["root"]}, [line["root"]]
        while frontier:
            cur = frontier.pop()
            for t in _live_children(line, cur):
                if t not in seen:
                    seen.add(t)
                    frontier.append(t)
        shadowed = set(line["members"]) - seen
        assert not shadowed, (lid, sorted(shadowed))


def test_dead_ends_are_annotated():
    """A member below its line's ceiling with no evolution rows must say so in
    its Notes (canon dead ends like Monzaemon, or a graph-forced leaf) — a
    silent dead end is a stranding bug, not a design choice."""
    import csv
    import os
    notes = {}
    path = os.path.join(os.path.dirname(lines.__file__), "data", "lines.csv")
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            notes.setdefault((r["LineID"], int(r["DexNum"])), []).append(r["Notes"])
    for lid, line in _all_lines().items():
        ceiling = max(STAGES.index(r["stage"]) for r in line["members"].values())
        for num, row in line["members"].items():
            if STAGES.index(row["stage"]) >= ceiling or line["children"].get(num):
                continue
            note = " ".join(notes.get((lid, num), []))
            assert "dead end" in note or "punishment leaf" in note, (lid, num, note)


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
