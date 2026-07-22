"""The 0.5 battle — the precomputed HP race (ported 2026-07-17; pins carried
from the clone's test_clone_sim battle block, adapted to classic stages)."""
import random

from tuipet import battle
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_hit_chance_components():
    a = battle.Side(0, stage="Rookie", attribute="Vaccine",
                    strength=4, strength_max=4, hunger=4, hunger_max=4,
                    energy=5, energy_max=5, base_weight=10, weight=10)
    b = battle.Side(1, stage="Rookie", attribute="Virus",
                    strength=0, strength_max=4, hunger=0, hunger_max=4,
                    energy=0, energy_max=5, base_weight=10, weight=40)
    # a: base .3 + condition (.05+.05+.05+.1) + triangle .05 = 0.6
    assert abs(a.hit_chance(b) - 0.6) < 1e-9
    # b: base .3 + condition (-.05*3 - .1) - .05 = 0.0
    assert abs(b.hit_chance(a) - 0.0) < 1e-9


def test_stage_rank_shifts_the_odds():
    rook = battle.Side(0, stage="Rookie", attribute="Free")
    mega = battle.Side(1, stage="Mega", attribute="Free")
    assert abs((mega.hit_chance(rook) - rook.hit_chance(mega)) - 0.6) < 1e-9


def test_generate_is_deterministic_and_bounded():
    a = battle.Side(0, stage="Rookie", attribute="Free")
    b = battle.Side(1, stage="Rookie", attribute="Free")
    s1 = battle.generate(a, b, rounds=5, rng=random.Random(42).random)
    s2 = battle.generate(a, b, rounds=5, rng=random.Random(42).random)
    assert s1 == s2                        # the seeded engine is replayable
    seq, my_hp, foe_hp = s1
    assert len(seq) <= 5
    assert 0 <= my_hp <= 5 and 0 <= foe_hp <= 5


def test_damage_follows_the_trained_hit_type():
    mega = battle.Side(0, stage="Rookie", hit_type="mega")
    rng = random.Random(7)
    doubles = sum(1 for _ in range(1000) if mega.roll_damage(rng.random) == 2)
    assert doubles > 850                   # mega: ~90% double
    miss = battle.Side(0, stage="Rookie", hit_type="miss")
    rng = random.Random(7)
    doubles = sum(1 for _ in range(1000) if miss.roll_damage(rng.random) == 2)
    assert doubles < 300                   # miss: ~20% double


def test_999_battles_forces_mega():
    vet = battle.Side(0, stage="Rookie", hit_type="miss", battles=999)
    assert vet.hit_type == "mega"


def test_online_purse_values(monkeypatch):
    from tuipet import pet as pet_mod
    import time
    monkeypatch.setattr(pet_mod, "weekend_bonus", pet_mod._weekend_mult)
    base = time.mktime((2026, 7, 6, 12, 0, 0, 0, 0, -1))
    week = next(base + d * 86400 for d in range(7)
                if time.localtime(base + d * 86400).tm_wday == 0)
    sat = next(base + d * 86400 for d in range(7)
               if time.localtime(base + d * 86400).tm_wday == 5)
    assert pet_mod.online_reward(True, now=week) == 200
    assert pet_mod.online_reward(False, now=week) == 100
    assert pet_mod.online_reward(False, draw=True, now=week) == 150
    assert pet_mod.online_reward(True, now=sat) == 300


def test_local_battle_trains_and_online_does_not():
    p = _pet()
    p.energy = 20
    p.record_battle(True, {"num": 4, "stage": "Champion", "attribute": "Data"})
    assert p.stage_trainings == 2
    p.record_battle(True, {"num": 4, "stage": "Champion", "attribute": "Data"},
                    online=True)
    assert p.stage_trainings == 2          # online wins pay bits, not training


def test_progression_channels_survive_the_race():
    """The classic keepers inside the 0.5 record: battle_log, KO6 (never in
    PvP), stage-rank levels_fought, and the win's +1 power in the foe's
    attribute (the corpus stat gates feed on it)."""
    p = _pet(vaccine=5, data_power=3, virus=2)
    mega = {"num": 964, "stage": "Mega", "attribute": "Virus"}
    p.record_battle(True, mega)
    assert p.battle_log[-1] == 1 and p.mega_kills == 1
    assert p.levels_fought[-1] == 6        # stage rank IS the level now
    assert p.virus == 3                    # +1 in the foe's attribute
    p.record_battle(True, mega, online=True)
    # L17 ruling (Joel 2026-07-20, option a): online is progression-neutral —
    # KO6 stays still, and so do wins/battles/battle_log/stage_battles
    assert p.mega_kills == 1 and p.wins == 1 and p.battles == 1
    p.record_battle(False, mega)
    assert p.battle_log[-1] == 0 and p.wins == 1


def test_raid_bout_reports_damage_and_records_nothing():
    p = _pet()
    b0, w0 = p.battles, p.wins
    random.seed(3)
    bout = battle.RaidBout(p, {"num": 964, "name": "Boss", "stage": "Mega",
                               "boss": True})
    while not bout.over:
        bout.play_round()
    assert bout.dealt >= 0 and bout.enemy_hp == battle.HP   # the bar never moves
    assert (p.battles, p.wins) == (b0, w0)                  # nothing recorded


def test_the_panel_bar_locks_and_replays_the_race():
    from tuipet.battlescreen import BattlePanel
    random.seed(5)
    p = _pet()
    pan = BattlePanel(p, {"num": 4, "name": "X", "stage": "Champion",
                          "attribute": "Data"})
    pan.key("space")                       # skip the intro
    assert pan.phase == "ready"
    for _ in range(6):
        pan.anim()                         # the bar sweeps
    pan.bar = (pan.mega_lo + pan.mega_hi) // 2
    pan.key("space")                       # lock -> the race builds
    assert pan.battle is not None and p.saved_hit_type == "mega"
    for _ in range(2000):
        pan.anim()
        assert pan.text().plain is not None
        if pan.phase == "result":
            break
    assert pan.phase == "result"
    assert pan.key("space") == ("done", pan.battle)


# --- combat feedback + the bar's real stake (gameplay polish #1/#3/#5) -------

def _side(**kw):
    d = dict(stage="Rookie", attribute="Free", strength=4, strength_max=4,
             hunger=4, hunger_max=4, energy=5, energy_max=5,
             base_weight=10, weight=10)
    d.update(kw)
    return battle.Side(0, **d)


def test_the_saved_form_steadies_or_shakes_the_aim():
    """#3: the timing bar's grade only ever tiered damage EV while the
    fight was decided by hit_chance -- the one interactive moment barely
    moved outcomes.  A mega now adds 0.05 accuracy, a miss costs it."""
    foe = _side()
    normal = _side().hit_chance(foe)
    mega = _side(hit_type="mega").hit_chance(foe)
    miss = _side(hit_type="miss").hit_chance(foe)
    assert abs(mega - normal - 0.05) < 1e-9
    assert abs(normal - miss - 0.05) < 1e-9


def test_coach_line_names_the_biggest_fixable_drag():
    """#1: precedence = fixability (condition tonight > rank > drills)."""
    foe = _side()
    assert "weight" in battle.coach_line(_side(weight=25), foe)
    assert "hungry" in battle.coach_line(_side(hunger=1), foe)
    assert "energy" in battle.coach_line(_side(energy=1), foe)
    assert "effort" in battle.coach_line(_side(strength=1), foe)
    assert "outranked" in battle.coach_line(_side(), _side(stage="Mega"))
    assert "drills" in battle.coach_line(_side(), foe)   # nothing else drags
    maxed = _side(trainings_cur=999, trainings_total=9999)
    assert battle.coach_line(maxed, foe) == ""           # a clean loss is luck


def test_a_true_draw_is_flagged():
    """#5: equal survivors counted as a silent loss -- the flag lets the
    result card SAY so."""
    me, foe = _side(), _side()
    b = battle.Battle(me, {"num": 100})
    b.pet_hp = b.enemy_hp = 2
    b.over = False
    b._finish()
    assert b.drawn and not b.won
    b2 = battle.Battle(me, {"num": 100})
    b2.pet_hp, b2.enemy_hp = 3, 2
    b2.over = False
    b2._finish()
    assert not b2.drawn and b2.won


def test_the_result_note_tells_margin_draw_or_why():
    """#1+#5 on the card: win = HP to spare, draw = the rule, loss = the
    coach line."""
    from tuipet.battlescreen import BattlePanel
    p = _pet()
    pan = BattlePanel(p, enemy={"num": 100})
    pan.battle = battle.Battle(_side(), {"num": 100})
    pan.battle.over = True
    pan.won = True
    pan.battle.pet_hp = 1
    assert "whisker" in pan._result_note()
    pan.battle.pet_hp = 4
    assert "4 HP to spare" in pan._result_note()
    pan.won = False
    pan.battle.drawn = True
    assert "counts as a loss" in pan._result_note()
    pan.battle.drawn = False
    pan.battle.me = _side(hunger=1)
    pan.battle.foe = _side()
    assert "hungry" in pan._result_note()
