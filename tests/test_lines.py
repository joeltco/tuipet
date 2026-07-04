"""LINES_SPEC arc 1 — the line engine: grammar, first-match selection, per-stage
counters, the hatch binding, and the digicore chart UI for line pets.

The ver1 coverage matrix is the load-bearing test: every reachable counter
combination at each parent must land on exactly one deterministic row (the
whole point of replacing the fuzzy engine)."""
import pytest

from tuipet import lines
from tuipet.pet import Pet


# ---- a minimal stand-in with just the counters the grammar reads ------------

class _Counters:
    def __init__(self, num, line_id="ver1", cm=0, tr=0, of=0, btl=0, log=(),
                 mega=0, vac=0, dat=0, vir=0, hp=5):
        self.num, self.line_id = num, line_id
        self.care_mistakes, self.stage_trainings, self.overeat = cm, tr, of
        self.stage_battles, self.battle_log, self.mega_kills = btl, list(log), mega
        self.vaccine, self.data_power, self.virus, self.full_health = vac, dat, vir, hp


# ---- grammar -----------------------------------------------------------------

def test_rule_grammar_parses_every_atom():
    assert lines.parse_rule("TIME") == [[]]
    assert lines.parse_rule("") == [[]]
    assert lines.parse_rule("CM 0-2, TR 16+") == [[("cm", 0, 2), ("tr", 16, None)]]
    assert lines.parse_rule("WIN 12/15") == [[("win", 12, 15)]]
    assert lines.parse_rule("OF 3") == [[("of", 3, 3)]]
    assert lines.parse_rule("BTL 15+, LV 5-6, KO6 5+") == \
        [[("btl", 15, None), ("lv", 5, 6), ("ko6", 5, None)]]
    assert lines.parse_rule("AREA 3") == [[("area", "3", None)]]
    # OR alternatives split independently
    assert lines.parse_rule("CM 3+, TR 0-4 | CM 3+, OF 0-2") == \
        [[("cm", 3, None), ("tr", 0, 4)], [("cm", 3, None), ("of", 0, 2)]]


def test_rule_grammar_rejects_junk():
    with pytest.raises(ValueError):
        lines.parse_rule("XY 3+")
    with pytest.raises(ValueError):
        lines.parse_rule("AREA")


def test_ver1_loads_shaped_like_the_spec():
    v1 = lines.load_lines()["ver1"]
    assert v1["root"] == 1411
    assert len(v1["members"]) == 13
    # first-match order is the data: Numemon's catch-all must be LAST
    assert [r["num"] for r in v1["children"][29]] == [93, 102, 95, 124, 116]
    assert lines.line_for_hatch(1411) == "ver1"
    assert lines.line_for_hatch(2) == ""          # the duplicate Botamon is NOT a root


# ---- ver1 coverage matrix (the DM20 brackets, deterministic) -----------------

def _expected_champion(cm, tr, of):
    if cm <= 2:
        return 93 if tr >= 16 else 102
    if tr >= 16 and of >= 3:
        return 95
    if 5 <= tr <= 15 and of >= 3:
        return 124
    return 116


def test_agumon_matrix_every_combo_lands_on_exactly_one_row():
    for cm in range(0, 6):
        for tr in (0, 4, 5, 15, 16, 25):
            for of in (0, 2, 3, 6):
                got = lines.select_line(_Counters(29, cm=cm, tr=tr, of=of))
                assert got == _expected_champion(cm, tr, of), (cm, tr, of, got)


def test_perfect_gate_is_the_rolling_window():
    assert lines.select_line(_Counters(93, log=[1] * 11 + [0] * 4)) is None
    assert lines.select_line(_Counters(93, log=[1] * 12 + [0] * 3)) == 220
    # only the LAST 15 count: 12 old wins pushed out by recent losses don't gate
    assert lines.select_line(_Counters(93, log=[1] * 12 + [0] * 15)) is None
    # every ver1 Adult funnels through the same gate
    assert lines.select_line(_Counters(124, log=[1] * 12)) == 237
    assert lines.select_line(_Counters(116, log=[1] * 12)) == 192


def test_mega_gate_and_the_top_of_the_line():
    assert lines.select_line(_Counters(220, cm=0)) == 297
    assert lines.select_line(_Counters(220, cm=3)) is None
    assert lines.select_line(_Counters(300)) is None        # Mega: no children, stays


def test_time_rows_pass_with_zero_counters():
    assert lines.select_line(_Counters(1411)) == 1455
    assert lines.select_line(_Counters(1455)) == 29


# ---- Pet wiring ----------------------------------------------------------------

def _line_pet():
    p = Pet.new_egg(egg_type=1)          # the Botamon egg
    p._hatch_into_fresh()
    return p


def test_botamon_egg_binds_the_ver1_line():
    p = _line_pet()
    assert (p.num, p.line_id) == (1411, "ver1")
    assert lines.active(p)
    assert lines.bedtime(p) == "20:00"


def test_training_counts_every_attempt_win_or_lose():
    p = _line_pet()
    p.apply_training(3, 90, game="vaccine")      # success
    p.apply_training(0, 10, game="vaccine")      # failure still counts (Pen20)
    assert p.stage_trainings == 2


def test_battles_feed_the_stage_count_and_rolling_log():
    p = _line_pet()
    for i in range(20):
        p.record_battle(i % 2 == 0)
    assert p.stage_battles == 20
    assert len(p.battle_log) == 15               # rolling window caps at 15
    p.record_battle(True, enemy={"stage": "Mega", "hp": 20, "vaccine": 90,
                                 "data_power": 0, "virus": 0, "bits": (1, 2)})
    p.record_battle(True, enemy={"stage": "Champion", "hp": 10, "vaccine": 0,
                                 "data_power": 50, "virus": 0, "bits": (1, 2)})
    assert p.mega_kills == 1                     # only Ultimate/Mega-class foes count


def test_evolution_resets_stage_counters_but_keeps_the_log():
    p = _line_pet()
    p.apply_training(3, 90, game="vaccine")
    p.record_battle(True)
    p.care_mistakes = 4
    p.evolve_to(1455)
    assert (p.stage_trainings, p.stage_battles, p.care_mistakes) == (0, 0, 0)
    assert p.battle_log == [1]                   # Pen20: battles carry over


def test_full_ver1_life_greymon_road():
    p = _line_pet()
    p.stage_seconds = 9e8
    p._maybe_evolve()
    assert p.num == 1455                         # Koromon: time alone
    p.stage_seconds = 9e8
    p._maybe_evolve()
    assert p.num == 29                           # Agumon: time alone
    p.care_mistakes, p.stage_trainings = 1, 16   # good care, hard training
    p.stage_seconds = 9e8
    p._maybe_evolve()
    assert p.num == 93                           # Greymon
    p.stage_seconds = 9e8
    p._maybe_evolve()
    assert p.num == 93                           # battle gate unmet: stays, no bail-out
    p.battle_log = [1] * 12 + [0] * 3
    p._maybe_evolve()
    assert p.num == 220                          # MetalGreymon at 12/15
    p.care_mistakes = 0
    p.stage_seconds = 9e8
    p._maybe_evolve()
    assert p.num == 297                          # BlitzGreymon: 0-2 slips at Perfect
    p.stage_seconds = 9e8
    p._maybe_evolve()
    assert p.num == 297                          # top of the line


def test_neglect_road_leads_to_numemon():
    p = _line_pet()
    for _ in range(2):
        p.stage_seconds = 9e8
        p._maybe_evolve()
    p.care_mistakes, p.stage_trainings, p.overeat = 5, 2, 0
    p.stage_seconds = 9e8
    p._maybe_evolve()
    assert p.num == 116                          # Numemon: the face of bad care


def test_corpus_pets_keep_the_fuzzy_engine():
    p = Pet.from_num(29)
    assert p.line_id == "" and not lines.active(p)
    # a line pet jogressed OUT of its subtree falls back to the corpus engine
    q = _line_pet()
    q.num = 62                                   # Veemon: not a ver1 member
    assert not lines.active(q)


def test_line_fields_survive_the_save_round_trip():
    from tuipet import persistence
    p = _line_pet()
    p.stage_trainings, p.battle_log, p.mega_kills = 7, [1, 0, 1], 2
    d = persistence.to_save_dict(p)
    q, _ = persistence.pet_from_save(d, catch_up=False)
    assert (q.line_id, q.stage_trainings, q.battle_log, q.mega_kills) == \
        ("ver1", 7, [1, 0, 1], 2)


# ---- digicore chart UI (panel smoke: does it draw) ----------------------------

def test_digicore_pages_render_the_line_chart():
    from tuipet.digicorescreen import DigiCorePanel, next_evolution
    p = _line_pet()
    for _ in range(2):                           # walk to Agumon (the 5-row chart)
        p.stage_seconds = 9e8
        p._maybe_evolve()
    p.care_mistakes, p.stage_trainings = 1, 16
    assert next_evolution(p) == 93               # silhouette: the closest row
    pan = DigiCorePanel(p)
    pan.text()
    for k in (["space", "space"] + ["right"] * 7 +
              ["enter", "down", "down", "up", "escape", "down", "enter", "escape"]):
        pan.key(k)
        pan.anim()
        pan.text()                               # every state draws


def test_requirement_report_shows_live_counters():
    p = _line_pet()
    for _ in range(2):
        p.stage_seconds = 9e8
        p._maybe_evolve()
    p.care_mistakes, p.stage_trainings = 1, 10
    rows = lines.requirement_report(p, 93)
    assert (True, "care slips 0-2  (now 1)") in rows
    assert (False, "trainings 16+  (now 10)") in rows
    # OR rules report the closest alternative
    r = lines.requirement_report(_Counters(93, log=[1] * 10 + [0] * 5), 220)
    assert r == [(False, "wins 12 of last 15  (now 10/15)")]
