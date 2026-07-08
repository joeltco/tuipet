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
    assert len(v1["members"]) == 16
    # the Koromon split (DM20 canon; the Betamon half was missing until
    # 2026-07-07 -- Joel: "wheres the betamon line on the 1st egg???")
    assert [r["num"] for r in v1["children"][1455]] == [29, 37]
    # first-match order is the data: Numemon's catch-all must be LAST
    assert [r["num"] for r in v1["children"][29]] == [93, 102, 95, 124, 116]
    assert [r["num"] for r in v1["children"][37]] == [102, 95, 90, 110, 116]
    # dual-road targets keep one row per parent; members unions the parentage
    assert v1["members"][102]["parents"] == [29, 37]
    assert v1["members"][95]["parents"] == [29, 37]
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


def test_koromon_splits_on_care_mistakes():
    """DM20 Ver.1: Agumon at 0-2 care mistakes, Betamon at 3+ (humulos chart).
    The clock alone no longer decides the first egg's Rookie."""
    assert lines.select_line(_Counters(1455, cm=0)) == 29
    assert lines.select_line(_Counters(1455, cm=2)) == 29
    assert lines.select_line(_Counters(1455, cm=3)) == 37
    assert lines.select_line(_Counters(1455, cm=9)) == 37


def _expected_betamon_champion(cm, tr, of):
    if cm <= 2:
        return 102 if tr >= 16 else 95
    if 8 <= tr <= 15:
        return 90 if of <= 2 else 110
    return 116


def test_betamon_matrix_every_combo_lands_on_exactly_one_row():
    """The Betamon road mirrors canon exactly: Devimon/Meramon flip their
    training brackets vs Agumon's, Airdramon/Seadramon split the 8-15
    training band by overfeed, Numemon takes the rest (TR 0-7 | 16+)."""
    for cm in range(0, 6):
        for tr in (0, 7, 8, 15, 16, 25):
            for of in (0, 2, 3, 6):
                got = lines.select_line(_Counters(37, cm=cm, tr=tr, of=of))
                assert got == _expected_betamon_champion(cm, tr, of), (cm, tr, of, got)


def test_betamon_champions_feed_the_ver1_ultimates():
    """Canon ultimate roads: Airdramon -> MetalGreymon, Seadramon -> Mamemon."""
    assert lines.select_line(_Counters(90, log=[1] * 12)) == 220
    assert lines.select_line(_Counters(110, log=[1] * 12)) == 237


# ---- ver2-ver5 canon rewrite (DM20 charts, humulos; egg sweep 2026-07-07) ----
# Every device line shares two bracket shapes.  First rookie (Agumon-shape):
# A(0-2,16+) B(0-2,0-15) C(3+,16+,OF3+) D(3+,5-15,OF3+) E(catch-all).
# Second rookie: A'(0-2,16+) B'(0-2,0-15) C'(3+,8-15,OF0-2) D'(3+,16+,OF3+)
# E'(catch-all).  (ver1's Betamon is the one canon exception: its D' is
# Seadramon at 8-15/OF3+ -- pinned in its own matrix above.)
_FIRST_ROOKIES = {  # parent: (split_parent, A, B, C, D, E)
    29: (1455, 93, 102, 95, 124, 116),     # ver1 Agumon
    34: (1459, 140, 101, 136, 108, 109),   # ver2 Gabumon
    31: (1456, 98, 91, 121, 87, 117),      # ver3 Patamon
    46: (1461, 125, 104, 120, 123, 118),   # ver4 Biyomon
    33: (1457, 129, 94, 114, 115, 112),    # ver5 Gazimon
}
_SECOND_ROOKIES = {  # parent: (split_parent, A', B', C', D', E')
    43: (1459, 101, 97, 136, None, 109),   # ver2 Elecmon (Whamon slot = corpus gap)
    45: (1456, 91, 106, 121, 122, 117),    # ver3 Kunemon
    44: (1461, 104, 88, 120, 135, 118),    # ver4 Palmon
    35: (1457, 94, 148, 114, 111, 112),    # ver5 Gizamon
}


def _lid(parent):
    return {29: "ver1", 34: "ver2", 31: "ver3", 46: "ver4", 33: "ver5",
            43: "ver2", 45: "ver3", 44: "ver4", 35: "ver5"}[parent]


def test_every_device_rookie_split_is_care_mistakes():
    for first, (split, *_r) in _FIRST_ROOKIES.items():
        lid = _lid(first)
        assert lines.select_line(_Counters(split, lid, cm=0)) == first, lid
    for second, (split, *_r) in _SECOND_ROOKIES.items():
        lid = _lid(second)
        assert lines.select_line(_Counters(split, lid, cm=3)) == second, lid


def test_first_rookie_matrix_all_device_lines():
    for parent, (_s, A, B, C, D, E) in _FIRST_ROOKIES.items():
        lid = _lid(parent)
        for cm in range(0, 6):
            for tr in (0, 4, 5, 15, 16, 25):
                for of in (0, 2, 3, 6):
                    if cm <= 2:
                        want = A if tr >= 16 else B
                    elif tr >= 16 and of >= 3:
                        want = C
                    elif 5 <= tr <= 15 and of >= 3:
                        want = D
                    else:
                        want = E
                    got = lines.select_line(_Counters(parent, lid, cm=cm, tr=tr, of=of))
                    assert got == want, (lid, parent, cm, tr, of, got, want)


def test_second_rookie_matrix_all_device_lines():
    for parent, (_s, A, B, C, D, E) in _SECOND_ROOKIES.items():
        lid = _lid(parent)
        for cm in range(0, 6):
            for tr in (0, 7, 8, 15, 16, 25):
                for of in (0, 2, 3, 6):
                    if cm <= 2:
                        want = A if tr >= 16 else B
                    elif 8 <= tr <= 15 and of <= 2:
                        want = C
                    elif tr >= 16 and of >= 3:
                        want = D if D is not None else E
                    else:
                        want = E
                    got = lines.select_line(_Counters(parent, lid, cm=cm, tr=tr, of=of))
                    assert got == want, (lid, parent, cm, tr, of, got, want)


def test_device_ultimate_feeds_match_canon():
    """WIN 12/15 funnels: each champion reaches its canon Perfect."""
    feeds = {  # champion: (line, ultimate)
        140: ("ver2", 195), 101: ("ver2", 195), 97: ("ver2", 195),
        108: ("ver2", 213), 136: ("ver2", 213), 109: ("ver2", 199),
        98: ("ver3", 191), 91: ("ver3", 191), 106: ("ver3", 191),
        87: ("ver3", 238), 121: ("ver3", 238), 122: ("ver3", 238),
        117: ("ver3", 194),
        125: ("ver4", 210), 104: ("ver4", 210), 88: ("ver4", 210),
        123: ("ver4", 196), 120: ("ver4", 196), 135: ("ver4", 196),
        118: ("ver4", 198),
        129: ("ver5", 214), 94: ("ver5", 214), 148: ("ver5", 214),
        115: ("ver5", 197), 114: ("ver5", 197), 111: ("ver5", 197),
        112: ("ver5", 239),
    }
    for champ, (lid, ult) in feeds.items():
        assert lines.select_line(_Counters(champ, lid, log=[1] * 12)) == ult, (lid, champ)
        assert lines.select_line(_Counters(champ, lid, log=[0] * 15)) is None, (lid, champ)


def test_device_megas_match_canon():
    megas = {  # ultimate: (line, mega)
        195: ("ver2", 290), 213: ("ver2", 398),
        191: ("ver3", 296), 194: ("ver3", 397),
        210: ("ver4", 396), 198: ("ver4", 395),
        214: ("ver5", 276), 239: ("ver5", 277),
    }
    for ult, (lid, mega) in megas.items():
        assert lines.select_line(_Counters(ult, lid, cm=0)) == mega, (lid, ult)
        assert lines.select_line(_Counters(ult, lid, cm=3)) is None, (lid, ult)


def test_verE_is_the_canon_straight_chain():
    """DM20's Meicoo bonus line has NO requirements until the Mega:
    YukimiBotamon -> Nyaromon -> Salamon -> Meicoomon -> Meicrackmon ->
    Rasielmon (CM 0-2)."""
    vE = lines.load_lines()["verE"]
    assert len(vE["members"]) == 6
    for parent, child in ((1410, 1458), (1458, 47), (47, 386), (386, 389)):
        assert lines.select_line(_Counters(parent, "verE", cm=9)) == child
    assert lines.select_line(_Counters(389, "verE", cm=0)) == 392
    assert lines.select_line(_Counters(389, "verE", cm=3)) is None


def test_requirement_report_shows_this_roads_rule():
    """Devimon is reachable from BOTH Rookies with different training
    brackets -- the data book must show the rule for the pet's own road."""
    agu = "".join(t for _, t in lines.requirement_report(_Counters(29), 102))
    beta = "".join(t for _, t in lines.requirement_report(_Counters(37), 102))
    assert "0-15" in agu and "16+" not in agu
    assert "16+" in beta and "0-15" not in beta


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
