"""The raid boss pins: server rules (rotation, attempts, damage clamp,
rank rewards, consolation) and the client's 10-round attempt."""
import os
import random
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import server as srv  # noqa: E402

from tuipet import battle  # noqa: E402
from tuipet.pet import Pet  # noqa: E402


def _fresh(now):
    srv._raid_rotate(now)
    return srv.RAID["boss"]


def test_first_boss_opens_immediately_then_cooldowns():
    now = 1_000_000.0
    b = _fresh(now)
    assert b["start"] == now                      # a fresh install waits nothing
    assert b["end"] == now + srv.RAID_WINDOW_S
    assert b["hp"] == b["max_hp"] >= 65 * srv.RAID_HP_PER_ENERGY
    # kill it -> the next boss stands 24h off
    b["hp"] = 0
    srv._raid_rotate(now + 10)
    nb = srv.RAID["boss"]
    assert nb["start"] == now + 10 + srv.RAID_COOLDOWN_S
    assert srv.RAID["history"][-1]["defeated"] is True


def test_escape_archives_as_not_defeated():
    now = 2_000_000.0
    b = _fresh(now)
    srv._raid_rotate(now + srv.RAID_WINDOW_S + 1)
    assert srv.RAID["history"][-1]["defeated"] is False
    assert srv.RAID["history"][-1]["boss_name"] == b["name"]


# the multiplier binds to the pet NUM now (a species record's real stage),
# not a forgeable stage STRING (round-3 audit 2026-07-16)
NUM_ULTSU, NUM_ADULT, NUM_PERFECT, NUM_CHILD = 740, 0, 557, 374


def test_attempts_are_three_per_day_and_damage_is_clamped():
    now = 3_000_000.0
    _fresh(now)
    srv.RAID["boss"]["start"] = now               # open the window
    for i in range(3):
        r = srv._raid_hit("joel", 999, NUM_ULTSU, now=now)
        assert r["ok"]
        # raw clamps to 20; the Ult-SU species multiplies x20
        assert r["dealt"] == 20 * srv.RAID_DMG_MULT * 20
    r = srv._raid_hit("joel", 5, NUM_ADULT, now=now)
    assert not r["ok"] and "attempts" in r["why"].lower()
    # a new day refills
    r = srv._raid_hit("joel", 10, NUM_ADULT, now=now + 86_400)
    assert r["ok"] and r["dealt"] == 10 * srv.RAID_DMG_MULT * 2


def test_raid_multiplier_binds_to_num_not_a_forged_stage_string():
    now = 3_500_000.0
    _fresh(now)
    srv.RAID["boss"]["start"] = now
    # a Child pet, and the forge: a stage STRING where the num goes
    child = srv._raid_hit("honest", 20, NUM_CHILD, now=now)
    forge = srv._raid_hit("cheat", 20, "super ultimate", now=now)
    assert child["dealt"] == 20 * srv.RAID_DMG_MULT * 1     # honest x1
    assert forge["dealt"] == 20 * srv.RAID_DMG_MULT * 1     # forge falls to x1


def test_stage_mult_follows_the_source_table():
    assert srv._raid_stage_mult("Adult") == 2
    assert srv._raid_stage_mult("Perfect") == 5
    assert srv._raid_stage_mult("Armor-Hybrid") == 10
    assert srv._raid_stage_mult("Ultimate-Super Ultimate") == 20
    assert srv._raid_stage_mult("Child") == 1
    assert srv._raid_stage_mult("garbage") == 1


def test_kill_pays_by_rank_and_escape_pays_consolation():
    now = 4_000_000.0
    _fresh(now)
    b = srv.RAID["boss"]
    b["start"] = now
    b["hp"] = b["max_hp"] = 100                   # a killable test boss
    srv._raid_hit("first", 20, NUM_ULTSU, now=now)   # overkill
    assert srv.RAID["boss"]["name"]               # rotated to the next boss
    rec = srv.RAID["history"][-1]
    assert rec["defeated"] and "first" in rec["board"]
    a = srv._raid_award("first")
    assert a["rank"] == 1 and a["bits"] == 5000 and a["items"] == 3
    # claim on a weekday pays face value and latches
    wd = now
    while time.localtime(wd).tm_wday >= 5:
        wd += 86_400
    r = srv._raid_claim("first", a["id"], now=wd)
    assert r["ok"] and r["bits"] == 5000 and len(r["items"]) == 3
    assert all(i in srv.RAID_ITEM_POOL for i in r["items"])
    assert not srv._raid_claim("first", a["id"], now=wd)["ok"]

    # an escape pays the flat consolation
    now2 = wd + 10
    srv.RAID["boss"]["start"] = now2
    srv._raid_hit("second", 10, NUM_ADULT, now=now2)
    srv.RAID["boss"]["end"] = now2 - 1            # force the escape
    srv._raid_rotate(now2)
    a2 = srv._raid_award("second")
    assert a2 and not a2["defeated"] and a2["bits"] == 100 and a2["items"] == 0


def test_view_reports_board_and_attempts():
    now = 5_000_000.0
    _fresh(now)
    srv.RAID["boss"]["start"] = now
    srv._raid_hit("ana", 20, NUM_PERFECT, now=now)
    srv._raid_hit("bob", 5, NUM_ADULT, now=now)
    v = srv._raid_view("bob", now=now)
    assert v["top"][0][0] == "ana"
    assert v["you"] == [2, 5 * srv.RAID_DMG_MULT * 2]
    assert v["attempts"] == 2


def test_generate_raid_is_ten_rounds_from_ten_hp():
    me = battle.Side(0, stage="Adult", attribute="Vaccine")
    boss = battle.Side(1, stage="Ultimate-Super Ultimate", attribute="Free")
    rng = random.Random(9).random
    seq, dealt, my_hp = battle.generate_raid(me, boss, rng=rng)
    assert len(seq) <= battle.ROUNDS_RAID
    assert 0 <= dealt <= 2 * battle.ROUNDS_RAID
    assert 0 <= my_hp <= battle.RAID_PLAYER_HP
    assert dealt == sum(d for hit, d, _bh, _bd in seq if hit)


def test_raid_page_gates_and_flow():
    from tuipet import lobbyscreen

    class _Stub:
        def __init__(self):
            self.sent = []
            self.raid = None
            self.raid_reward = None
            self.name = "joel"
            self.state = None
        def raid_get(self): self.sent.append(("get",))
        def raid_hit(self, d, st): self.sent.append(("hit", d, st))
        def raid_claim(self, rid): self.sent.append(("claim", rid))
        def update_pet(self, *a): pass

    pet = Pet.new_egg(egg_type=1)
    pet._hatch_into_fresh()
    pan = lobbyscreen.LobbyPanel.__new__(lobbyscreen.LobbyPanel)
    pan.pet = pet
    pan.client = _Stub()
    pan.raid_fight = None
    pan.raid_note = ""
    pan.bshow = None
    pan.sfx = None
    # sick pets are barred (the source gate)
    pet.sick = True
    assert "sick" in pan._raid_gate()
    pet.sick = False
    assert pan._raid_gate() == ""
    # a live boss: the attack runs 10 rounds and reports the raw damage
    pan.client.raid = {"boss": {"num": pet.num, "name": "Bossmon",
                                "hp": 999, "max_hp": 999, "start": 0,
                                "end": 10 ** 12},
                       "now": 5, "attempts": 3, "top": [], "you": [0, 0],
                       "award": None}
    random.seed(4)
    pan._raid_attack()
    while pan.raid_fight is not None:
        pan.bshow = None
        pan._raid_next_volley()
    hit = [m for m in pan.client.sent if m[0] == "hit"]
    assert len(hit) == 1
    assert 0 <= hit[0][1] <= 20 and hit[0][2] == pet.stage
    # the page renders
    assert pan._text_raid() is not None
