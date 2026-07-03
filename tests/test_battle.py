"""Battle resolution math (Workstream A).

tuipet's combat is DVPet's Model.Battle: per-round damage is
    base_attack(stage) + calc_attack_power(attr)  (+ affinity, which is 0)
floored at 0, where calc_attack_power is -1/0/+1 from comparing this side's
attribute count against the opponent's. (The "attribute triangle" is a real-
hardware concept; tuipet's actual modifier is this count comparison.)

A num=-1 pet/enemy carries no attack-effect chips, so battlefx is a no-op and
rounds are deterministic except for checkFirst ties — which we avoid by giving
the two sides different power sums. Persistence side effects of record_battle are
sandboxed by the autouse fixture in conftest.
"""
import random


from tuipet import battle, battlefx
from tuipet.battle import Battle, calc_attack_power, BASE_ATTACK, MAX_HEALTH
from tuipet.pet import Pet


def _enemy(stage="Rookie", v=0, d=0, vi=0, hp=10, num=-1, boss=False):
    return {"num": num, "name": "Foe", "stage": stage, "vaccine": v,
            "data_power": d, "virus": vi, "hp": hp, "boss": boss, "bits": (1, 5)}


def _pet(stage="Rookie", v=5, d=5, vi=5, wins=0):
    return Pet(num=-1, stage=stage, vaccine=v, data_power=d, virus=vi, wins=wins)


# ---- pure math -------------------------------------------------------------

def test_calc_attack_power():
    assert calc_attack_power("Vaccine", {"Vaccine": 3}, {"Vaccine": 1}) == 1
    assert calc_attack_power("Vaccine", {"Vaccine": 1}, {"Vaccine": 3}) == -1
    assert calc_attack_power("Vaccine", {"Vaccine": 2}, {"Vaccine": 2}) == 0


def test_damage_base_plus_power_floored():
    b = Battle(_pet("Rookie"), _enemy("Rookie"))
    strong = {"Vaccine": 9, "Data": 0, "Virus": 0}
    weak = {"Vaccine": 1, "Data": 0, "Virus": 0}
    even = {"Vaccine": 5, "Data": 0, "Virus": 0}
    assert b._damage("Rookie", "Vaccine", strong, weak) == BASE_ATTACK["Rookie"] + 1   # 6
    assert b._damage("Rookie", "Vaccine", even, even) == BASE_ATTACK["Rookie"]          # 5
    assert b._damage("Rookie", "Vaccine", weak, strong) == BASE_ATTACK["Rookie"] - 1    # 4
    # Fresh base 1 with a disadvantage -> 1 + (-1) = 0, floored (never negative)
    assert b._damage("Fresh", "Vaccine", weak, strong) == 0


# ---- setup -----------------------------------------------------------------

def test_hp_setup_per_stage():
    # battle HP = the pet's TRAINED fullHealthPoints (HP drill grows it);
    # the flat stage table remains only as the no-field fallback
    p = _pet("Rookie")
    p.full_health = 8
    assert Battle(p, _enemy(hp=10)).pet_hp == 8
    # enemy HP is taken from its sheet, floored to a minimum of 2
    assert Battle(_pet(), _enemy(hp=1)).enemy_hp == 2
    assert Battle(_pet(), _enemy(hp=20)).enemy_hp == 20


def test_enemy_attribute_is_strongest_count():
    b = Battle(_pet(), _enemy(v=1, d=9, vi=2))
    assert b.enemy["attribute"] == "Data"


# ---- win / loss ------------------------------------------------------------

def test_win_when_pet_survives():
    b = Battle(_pet(), _enemy())
    b.pet_hp, b.enemy_hp = 3, 0
    b._finish()
    assert b.over is True and b.won is True


def test_loss_when_pet_down():
    b = Battle(_pet(), _enemy())
    b.pet_hp, b.enemy_hp = 0, 3
    b._finish()
    assert b.won is False


def test_double_ko_is_a_loss():
    """battleEnd: the player loses iff its OWN hp <= 0 — a mutual KO is a loss."""
    b = Battle(_pet(), _enemy())
    b.pet_hp, b.enemy_hp = 0, 0
    b._finish()
    assert b.won is False


# ---- initiative ------------------------------------------------------------

def test_initiative_favours_greater_power():
    strong = Battle(_pet(v=10, d=10, vi=10), _enemy(v=0, d=0, vi=0))
    assert battlefx._check_first(strong) is True
    weak = Battle(_pet(v=0, d=0, vi=0), _enemy(v=10, d=10, vi=10, hp=10))
    assert battlefx._check_first(weak) is False


def test_first_striker_ko_prevents_retaliation():
    """If the player goes first and the blow is lethal, the enemy never hits back."""
    b = Battle(_pet(v=20, d=20, vi=20), _enemy("Rookie", v=0, d=0, vi=0, hp=1))
    assert b.pet_hp == b.pet_max
    b.play_round("Vaccine")
    assert b.over is True and b.won is True
    assert b.pet_hp == b.pet_max, "a first-strike KO must not let the enemy retaliate"


# ---- AI difficulty ramp (adapted, but the thresholds are pinned) ----------

def test_ai_ramp_thresholds():
    assert battle.ai_for_wins(0, False) == "Random"
    assert battle.ai_for_wins(15, False) == "Brute"
    assert battle.ai_for_wins(30, False) == "StrategicBrute"
    assert battle.ai_for_wins(45, False) == "StrategicDefense"
    assert battle.ai_for_wins(60, True) == "StrategicDefense"
    assert battle.ai_for_wins(60, False) == "StrategicBalanced"


# ---- full bout invariants --------------------------------------------------

def test_full_battle_terminates_and_stays_bounded():
    random.seed(1234)
    b = Battle(_pet("Rookie", v=4, d=4, vi=4), _enemy("Rookie", v=3, d=3, vi=3, hp=8))
    for _ in range(200):
        if b.over:
            break
        b.play_round("Vaccine")
        assert b.pet_hp <= b.pet_max, "HP must never exceed the cap (heal clamp)"
        assert b.enemy_hp <= b.enemy_max
    assert b.over is True
    assert b.won in (True, False)


def test_battle_win_grows_dominant_attribute():
    # battleEnd incStats: a win adds +1 power in the enemy's dominant attribute
    from tuipet.pet import Pet
    p = Pet(num=1, stage="Rookie", attribute="Vaccine", vaccine=5, data_power=5, virus=5)
    v0 = p.virus
    msg = p.record_battle(True, {"stage": "Rookie", "hp": 10, "bits": (1, 1),
                                 "vaccine": 2, "data_power": 3, "virus": 9, "num": 1})
    assert p.virus == v0 + 1 and "+1 Virus" in msg


def test_battle_loss_saps_obedience():
    from tuipet.pet import Pet
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    o0 = p.obedience
    p.record_battle(False, {"stage": "Rookie", "hp": 10, "num": 1,
                            "vaccine": 1, "data_power": 1, "virus": 1})
    assert p.obedience == o0 - 1


def test_hollow_win_is_joyless():
    # beating a feeble higher-stage foe costs mood (OverpoweredBattleWonMoodDec)
    import random as _r
    _r.seed(0)
    from tuipet.pet import Pet
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    p.mood = 0
    p.record_battle(True, {"stage": "Champion", "hp": 3, "bits": (0, 0), "num": 1,
                           "vaccine": 1, "data_power": 1, "virus": 1})
    assert p.mood < 10        # the +10 win bump got eaten by the -20 hollow-win penalty
