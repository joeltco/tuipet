"""The DMX level system, humulos canon (fix 2026-07-17).

The manual (humulos.com/digimon/dmx/manual): level rises on battle
experience -- cumulative thresholds 50/150/500/800/1000/1500/2000/3000/5000
for levels 2..10 -- capped per stage (Rookie 4 / Champion 6 / Ultimate 8 /
Mega 10), and "Stages IV, V and VI take Level into account" for evolution.
tuipet's declared tuning: EXP_PER_WIN=100 (the manual leaves the award
unspecified), PvP excluded like KO6.  The old DVPet getLevel read powers +
trained HP -- both starved by the 0.5 conversions, walling all 73 LV atoms.
"""
from tuipet import lines
from tuipet.lines import DMX_EXP_LEVELS, DMX_LEVEL_CAP, _pet_level
from tuipet.pet import Pet, EXP_PER_WIN


def _pet(stage="Ultimate", exp=0):
    p = Pet(num=205, stage=stage, attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p.exp = exp
    return p


def test_the_canon_threshold_table_verbatim():
    assert DMX_EXP_LEVELS == (0, 50, 150, 500, 800, 1000, 1500, 2000, 3000, 5000)
    assert DMX_LEVEL_CAP["Rookie"] == 4 and DMX_LEVEL_CAP["Champion"] == 6
    assert DMX_LEVEL_CAP["Ultimate"] == 8 and DMX_LEVEL_CAP["Mega"] == 10


def test_levels_climb_the_table_and_cap_by_stage():
    assert _pet_level(_pet(exp=0)) == 1
    assert _pet_level(_pet(exp=49)) == 1
    assert _pet_level(_pet(exp=50)) == 2
    assert _pet_level(_pet(exp=800)) == 5
    assert _pet_level(_pet(exp=5000)) == 8         # Ultimate caps at 8...
    assert _pet_level(_pet(stage="Mega", exp=5000)) == 10   # ...a Mega reads 10
    assert _pet_level(_pet(stage="Rookie", exp=5000)) == 4  # the Rookie cap


def test_wins_pay_experience_but_pvp_never_does():
    p = _pet()
    p.energy = 20
    foe = {"num": 4, "stage": "Champion", "attribute": "Data"}
    p.record_battle(True, foe)
    assert p.exp == EXP_PER_WIN
    p.record_battle(False, foe)
    assert p.exp == EXP_PER_WIN                    # losses pay nothing
    p.record_battle(True, foe, online=True)
    assert p.exp == EXP_PER_WIN                    # PvP excluded, like KO6


def test_every_lv_atom_is_reachable_under_its_parents_cap():
    """The un-walling this fix exists for: each LV-gated member's lower
    bound must be reachable at the cap of at least one of its PARENTS'
    stages (a Mega row gating LV 8 reads the Ultimate parent's cap; the
    LV 9-10 rows are the Mega X-roads)."""
    L = lines.load_lines()
    checked = 0
    for lid, line in L.items():
        for m in line["members"].values():
            for alt in m["rule"]:
                for kind, a, b in alt:
                    if kind != "lv":
                        continue
                    checked += 1
                    caps = [DMX_LEVEL_CAP.get(
                        line["members"][p]["stage"], 10)
                        for p in m["parents"] if p in line["members"]]
                    assert caps and a <= max(caps), \
                        f"{lid}:{m['num']} LV {a} unreachable (caps {caps})"
    assert checked >= 70                            # the whole family verified


def test_an_lv_gated_road_opens_at_the_canon_exp():
    """End to end on verX: Agumon X -> MetalGreymon X wants LV 2 = 50 exp
    = one paid win under the declared tuning."""
    class _C:
        def __init__(self, exp):
            self.num, self.line_id = 829, "verX"
            self.care_mistakes = self.stage_trainings = self.overeat = 0
            self.stage_battles, self.battle_log, self.mega_kills = 0, [], 0
            self.exp = exp
    assert lines.select_line(_C(0)) == 997          # unproven: the slip road
    assert lines.select_line(_C(EXP_PER_WIN)) == 851   # one win: the X road
