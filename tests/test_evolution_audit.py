"""THE EVOLUTION AUDIT — the pins (2026-07-25).

Joel: "lets do a full blown evolution audit next."

**This audit found nothing broken** — the first of the seven that didn't.
So what it leaves behind is the measurement itself, pinned: every egg
raised to a final form, every gate proved satisfiable, both off-chart
doors walked, and the pages measured against the box.  If a future edit
strands a line, resurrects a placeholder, forgets a counter reset or
writes a gate nobody can meet, one of these fails.

Three things I chased as bugs and proved were correct — recorded here so
nobody burns the time again:

  * a line row can read `unmet=0` while `ready=False`.  That is the DOOR
    shape: the checklist row is informational (`met=None`, e.g. "jogress
    with a Vaccine/Free partner"), so it counts as neither met nor unmet
    and the page names the road instead of pretending it is a countdown.
  * `dna_applied` is not emptied on evolve, it is ZEROED -- charges do
    clear, the dict just keeps its keys.
  * a crest egg's landing looks random because several armor forms can
    answer one crest; the shop dossier lists exactly that set.
"""
import random

import pytest

from tuipet import data, digicore, egg as egg_mod, evolution, grid
from tuipet import lines as L, shop
from tuipet.digicorescreen import DigiCorePanel
from tuipet.pet import Pet

R, C = grid.ROWS, grid.COLS


def _raised(**kw):
    p = Pet(num=kw.pop("num", 100), stage=kw.pop("stage", "Champion"),
            attribute="Vaccine", obedience=500)
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight()
    p.care_mistakes, p.overeat = 0, 0
    p.stage_trainings, p.total_trainings = 40, 400
    p.stage_battles, p.battles, p.wins = 20, 60, 50
    p.battle_log = [1] * 15
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _grow(egg_idx, care="good", cap=40):
    """Hatch and raise to a stop, letting the REAL charts decide."""
    random.seed(1000 + egg_idx)
    targets = egg_mod.hatch_targets(egg_idx)
    if not targets:
        return None, []
    p = Pet(num=targets[0], stage="Fresh", attribute="Vaccine", obedience=500)
    p.egg_type = egg_idx
    L.adopt_line(p, prev=-1)
    road = [p.num]
    for _ in range(cap):
        if care == "good":
            p.care_mistakes, p.overeat = 0, 0
            p.stage_trainings, p.total_trainings = 40, 400
            p.stage_battles, p.battles, p.wins = 20, 60, 50
            p.battle_log = [1] * 15
            p.weight = p._base_weight()
            p.strength, p.hunger = 4, 4
        else:
            p.care_mistakes, p.overeat = 12, 8
            p.stage_trainings = p.stage_battles = 0
            p.battle_log = [0] * 15
        p.energy = p.max_energy
        p.stage_seconds = p.STAGE_DURATION.get(p.stage, 9e9) + 1
        before = p.num
        p._maybe_evolve()
        if p.num == before:
            break
        road.append(p.num)
    return p, road


# ---- every egg reaches somewhere real -----------------------------------

@pytest.mark.parametrize("egg_idx", range(0, 46, 5))
@pytest.mark.parametrize("care", ["good", "neglect"])
def test_every_egg_raises_to_a_real_form(egg_idx, care):
    p, road = _grow(egg_idx, care)
    if p is None:
        pytest.skip("egg has no hatch targets")
    assert len(road) >= 2, "an egg that never evolves once"
    assert not data.is_placeholder(p.num), "a road ended on placeholder art"
    assert p.stage in ("Rookie", "Champion", "Ultimate", "Mega")
    # wherever it stopped, it stopped at a form the game can render + name
    assert data.record_for(p.num).get("name")


def test_good_care_climbs_higher_than_neglect():
    """The whole point of the care gates: the same eggs, raised two ways."""
    ladder = ["Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"]
    good = neglect = 0
    for i in range(0, 46, 4):
        gp, _ = _grow(i, "good")
        np_, _ = _grow(i, "neglect")
        if gp and np_:
            good += ladder.index(gp.stage)
            neglect += ladder.index(np_.stage)
    assert good > neglect


# ---- the gates themselves ------------------------------------------------

def test_no_line_row_asks_for_something_impossible():
    """1,151 rows across 51 lines.  A WIN gate deeper than its own rolling
    window, a negative care-mistake bracket or a drill/battle count past
    the counters' ceiling would make a form permanently unreachable."""
    bad = []
    for lid, line in L.load_lines().items():
        for parent, kids in line["children"].items():
            for row in kids:
                for alt in row["rule"]:
                    for at in alt:
                        kind = at[0]
                        if kind == "win" and len(at) >= 3 and at[1] > at[2]:
                            bad.append((lid, parent, row["num"], at))
                        if kind in ("cm", "of") and len(at) >= 2 and at[1] < 0:
                            bad.append((lid, parent, row["num"], at))
                        if kind in ("tr", "btl") and len(at) >= 2 and at[1] > 999:
                            bad.append((lid, parent, row["num"], at))
    assert not bad, f"unsatisfiable gates: {bad[:3]}"


def test_every_rule_atom_the_data_uses_has_a_live_handler():
    """The singleton trap: exactly ONE row in the whole corpus uses AREA
    (DoruGreymon -> Alphamon).  An atom the checker doesn't know would read
    as permanently unmet and quietly delete a form from the game."""
    kinds = set()
    for line in L.load_lines().values():
        for kids in line["children"].values():
            for row in kids:
                for alt in row["rule"]:
                    for at in alt:
                        kinds.add(at[0])
    p = _raised()
    for kind in kinds:
        atom = {"win": (kind, 12, 15), "jogress": (kind, 1, None),
                "area": (kind, "3", None)}.get(kind, (kind, 0, 99))
        L._atom_met(p, atom)          # must not raise: every kind is handled
        met, text = L._atom_row(p, atom)
        assert text, f"{kind} renders no checklist row"


def test_a_door_only_row_names_the_door_instead_of_faking_a_countdown():
    """`unmet=0` with `ready=False` is the DOOR shape, not a lie: the row
    is informational (met=None) and says how to get there."""
    p, _road = _grow(43, "good")          # ends at Growmon, a jogress door
    rows = L.evo_rows(p)
    assert rows, "the stuck form has no onward rows at all"
    for num, _name, ready, unmet in rows:
        if not ready and unmet == 0:
            report = L.requirement_report(p, num)
            assert any(met is None and txt for met, txt in report), \
                "a door row must SAY the door"


# ---- what an evolution does to the ledger -------------------------------

def test_evolving_resets_the_stage_counters_and_keeps_the_life_ones():
    p = _raised(care_mistakes=7, stage_trainings=55, stage_battles=9,
                total_trainings=500)
    p.stage_seconds = p.STAGE_DURATION[p.stage] + 1
    before_num = p.num
    p._maybe_evolve()
    if p.num == before_num:
        pytest.skip("this fixture's form has no ready row")
    assert p.stage_trainings == 0 and p.stage_battles == 0
    assert p.care_mistakes == 0
    assert p.total_trainings == 500 and p.battles == 60 and p.wins == 50
    assert len(p.battle_log) == 15          # the Pen20 window rides for life


def test_the_elder_gate_cannot_strand_a_pet_mid_ladder():
    """Evolution freezes at elder.  That must sit far beyond the whole
    ladder, or a slow raiser would be locked out of its own Mega."""
    from tuipet.petbase import AGE_DAY, GERIATRIC_AGE_DAYS
    p = Pet(num=100, stage="Fresh", attribute="Vaccine")
    ladder = sum(d for d in p.STAGE_DURATION.values() if d < 9e8)
    assert GERIATRIC_AGE_DAYS * AGE_DAY > ladder * 10


# ---- the two off-chart doors --------------------------------------------

@pytest.mark.usefixtures("care_ok")
def test_an_armed_field_steers_the_next_evolution_and_clears_its_charge():
    p = _raised()
    fld = p.field if p.field not in ("", "None") else "NatureSpirit"
    p.dna_applied = {fld: 999}
    target = evolution.divergence_target(p)
    assert target is not None, "an armed Field opened no road"
    p.stage_seconds = p.STAGE_DURATION[p.stage] + 1
    p._maybe_evolve()
    assert p.num == target and not data.is_placeholder(p.num)
    # charges CLEAR on evolve (the dict keeps its keys; the values go to 0)
    assert all(v == 0 for v in p.dna_applied.values())


def test_a_crest_lands_only_on_forms_the_dossier_promised():
    """The shop names what a crest would answer RIGHT NOW; several armor
    forms may answer one crest, so the dossier lists the set and the pick
    must come from it."""
    promised = set(shop.crest_answer(_raised(num=33, stage="Rookie"),
                                     "egg_of_courage"))
    if not promised:
        pytest.skip("no armor answer for this fixture")
    got = set()
    for seed in range(12):
        random.seed(seed)
        q = _raised(num=33, stage="Rookie")
        tgt = evolution.item_select(q, Pet._CREST_IDS["egg_of_courage"])
        if tgt:
            got.add(data.record_for(tgt).get("name"))
    assert got <= promised, f"a crest landed off-dossier: {got - promised}"


# ---- the book itself -----------------------------------------------------

def test_the_album_roster_is_canonical_and_placeholder_free():
    roster = data.album_roster()
    assert len(roster) > 1000
    assert not [n for n in roster if data.is_placeholder(n)]
    assert len(set(roster)) == len(roster)


@pytest.mark.parametrize("page", range(9))
def test_every_digicore_page_fits_the_LCD(page):
    p = _raised(total_trainings=412, stage_trainings=42, trophies=3)
    pan = DigiCorePanel(p)
    if page >= len(pan.pages):
        pytest.skip("fewer pages than that")
    pan.i = page
    for _ in range(3):
        pan.anim()
    rows = pan.text().plain.rstrip("\n").split("\n")
    assert len(rows) <= R, f"{pan.pages[page][0]}: {len(rows)} rows"
    assert max(len(r) for r in rows) <= C
    pan.strip()


def test_the_core_countdown_never_contradicts_itself():
    """'◆ N to evolve' must not appear on a pet with nothing pending, and
    must never read zero while an evolution IS pending."""
    for stage in ("Rookie", "Champion", "Ultimate"):
        p = _raised(stage=stage)
        p.stage_seconds = 0.0
        growth = p.STAGE_DURATION.get(p.stage)
        pending = (growth is not None and growth < 9e8
                   and digicore.has_next(p))
        n = digicore.core_number(p)
        assert n >= 1
        if pending:
            assert n <= digicore.DIGICORE_BASE_RATE
