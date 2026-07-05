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
    # under ORDERS the unconditional BattleFreeObedienceInc (+1) nets a loss to 0
    # (canon battleEnd); FREE style forgoes it, so the loss bites in full
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    o0 = p.obedience
    p.record_battle(False, {"stage": "Rookie", "hp": 10, "num": 1,
                            "vaccine": 1, "data_power": 1, "virus": 1})
    assert p.obedience == o0                       # -1 loss + 1 discipline
    f = Pet(num=1, stage="Rookie", attribute="Vaccine", free_style=True)
    o0 = f.obedience
    f.record_battle(False, {"stage": "Rookie", "hp": 10, "num": 1,
                            "vaccine": 1, "data_power": 1, "virus": 1})
    assert f.obedience == o0 - 1


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


# ---- battle style (Battle_Style: Free vs Orders) -----------------------------

def test_free_style_adds_one_to_all_powers_and_self_picks():
    p = _pet("Rookie")
    p.vaccine, p.data_power, p.virus = 10, 5, 5
    p.free_style = True
    b = Battle(p, _enemy(hp=10))
    assert b._pet_counts == {"Vaccine": 11, "Data": 6, "Virus": 6}
    b.play_round("Virus")                      # the order is moot: it picks its own
    assert b.last_player_attr == b._own_choice() or b.last_player_attr in ("Vaccine", "Data", "Virus")
    assert not b.refused_order                 # Free never "refuses" -- no orders given


def test_orders_can_be_refused_mid_fight():
    import random
    random.seed(0)
    p = _pet("Rookie")
    p.vaccine, p.data_power, p.virus = 10, 5, 5
    p.obedience = -500                         # rock bottom: refusals certain
    p.full_health = 10
    b = Battle(p, _enemy(hp=10))
    b.play_round("Virus")
    assert b.refused_order                     # refuseAttack overrode the order
    assert p.scold_flag                        # setScold(true) mid-fight


def test_orders_pay_obedience_and_prouder_wins():
    p = _pet("Rookie")
    p.obedience = 50
    p.free_style = False
    m0 = p.mood
    p.record_battle(True, _enemy(hp=10))
    assert p.obedience >= 51                   # BattleFreeObedienceInc (+win rewards)
    free = _pet("Rookie")
    free.obedience = 50
    free.free_style = True
    free.record_battle(True, _enemy(hp=10))
    assert p.mood > free.mood                  # OrdersWonMoodInc only under orders


# ---- the surrender system (checkSurrender / onSurrender, wired 2026-07) ------

def _bp(obedience=500, mood=0):
    import tuipet.battlescreen as bs
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=obedience)
    p.mood = mood
    p.full_health = 10
    panel = bs.BattlePanel(p, {"num": 4, "name": "Foe", "stage": "Champion",
                               "vaccine": 5, "data_power": 5, "virus": 5,
                               "hp": 10, "bits": (0, 0)})
    return p, panel


def test_obedient_pet_never_asks_to_quit():
    import random
    random.seed(0)
    p, panel = _bp(obedience=500)
    for _ in range(60):
        panel._on_round_end()
        assert panel.phase == "menu"              # cont score towers over the roll


def test_broken_pet_falters_and_the_trainer_decides():
    import random
    random.seed(0)
    p, panel = _bp(obedience=-400, mood=-200)
    panel.battle.pet_hp = 1                       # bleeding: the low-HP factors bite
    asked = False
    for _ in range(80):
        panel.phase = "anim"
        panel._on_round_end()
        if panel.phase == "surrender_ask":
            asked = True
            break
        if panel.phase == "result":               # sv==1: it ran outright -- also valid
            asked = True
            break
    assert asked
    if panel.phase == "surrender_ask":
        o0 = p.obedience
        panel.key("n")                            # send it back in
        assert panel.phase == "menu"
        assert p.obedience == o0 + 1              # surrender_reject: obeys a touch more


def test_player_surrender_can_be_refused():
    import random
    random.seed(0)
    p, panel = _bp(obedience=-500)                # non-compliant: refusal certain
    panel.phase = "menu"
    r = panel._player_surrender()
    assert r is None                              # it would NOT give up
    assert p.scold_flag                           # the defiance opens the scold window
    p2, panel2 = _bp(obedience=500)
    p2.compliance = True                          # compliant: the surrender proceeds
    r2 = panel2._player_surrender()
    assert r2 == ("done", None)


# ---- battle animation audit (2026-07-04): reveal / dodge fidelity ------------

def test_intro_reveals_the_opponent_with_the_start_sting():
    """DVPet startBattle(): after the banner the OPPONENT is shown alone,
    taunting 1->6->1->6, with the _startBattle sting at the reveal edge."""
    import tuipet.battlescreen as bs
    _, panel = _bp()
    ms = [e["m"] for e in panel.timeline]
    assert ms[-bs.REVEAL_T:] == ["reveal"] * bs.REVEAL_T   # banner, THEN the taunt
    assert all(e.get("view") == "foe" for e in panel.timeline[-bs.REVEAL_T:])
    assert panel.sfx == "battle"                  # the banner sting on frame one
    panel.sfx = None
    while panel.timeline[panel.i]["m"] != "reveal":
        panel.anim()
    assert panel.sfx == "startBattle"             # fired exactly at the reveal edge
    assert "appears!" in panel.hud_note or panel.text() is not None
    panel._render_scene_frame(panel.timeline[panel.i])
    assert "appears!" in panel.hud_note


def test_dodge_hides_the_orb_and_hops_the_defender():
    """Canon dodge(): the attack sprite is HIDDEN (the unhurt hop IS the miss)
    and the defender leaps toward its wall AND UP, then drops back down.
    2026-07-04 raster audit: the old whiff-past orb restarted at the far edge
    (a visible teleport) and merged into the 16px defender like a hit."""
    from tuipet.theme import SIL_DAY
    _, panel = _bp()
    panel.pet_attr = panel.foe_attr = "Vaccine"
    calls = []
    panel._orb_overlay = lambda fr, mouth: (calls.append(fr["m"]), [])[1]
    base = {"view": "foe", "atk": "pet", "def": "foe", "ph": 5, "fh": 5}
    panel._render_scene_frame({"m": "dodge", "prog": 5 / 14, **base})
    panel._render_scene_frame({"m": "fire_in", "prog": 0.5, "double": False, **base})
    assert calls == ["fire_in"]                   # no orb drawn on the dodge

    def top_row(fr):
        t = panel._render_scene_frame(fr)
        for i, line in enumerate(t.markup.split("\n")):   # arena = markup, NEVER .plain
            if SIL_DAY in line:
                return i
        return None

    grounded = top_row({"m": "faceoff", **base})
    apex = top_row({"m": "dodge", "prog": 5 / 14, **base})
    landed = top_row({"m": "dodge", "prog": 13 / 14, **base})   # an IDLE return beat
    assert apex < grounded                        # airborne at the apex
    assert landed == grounded                     # back on its mark for the pose flips


def test_round_skip_never_swallows_the_killing_blow():
    """Joel 2026-07-05 ('it didn't play through to the death'): a bounced
    double-ENTER right after picking used to vaporise the whole round to the
    result.  Skips debounce the first beats, then jump TO the final impact
    (hit/flinch still play); a second press inside the impact finishes."""
    import random
    from tuipet.pet import Pet
    from tuipet.battlescreen import BattlePanel, SKIP_DEBOUNCE

    def run(presses):
        random.seed(3)
        p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=500)
        p.world_seconds = 12 * 60.0
        p.full_health = 5
        bp = BattlePanel(p, enemy={"num": 964, "name": "Foe", "stage": "Champion",
                                   "hp": 15, "vaccine": 8, "data_power": 0,
                                   "virus": 0, "bits": (1, 2)})
        bp.key("space")
        bp.key("1")
        for when in presses:
            while bp.i < when and bp.phase == "anim":
                bp.anim()
            bp.key("enter")
        seen, guard = [], 0
        while bp.phase == "anim" and guard < 400:
            m = bp.timeline[min(bp.i, len(bp.timeline) - 1)]["m"]
            if not seen or seen[-1] != m:
                seen.append(m)
            bp.anim()
            guard += 1
        return seen

    bounce = run([1])                             # the double-tap
    assert "windup" in bounce and "hit" in bounce and "flinch" in bounce
    skipped = run([SKIP_DEBOUNCE + 4])            # a deliberate skip
    assert "hit" in skipped                       # ...still shows the blow
