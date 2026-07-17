"""LINES_SPEC arc 4 — the verX line (DMX grammar: LV/KO6/AREA/BTL), the Pen20
DP jogress meter, and the X-Antibody retirement."""
import random

from tuipet import data, jogress, lines, persistence
from tuipet.pet import Pet, DP_MAX


class _C:
    """Counter stub with just what the rule grammar reads."""
    def __init__(self, num, cm=0, tr=0, of=0, btl=0, log=(), mega=0, exp=0):
        self.num, self.line_id = num, "verX"
        self.care_mistakes, self.stage_trainings, self.overeat = cm, tr, of
        self.stage_battles, self.battle_log, self.mega_kills = btl, list(log), mega
        self.exp = exp                       # DMX battle experience (LV fix 2026-07-17)


def test_verx_loads_shaped_like_the_spec():
    vx = lines.load_lines()["verX"]
    assert vx["root"] == 1426                     # the EGG's hatch chain, not dex 928
    assert len(vx["members"]) == 15
    assert [r["num"] for r in vx["children"][1479]] == [41, 829]
    assert lines.line_for_hatch(1426) == "verX"


def test_rookie_split_pure_or_scrappy():
    assert lines.select_line(_C(1479, cm=0)) == 41      # Dorumon: kept pure
    assert lines.select_line(_C(1479, cm=3)) == 829     # Agumon X: the scrappy road


def test_dorumon_corrupts_without_care_and_training():
    assert lines.select_line(_C(41, cm=1, tr=8)) == 86       # Dorugamon
    assert lines.select_line(_C(41, cm=1, tr=7)) == 745      # DexDorugamon (lazy)
    assert lines.select_line(_C(41, cm=4, tr=20)) == 745     # DexDorugamon (neglect)


def test_agumon_x_level_gate():
    # LV 2 = 50 battle exp (the humulos DMX table; fix 2026-07-17)
    assert lines.select_line(_C(829, cm=0, exp=50)) == 851
    assert lines.select_line(_C(829, cm=0, exp=0)) == 997
    assert lines.select_line(_C(829, cm=3, exp=5000)) == 997   # slips: Numemon X


def test_ultimate_gates_win_btl_ko6():
    assert lines.select_line(_C(86, log=[1] * 12)) == 258            # DoruGreymon
    assert lines.select_line(_C(745, btl=10, log=[0] * 10)) == 747   # feral: losses count
    assert lines.select_line(_C(745, btl=9)) is None
    assert lines.select_line(_C(851, log=[1] * 12, mega=1)) == 845   # MetalGreymon X
    assert lines.select_line(_C(851, log=[1] * 12, mega=0)) is None  # KO6 unmet


def test_alphamon_needs_the_felled_raids():
    """AREA 3 re-gated (BASIC VPET 2026-07-16): 4 felled raid bosses now."""
    c = _C(258, cm=0, mega=3)
    assert lines.select_line(c) == 329            # 3 raids: the beast road still
    for _ in range(3):
        persistence.raid_add()
    assert lines.select_line(c) == 329            # 3 is not enough for the ruins
    persistence.raid_add()
    assert lines.select_line(c) == 330            # Alphamon: care + kills + 4 bosses
    assert lines.select_line(_C(845, cm=0)) == 856          # WarGreymon X
    assert lines.select_line(_C(997, cm=0, log=[1] * 15)) is None    # punishment leaf


def test_numemon_x_is_a_leaf_and_dex_road_completes():
    vx = lines.load_lines()["verX"]
    assert 997 not in vx["children"]
    assert [r["num"] for r in vx["children"][747]] == [746]  # DexDorugoramon


# ---- Pen20 DP meter ---------------------------------------------------------------

def _pet():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 12 * 60.0
    return p


def test_sleep_refills_dp_in_three_game_hours():
    p = _pet()
    p.asleep, p.anim = True, "sleep"
    for _ in range(180):
        p.tick(1.0)
    assert p.dp == DP_MAX


def test_jogress_demands_and_spends_full_dp():
    random.seed(9)
    p = _pet()
    p.compliance = True
    msg = jogress.can_jogress(p)
    assert msg is not None and "DP 0/4" in msg
    p.dp = DP_MAX
    assert "DP" not in (jogress.can_jogress(p) or "")
    opts = jogress.options(p)
    if opts:                                  # data-dependent; the spend is the point
        jogress.fuse(p, opts[0]["num"])
        assert p.dp == 0


# ---- the X-Antibody retirement ------------------------------------------------------

def test_no_pet_is_born_with_the_antibody():
    import tuipet.pet as pet_mod
    assert not hasattr(pet_mod, "X_BIRTH_TARGET")
    for seed in range(120):
        random.seed(seed)
        p = Pet.new_egg(egg_type=1)
        p._hatch_into_fresh()
        assert p.x_antibody == "None"


def test_antibody_no_longer_steers_selection():
    from tuipet import evolution
    random.seed(4)
    p = Pet.from_num(12)                      # corpus Koromon (fuzzy engine)
    p.x_antibody = "Permanent"                # a legacy save
    _, by_num = data.load_sprites()
    for _ in range(30):
        t = evolution.select(p)
        if t is not None:
            assert by_num[t]["stage"] != p.stage    # same-stage X reformat is gone


def test_surrender_lands_a_loss_in_the_rolling_window():
    """Audit 2026-07-04: surrendering skipped the battle_log entirely, letting
    a player keep the 12-of-15 window loss-free by fleeing every bad fight."""
    import random
    from tuipet.battle import Battle
    random.seed(3)
    p = _pet()
    p.battle_log = [1] * 5
    b = Battle(p, enemy={"num": 100, "name": "Foe", "stage": "Champion", "hp": 10,
                         "vaccine": 50, "data_power": 0, "virus": 0, "bits": (1, 2)})
    b.surrender()
    assert p.battle_log == [1] * 5 + [0]        # the fled fight counts against you
    assert p.wins == 0 and b.won is False       # classic stats stay canon
