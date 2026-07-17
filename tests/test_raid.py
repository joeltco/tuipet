"""The DSprite raid conversion (BASIC VPET 2026-07-16): adventure's slot on
the keymap became the community boss fight, ported from the v0.4.x clone.

Covered here, all four layers:
 * server: rotation, the num-bound damage multiplier, the daily attempt
   ledger, kill-archives-immediately, rank pay + double-claim refusal
 * net: the three raid messages land in LobbyClient state
 * panel: text() smoke in every view state (the panel-smoke-gap rule), the
   10-round volley cutoff reporting raw damage, the claim applying bits /
   items / KO6 / the raids channel
 * sim + eggs: a raid bout writes NOTHING on the pet's record (the clone's
   generate_raid contract), and the old MapComplete rows gate on felled
   raids now (map N -> N+1 bosses)
"""
import json
import os
import sys

import pytest

from tuipet import data, egg, persistence
from tuipet.net import LobbyClient
from tuipet.pet import Pet
from tuipet import raidscreen
from tuipet.raidscreen import RaidPanel, RAID_ROUNDS


def _srv(tmp_path):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    import server
    server.RAID_PATH = str(tmp_path / "raid.json")
    server.RAID = server._load_raid()
    return server


# ---- server: rotation + hit + attempts + claim --------------------------------

def test_rotation_stages_a_pool_boss_and_a_fresh_install_opens_now(tmp_path):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000.0)
    b = srv.RAID["boss"]
    assert b is not None and b["start"] == 1000.0          # no cooldown on first boot
    assert b["hp"] == b["max_hp"] == 80 * srv.RAID_HP_PER_ENERGY
    pool_nums = {p["num"] for p in srv._raid_pool()}
    assert b["num"] in pool_nums
    assert data.record_for(b["num"]).get("stage") == "Mega"


def test_hit_binds_the_multiplier_to_the_card_num(tmp_path):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000.0)
    mega = srv.RAID["boss"]["num"]                          # any Mega: mult x20
    r = srv._raid_hit("joel", 10, mega, now=1001.0)
    assert r["ok"] and r["dealt"] == 10 * srv.RAID_DMG_MULT * 20
    # an unknown/None num fails CLOSED to x1, never x20
    r2 = srv._raid_hit("kai", 10, None, now=1001.0)
    assert r2["ok"] and r2["dealt"] == 10 * srv.RAID_DMG_MULT


def test_the_raw_ceiling_is_the_classic_volley(tmp_path):
    """10 rounds x (BASE_ATTACK 5 + 1) = 60: the honest classic ceiling
    (the clone's 20 fit its own <=2-per-round engine)."""
    srv = _srv(tmp_path)
    assert srv.RAID_MAX_RAW == 60
    srv._raid_rotate(now=1000.0)
    r = srv._raid_hit("joel", 9999, None, now=1001.0)
    assert r["dealt"] == 60 * srv.RAID_DMG_MULT


def test_three_attempts_a_day_then_the_gate_refuses(tmp_path):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000.0)
    for _ in range(srv.RAID_ATTEMPTS_PER_DAY):
        assert srv._raid_hit("joel", 1, None, now=1001.0)["ok"]
    r = srv._raid_hit("joel", 1, None, now=1001.0)
    assert not r["ok"] and "attempts" in r["why"].lower()
    # ...but the next UTC day resets the ledger
    assert srv._raid_hit("joel", 1, None, now=1001.0 + 86400)["ok"]


def test_kill_archives_and_pays_rank_one_exactly_once(tmp_path):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000.0)
    srv.RAID["boss"]["hp"] = 1                              # one hit fells it
    srv._raid_hit("joel", 10, None, now=1001.0)
    assert srv.RAID["history"] and srv.RAID["history"][-1]["defeated"]
    assert srv.RAID["boss"]["start"] > 1001.0               # the next boss is incoming
    rid = srv.RAID["history"][-1]["id"]
    view = srv._raid_view("joel", now=1002.0)
    assert view["award"] and view["award"]["id"] == rid
    r = srv._raid_claim("joel", rid, now=1002.0)
    assert r["ok"] and r["defeated"] and r["rank"] == 1
    assert r["bits"] in (srv.RAID_RANK_BITS[1], int(srv.RAID_RANK_BITS[1] * 1.5))
    assert len(r["items"]) == srv.RAID_RANK_ITEMS[1]
    assert all(k in data.load_vitems() for k in r["items"])
    assert not srv._raid_claim("joel", rid, now=1003.0)["ok"]   # double-claim refused
    # a bystander who never hit it has nothing to claim
    assert not srv._raid_claim("kai", rid, now=1003.0)["ok"]


def test_an_escaped_boss_pays_flat_consolation(tmp_path):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000.0)
    srv._raid_hit("joel", 10, None, now=1001.0)
    end = srv.RAID["boss"]["end"]
    srv._raid_rotate(now=end + 1)                           # the window lapses
    rec = srv.RAID["history"][-1]
    assert not rec["defeated"]
    r = srv._raid_claim("joel", rec["id"], now=end + 2)
    assert r["ok"] and not r["defeated"]
    assert r["bits"] in (srv.RAID_CONSOLATION, int(srv.RAID_CONSOLATION * 1.5))
    assert r["items"] == []


# ---- net: the three messages land -----------------------------------------------

def test_net_raid_messages_land_in_client_state():
    c = LobbyClient("ws://x/", "joel")
    c._handle('{"t": "raid", "boss": {"num": 5}, "attempts": 3}')
    assert c.raid["boss"]["num"] == 5
    c._handle('{"t": "raid_hit", "ok": true, "dealt": 100000}')
    assert c.raid is None                                   # stale view dropped
    c._handle('{"t": "raid_reward", "ok": true, "bits": 500, "items": []}')
    assert c.raid_reward["bits"] == 500


# ---- panel -----------------------------------------------------------------------

class _StubState:
    me_id = 1


class _StubClient:
    def __init__(self):
        self.state = _StubState()
        self.raid = None
        self.raid_reward = None
        self.calls = []

    def raid_get(self):
        self.calls.append(("get",))

    def raid_hit(self, damage, stage):
        self.calls.append(("hit", damage, stage))

    def raid_claim(self, raid_id):
        self.calls.append(("claim", raid_id))


def _pet():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p.vaccine, p.data_power, p.virus = 5, 3, 2
    return p


def _view(mega, hp=1000, start=0.0, now=100.0, attempts=3, award=None):
    return {"t": "raid", "now": now,
            "boss": {"num": mega, "name": "BossMon", "hp": hp, "max_hp": 1000,
                     "start": start, "end": start + 604800},
            "top": [["kai", 2000000]], "you": [2, 150000],
            "attempts": attempts, "award": award}


def _mega():
    return json.load(open("server/raid_pool.json"))[0]["num"]


def _panel():
    pan = RaidPanel(_pet(), None, client=_StubClient())
    return pan


def test_panel_text_smokes_in_every_view_state():
    pan = _panel()
    assert pan.text().plain                                 # no view yet
    pan.anim()                                              # me_id up -> raid_get fires
    assert ("get",) in pan.client.calls
    pan.client.raid = _view(_mega())
    pan.anim()
    plain = pan.text().plain
    assert "BossMon" in plain and "POOL" in plain
    # incoming: the countdown replaces the pool bar
    pan.client.raid = _view(_mega(), start=90000.0, now=100.0)
    assert "INCOMING" in pan.text().plain
    # a waiting purse advertises the claim key
    pan.client.raid = _view(_mega(), award={"id": "9", "boss": "BossMon"})
    assert "purse" in pan.text().plain
    assert pan.strip()


def test_space_needs_a_standing_boss_and_attempts():
    pan = _panel()
    pan.key("space")                                        # no view: just re-asks
    assert pan.sub is None
    pan.client.raid = _view(_mega(), attempts=0)
    pan.key("space")
    assert pan.sub is None and "attempts" in pan.msg.lower()
    pan.client.raid = _view(_mega(), hp=0)
    pan.key("space")
    assert pan.sub is None                                  # a fallen boss takes no hits
    pan.client.raid = _view(_mega())
    pan.key("space")
    assert pan.sub is not None
    assert pan.sub.battle.source == "raid"                  # the record-less bout
    assert pan.sub.battle.enemy_max == raidscreen.RAID_BOSS_HP
    assert pan.sub.text().plain                             # the bout renders too


def test_the_volley_ends_itself_at_ten_rounds_and_reports():
    pan = _panel()
    pan.client.raid = _view(_mega())
    pan.key("space")
    b = pan.sub.battle
    b.round = RAID_ROUNDS
    b.enemy_hp = b.enemy_max - 37                           # 37 raw landed
    pan.sub.phase = "menu"
    pan.anim()
    assert pan.sub is None
    assert ("hit", 37, "Champion") in pan.client.calls


def test_a_raid_bout_writes_nothing_on_the_pet():
    p = _pet()
    before = (p.battles, p.wins, p.energy, p.exercise_today)
    assert p.record_battle(True, {"stage": "Mega"}, source="raid") == ""
    assert (p.battles, p.wins, p.energy, p.exercise_today) == before


def test_claim_pays_bits_items_ko6_and_the_raids_channel():
    pan = _panel()
    p = pan.pet
    p.bits = 100
    pan.client.raid_reward = {"t": "raid_reward", "ok": True, "bits": 5000,
                              "items": ["energy_drink", "premium_meat"],
                              "defeated": True, "rank": 1, "boss": "BossMon"}
    pan.anim()
    assert p.bits == 5100
    assert p.inventory.get("energy_drink") == 1
    assert p.inventory.get("premium_meat") == 1
    assert p.mega_kills == 1                                # the felled boss is KO6
    assert persistence.get_progress()["raids"] == 1
    assert "BossMon" in pan.msg
    # an escaped-boss claim pays but counts nothing
    pan.client.raid_reward = {"t": "raid_reward", "ok": True, "bits": 100,
                              "items": [], "defeated": False}
    pan.anim()
    assert p.bits == 5200 and p.mega_kills == 1
    assert persistence.get_progress()["raids"] == 1


# ---- eggs: the MapComplete re-gate ----------------------------------------------

def _prog(raids=0):
    prog = persistence.get_progress()
    prog["raids"] = raids
    return prog


def test_map_rows_gate_on_felled_raids_now():
    rules = data.load_egg_unlock()
    row = next(r for r in rules.values() if r.get("map") == 0)
    deep = next(r for r in rules.values() if r.get("map") == 4)
    assert not egg._conditions_met(row, _prog(raids=0))
    assert egg._conditions_met(row, _prog(raids=1))
    assert not egg._conditions_met(deep, _prog(raids=4))
    assert egg._conditions_met(deep, _prog(raids=5))


def test_map_rows_tell_the_raid_story():
    rules = data.load_egg_unlock()
    idx = next(i for i, r in rules.items() if r.get("map") == 1)
    assert rules[idx]["desc"] == "Fell 2 raid bosses"
    assert egg.unlock_progress(idx, _prog(raids=1)) == "raid bosses felled 1/2"
    assert egg.unlock_ratio(idx, _prog(raids=1)) == 0.5
