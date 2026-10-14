"""The adventure WORLD rebuilt (2026-10-14, Joel: "it was built with an older
llm ... needs to be built from scratch"): 30 maps, one per scene background,
one map = one run (march -> town halfway -> boss), unlocked in order."""
import json
import os
import random

from tuipet import adventure as A, backgrounds, shop
from tuipet.adventure import Adventure, MAPS, MAX_LIVES
from tuipet.pet import Pet

TIER_RANK = {t: i for i, t in enumerate(A.TIERS)}


def _pet(stage_num=100):
    p = Pet.new_egg()
    p._hatch_into_fresh()
    p.evolve_to(stage_num)
    p.energy = p.max_energy
    return p


def test_thirty_maps_one_per_scene_background():
    assert len(MAPS) == 30
    scenes = [m["scene"] for m in MAPS]
    assert len(set(scenes)) == 30                       # no backdrop reused
    assert all(s in backgrounds.NAMES for s in scenes)
    assert len({m["name"] for m in MAPS}) == 30         # every map its own name
    assert MAPS[22]["name"] == "Monster Island"


def test_tiers_climb_in_road_order():
    ranks = [TIER_RANK[m["tier"]] for m in MAPS]
    assert ranks == sorted(ranks)
    assert [sum(1 for m in MAPS if m["tier"] == t) for t in A.TIERS] == [7, 8, 8, 7]


def test_wilds_fit_the_tier_and_kaiju_stay_on_monster_island():
    for i, m in enumerate(MAPS):
        assert m["randoms"], m["name"]
        for e in m["randoms"]:
            gz = 1623 <= e["num"] <= 1650
            assert gz == (i == 22), (m["name"], e["name"])
            if not gz:
                assert e["stage"] == m["tier"], (m["name"], e["name"])


def test_every_boss_is_unique_and_outranks_or_matches_its_road():
    nums = [m["bosses"][0]["num"] for m in MAPS]
    assert len(set(nums)) == 30
    for m in MAPS:
        b = m["bosses"][0]
        assert b["boss"]
        assert TIER_RANK[b["stage"]] >= TIER_RANK[m["tier"]]
    assert MAPS[-1]["bosses"][0]["parade_msg"]           # the last gate ends the road


def test_road_finds_are_food_and_care_only():
    for m in MAPS:
        assert m["find_keys"]
        for k in m["find_keys"]:
            assert shop.CATALOG[k].category in ("Feed", "Cure"), (m["name"], k)


def test_the_town_sits_halfway_and_its_id_is_the_map():
    for i, m in enumerate(MAPS):
        (lo, hi, tid), = m["town_legs"]
        assert tid == i and lo < m["steps"] // 2 <= hi + 1
        assert A.map_tier(tid) == m["tier"]


def test_progress_unlocks_in_order_and_areas_follow():
    p = _pet()
    assert A.unlocked_indices(p) == (0,)
    for i in range(6):
        assert not A.is_map_cleared(p, 1)
        assert A.record_win(p, MAPS[i])
    assert A.is_map_cleared(p, 1) and not A.is_map_cleared(p, 2)
    assert not A.record_win(p, MAPS[0])                # a replay advances nothing
    assert A.frontier(p) == 6


def test_the_boss_reward_pays_once():
    p = _pet()
    run = Adventure(p, MAPS[0])
    got = run.award_drop(run.boss)
    assert got == MAPS[0]["reward"] and p.inventory.get(got[0]) == 1
    A.record_win(p, MAPS[0])
    replay = Adventure(p, MAPS[0])
    assert replay.replay and replay.award_drop(replay.boss) == []
    assert Adventure(p, MAPS[1]).award_drop(MAPS[1]["randoms"][0]) == []   # wilds drop nothing


def test_the_deep_maps_hold_the_human_spirits_and_the_x_program():
    spirits = [k for m in MAPS for k in m["reward"] if k.startswith("human_")]
    assert len(spirits) == len(set(spirits)) == 10
    assert all("x_program" in m["reward"] for m in MAPS if m["tier"] == "Mega")


def test_the_shortcut_opens_the_gate_and_the_rest_kit_rests():
    p = _pet()
    run = Adventure(p, MAPS[0])
    p.inventory = {"shortcut": 1, "rest_kit": 1, "life_recovery": 1}
    p.energy = 0
    run.lives = 1
    assert set(run.held_transports()) == {"shortcut", "rest_kit", "life_recovery"}
    assert run.use_transport("rest_kit") == "rest"
    assert p.energy == p.max_energy // 2 and "rest_kit" not in run.held_transports()
    assert run.use_transport("life_recovery") == "life-recovery" and run.lives == MAX_LIVES
    r = run.use_transport("shortcut")
    assert r == ("boss", run.boss) and run.loc == run.total
    assert run.held_transports() == []


def test_a_whole_run_marches_to_the_boss(monkeypatch):
    p = _pet()
    run = Adventure(p, MAPS[0])
    random.seed(7)
    monkeypatch.setattr(p, "check_stop_travel", lambda: False)
    seen = set()
    for _ in range(500):
        r = run.travel()
        kind = r[0] if isinstance(r, tuple) else r
        seen.add(kind)
        if kind == "encounter":
            run.resolve(True)
        elif kind == "boss":
            break
    assert "boss" in seen and "town" in seen
    assert run.resolve_boss(True) == "won" and run.done


def test_the_map_file_is_the_builders_output():
    """data/adventure_maps.json must be exactly what the builder makes from
    the game's own data -- no hand edits drifting from the rule."""
    import subprocess
    import sys
    root = os.path.join(os.path.dirname(__file__), "..")
    path = os.path.join(root, "src", "tuipet", "data", "adventure_maps.json")
    with open(path, encoding="utf-8") as f:
        before = f.read()
    subprocess.run([sys.executable, os.path.join(root, "tools", "build_adventure_maps.py")],
                   check=True, capture_output=True,
                   env={**os.environ, "PYTHONPATH": os.path.join(root, "src")})
    with open(path, encoding="utf-8") as f:
        assert f.read() == before
    assert len(json.loads(before)) == 30


def test_the_last_map_does_not_promise_a_next_one(monkeypatch):
    from tuipet.adventurescreen import AdventurePanel
    p = _pet()
    p.adv_progress = len(MAPS) - 1
    pan = AdventurePanel(p, zone=MAPS[-1])

    class _Win:
        won = True
    pan._fighting_boss, pan._fighting_enemy = True, pan.adv.boss
    pan.adv.loc = pan.adv.total
    pan._battle_done(_Win())
    assert "road is complete" in pan._home_msg and "new map" not in pan._home_msg
    assert pan._pulse["parade"] and pan._pulse["msg"] == A.FINAL_PARADE_MSG
