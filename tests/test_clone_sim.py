"""The clone-sim pins: the real-time care model, the growth chart, the HP
race and the credits surface -- every number transcribed from the source
rule set must hold exactly."""
import random
import time

import pytest

from tuipet import battle, data, egg, jogress
from tuipet.pet import (Pet, EVO_TIME, SLEEP_CLOCK, DEATH_MISTAKES,
                        DEATH_AGE, POOP_P, CALL_MINUTES, REPLAY_CAP_MIN,
                        online_reward)


def _awake_pet(stage="Child"):
    p = Pet.new_egg(egg_type=1)
    p._hatch_into_fresh()
    p.stage = stage
    p._hour = lambda: 12          # noon: every stage is awake
    p.stage_minutes = 1
    return p


# ---- the rule constants themselves ----

def test_the_rule_constants_are_the_source_numbers():
    assert EVO_TIME == {"Baby I": 10, "Baby II": 360, "Child": 600,
                        "Adult": 720, "Perfect": 840,
                        "Ultimate-Super Ultimate": 1440}
    assert SLEEP_CLOCK["Baby I"] == (20, 9)
    assert SLEEP_CLOCK["Child"] == (21, 8)
    assert SLEEP_CLOCK["Adult"] == (22, 8)
    assert DEATH_MISTAKES == ((20, 0.0015), (15, 3.75e-4),
                              (10, 7.5e-5), (5, 1.5e-5))
    assert DEATH_AGE == ((25, 3.75e-4), (20, 1.5e-4), (15, 3.75e-5))
    assert POOP_P == 0.002 and CALL_MINUTES == 20 and REPLAY_CAP_MIN == 4320


def test_perfect_care_cannot_die():
    """<5 mistakes, healthy, under age 15: the death roll is literally 0."""
    random.seed(1)
    p = _awake_pet()
    p.care_mistakes = 4
    p.hunger = p.strength = 4
    for _ in range(2000):
        p._sim_minute()
        p.hunger = p.strength = 4       # perfect care
        p.poop = 0
        p.sick = False
    assert not p.dead


def test_hourly_decay_and_the_20_minute_call():
    p = _awake_pet()
    p.stage_minutes = 59
    p.hunger = p.strength = 3
    p._sim_minute()                      # minute 60: the hourly decay
    assert p.hunger == 2 and p.strength == 2
    p.hunger = 0
    for _ in range(CALL_MINUTES - 1):
        p._sim_minute()
        assert p.care_mistakes == 0
        p.poop = 0
    assert p.call_on
    p._sim_minute()                      # the 20th ignored minute
    assert p.care_mistakes == 1
    assert p.call_ignored and not p.call_on   # latched: one mistake per call
    p.hunger = 4                          # feeding clears the latch
    p._sim_minute()
    assert not p.call_ignored


def test_evolution_gate_and_branch_rules():
    p = _awake_pet("Baby I")
    path = p.species_path
    chart = data.load_evo_branches().get(path)
    if not chart:
        pytest.skip("this baby has no chart entry")
    p.care_mistakes = 0
    p.stage_minutes = EVO_TIME["Baby I"]
    p.trainings_cur_stage = 10
    assert p._branch() == "best"
    num = p._maybe_evolve()
    assert num is not None
    assert p.stage == "Baby II"
    assert p.stage_minutes == 0 and p.care_mistakes == 0
    assert p.trainings_cur_stage == 0
    assert p.energy_bonus == 2            # 10 trainings // 5 banked


def test_branch_thresholds_per_stage():
    p = _awake_pet("Child")
    p.care_mistakes = 4
    assert p._branch() == "worst"
    p.care_mistakes = 0
    p.trainings_cur_stage = 25
    assert p._branch() == "best"
    p.trainings_cur_stage = 24
    assert p._branch() == "middle"
    p.stage = "Adult"
    p.battles, p.wins = 40, 0
    assert p._branch() == "best"
    p.stage = "Perfect"
    assert p._branch() == "middle"        # needs > 79 battles
    p.care_mistakes = 3
    assert p._branch() == "worst"


def test_sleep_window_wakes_with_a_full_tank():
    p = _awake_pet("Adult")
    p._hour = lambda: 23                  # bedtime
    p._sim_minute()
    assert p.asleep
    p.energy = 1
    p._hour = lambda: 9                   # morning
    p._sim_minute()
    assert not p.asleep
    assert p.energy == p.max_energy       # the full refill


def test_hatch_table_is_honoured():
    for et in (0, 5, 20):
        p = Pet.new_egg(egg_type=et)
        p._hatch_into_fresh()
        assert p.stage == "Baby I"
        assert p.num == egg.hatch_target(et)


# ---- battle ----

def test_hit_chance_components():
    a = battle.Side(0, stage="Child", attribute="Vaccine",
                    strength=4, strength_max=4, hunger=4, hunger_max=4,
                    energy=5, energy_max=5, base_weight=10, weight=10)
    b = battle.Side(1, stage="Child", attribute="Virus",
                    strength=0, strength_max=4, hunger=0, hunger_max=4,
                    energy=0, energy_max=5, base_weight=10, weight=40)
    # a: base .3 + condition (.05+.05+.05+.1) + triangle .05 = 0.6
    assert abs(a.hit_chance(b) - 0.6) < 1e-9
    # b: base .3 + condition (-.05*3 - .1) - .05 = 0.0
    assert abs(b.hit_chance(a) - 0.0) < 1e-9


def test_generate_is_deterministic_and_bounded():
    a = battle.Side(0, stage="Child", attribute="Free")
    b = battle.Side(1, stage="Child", attribute="Free")
    r1 = random.Random(42).random
    r2 = random.Random(42).random
    s1 = battle.generate(a, b, rounds=5, rng=r1)
    s2 = battle.generate(a, b, rounds=5, rng=r2)
    assert s1 == s2                        # the seeded engine is replayable
    seq, my_hp, foe_hp = s1
    assert len(seq) <= 5
    assert 0 <= my_hp <= 5 and 0 <= foe_hp <= 5


def test_damage_follows_the_trained_hit_type():
    mega = battle.Side(0, stage="Child", hit_type="mega")
    n = sum(mega.roll_damage(random.Random(7).random) for _ in range(1))
    # exact one-draw pins are noise; pin the distribution instead
    rng = random.Random(7)
    doubles = sum(1 for _ in range(1000) if mega.roll_damage(rng.random) == 2)
    assert doubles > 850                   # mega: ~90% double
    miss = battle.Side(0, stage="Child", hit_type="miss")
    rng = random.Random(7)
    doubles = sum(1 for _ in range(1000) if miss.roll_damage(rng.random) == 2)
    assert doubles < 300                   # miss: ~20% double


def test_999_battles_forces_mega():
    vet = battle.Side(0, stage="Child", hit_type="miss", battles=999)
    assert vet.hit_type == "mega"


def test_online_purse_values(monkeypatch):
    from tuipet import pet as pet_mod
    # conftest pins weekend_bonus to 1.0 -- restore the real one here
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
    p = _awake_pet()
    p.energy = 20
    p.record_battle(True)
    assert p.trainings_cur_stage == 2 and p.total_trainings == 2
    p.record_battle(True, online=True)
    assert p.trainings_cur_stage == 2      # online wins pay bits, not training


# ---- items / fusion / credits ----

def test_armor_evolution_via_crest_egg():
    armors = data.load_armor_evos()
    byp = data.num_by_path()
    child_path = next((k for k, v in armors.items()
                       if v and v[0]["result"] in byp and k in byp), None)
    if child_path is None:
        pytest.skip("no armor evolutions resolvable")
    p = Pet(num=byp[child_path], stage="Child", attribute="Free")
    e = armors[child_path][0]
    assert p.item_evolve(e["itemId"]) == byp[e["result"]]
    assert p.stage == "Armor-Hybrid"


def test_revive_floppy_raises_the_dead():
    p = _awake_pet()
    p._die("test")
    p.add_item("revive_floppy")
    out = p.use_item("revive_floppy")
    assert "LIVES" in out and not p.dead
    assert "revive_floppy" not in p.inventory


def test_credits_surface_names_artists():
    from tuipet.creditscreen import CreditsPanel, LEADS
    rows = CreditsPanel(_awake_pet()).rows
    body = " ".join(t for t, _ in rows)
    for lead in LEADS:
        assert lead in body
    assert "community" in body
