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
from tuipet.raidscreen import RaidPanel


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
    # adaptive HP (2026-07-18): a fresh install opens at the FLOOR -- a
    # small community can actually fell its first boss
    assert b["hp"] == b["max_hp"] == srv.RAID_HP_FLOOR
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


def test_the_raw_ceiling_is_the_clone_volley(tmp_path):
    """10 rounds x 2 damage = 20: the clone's own ceiling, restored when the
    0.5 HP race replaced the classic engine (2026-07-17)."""
    srv = _srv(tmp_path)
    assert srv.RAID_MAX_RAW == 20
    srv._raid_rotate(now=1000.0)
    r = srv._raid_hit("joel", 9999, None, now=1001.0)
    assert r["dealt"] == 20 * srv.RAID_DMG_MULT


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
    from tuipet import shop
    assert all(k in shop.CATALOG for k in r["items"])   # real TUIPET prizes
    assert not srv._raid_claim("joel", rid, now=1003.0)["ok"]   # double-claim refused
    # a bystander who never hit it has nothing to claim
    assert not srv._raid_claim("kai", rid, now=1003.0)["ok"]


def test_an_escaped_boss_pays_by_contribution(tmp_path):
    """Adaptive arc 2026-07-18: the flat 100 told a top contributor their
    week meant nothing.  Escape pay scales with your share of the pool,
    capped below rank-3 defeated money."""
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000.0)
    srv._raid_hit("joel", 10, None, now=1001.0)             # a token scratch
    end = srv.RAID["boss"]["end"]
    srv._raid_rotate(now=end + 1)                           # the window lapses
    rec = srv.RAID["history"][-1]
    assert not rec["defeated"]
    r = srv._raid_claim("joel", rec["id"], now=end + 2)
    assert r["ok"] and not r["defeated"] and r["items"] == []
    floor = srv.RAID_CONSOLATION
    assert floor <= r["bits"] <= int(srv.RAID_RANK_BITS[3] * 1.5)
    # a 20%+ contributor earns the escape CAP (rank-3 defeated money)
    srv2 = _srv(tmp_path / "b")
    srv2.RAID = srv2._load_raid()
    srv2._raid_rotate(now=1000.0)
    srv2.RAID["boss"]["max_hp"] = 1000
    srv2.RAID["board"]["kai"] = {"damage": 400, "ts": 1001.0}
    end2 = srv2.RAID["boss"]["end"]
    srv2._raid_rotate(now=end2 + 1)
    r2 = srv2._raid_claim("kai", srv2.RAID["history"][-1]["id"], now=end2 + 2)
    assert r2["bits"] in (srv2.RAID_RANK_BITS[3], int(srv2.RAID_RANK_BITS[3] * 1.5))


def test_adaptive_hp_tracks_the_community(tmp_path):
    """Felled -> the next bar rises x1.5; escaped -> the next pool is sized
    to ~what the community actually dealt; both clamped [floor, cap]."""
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000.0)
    assert srv.RAID["boss"]["max_hp"] == srv.RAID_HP_FLOOR
    srv.RAID["boss"]["hp"] = 1                              # fell it
    srv._raid_hit("joel", 10, None, now=1001.0)
    grown = srv.RAID["boss"]["max_hp"]
    assert grown == int(srv.RAID_HP_FLOOR * srv.RAID_GROW)
    # now let one escape after modest damage: the next fits the output
    srv.RAID["boss"]["start"] = 1002.0
    srv.RAID["board"] = {"joel": {"damage": 6_000_000, "ts": 1003.0}}
    srv._raid_rotate(now=srv.RAID["boss"]["end"] + 1)
    fitted = srv.RAID["boss"]["max_hp"]
    assert fitted == max(srv.RAID_HP_FLOOR, int(6_000_000 * srv.RAID_FIT))
    # the ceiling holds whatever the history says
    srv.RAID["history"][-1] = {"id": "x", "boss_name": "B", "num": 1,
                               "defeated": True, "ended": 1.0,
                               "max_hp": srv.RAID_HP_CAP,
                               "board": {}}
    assert srv._adaptive_hp() == srv.RAID_HP_CAP


def test_weekend_bonus_runs_on_utc(tmp_path):
    """One day-clock: attempts reset at UTC midnight and the weekend x1.5
    keys off UTC too (the localtime split was invisible skew)."""
    import inspect
    srv = _srv(tmp_path)
    src = inspect.getsource(srv._raid_claim)
    assert "gmtime" in src and "localtime" not in src


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

    def raid_hit(self, damage):
        self.calls.append(("hit", damage))

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
    # a waiting purse advertises the claim key (it shares the context line
    # with the status message on the 40-tick beat; raid-menu fix 2026-07-19)
    pan.client.raid = _view(_mega(), award={"id": "9", "boss": "BossMon"})
    pan.frame_i = 40                            # the purse's beat
    assert "purse" in pan.text().plain
    pan.frame_i = 0                             # the message's beat
    assert pan.msg in pan.text().plain
    # the whole page holds the 12-row LCD in every state (the old stacked
    # layout ran 14-15 rows and the box clipped the tail)
    for view in (_view(_mega()), _view(_mega(), start=90000.0, now=100.0),
                 _view(_mega(), award={"id": "9", "boss": "BossMon"})):
        pan.client.raid = view
        rows = pan.text().plain.rstrip("\n").split("\n")   # note()'s trailing \n
        assert len(rows) <= 12
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
    assert pan.sub is not None and pan.sub.raid             # the RaidBout replay
    assert pan.sub.text().plain                             # the bout renders too


def test_the_raid_bout_reports_its_dealt_damage():
    """0.5 BATTLE (2026-07-17): the attempt is the clone's generate_raid --
    the panel replays it, and closing the result reports `dealt`."""
    import random
    random.seed(3)
    pan = _panel()
    pan.client.raid = _view(_mega())
    pan.key("space")
    pan.sub.key("space")                                    # skip the intro
    pan.sub.bar = (pan.sub.mega_lo + pan.sub.mega_hi) // 2
    pan.sub.key("space")                                    # lock: RaidBout builds
    bout = pan.sub.battle
    assert type(bout).__name__ == "RaidBout"
    for _ in range(3000):
        pan.sub.anim()
        if pan.sub.phase == "result":
            break
    assert pan.sub.phase == "result"
    pan.key("space")                                        # close -> report
    assert pan.sub is None
    if bout.dealt:
        assert ("hit", bout.dealt) in pan.client.calls


def test_a_raid_bout_writes_nothing_on_the_pet():
    from tuipet import battle as battle_mod
    import random
    random.seed(3)
    p = _pet()
    before = (p.battles, p.wins, p.exercise_today)
    bout = battle_mod.RaidBout(p, {"num": _mega(), "stage": "Mega", "boss": True})
    while not bout.over:
        bout.play_round()
    assert (p.battles, p.wins, p.exercise_today) == before


def test_claim_pays_bits_items_ko6_and_the_raids_channel():
    pan = _panel()
    p = pan.pet
    p.bits = 100
    pan.client.raid_reward = {"t": "raid_reward", "ok": True, "bits": 5000,
                              "items": ["energy_drink", "steak"],
                              "defeated": True, "rank": 1, "boss": "BossMon"}
    pan.anim()
    assert p.bits == 5100
    assert p.inventory.get("energy_drink") == 1
    assert p.inventory.get("steak") == 1
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
    deep = next(r for r in rules.values() if r.get("map") == 3)
    assert not egg._conditions_met(row, _prog(raids=0))
    assert egg._conditions_met(row, _prog(raids=1))
    assert not egg._conditions_met(deep, _prog(raids=3))
    assert egg._conditions_met(deep, _prog(raids=4))


def test_map_rows_tell_the_raid_story():
    rules = data.load_egg_unlock()
    idx = next(i for i, r in rules.items() if r.get("map") == 1)
    assert rules[idx]["desc"] == "Fell 2 raid bosses"
    assert egg.unlock_progress(idx, _prog(raids=1)) == "raid bosses felled 1/2"
    assert egg.unlock_ratio(idx, _prog(raids=1)) == 0.5


def test_the_panel_reports_honestly_and_stays_live():
    """Raid review 2026-07-18: (1) the report line stays NEUTRAL until the
    gate's ack -- a credit speaks the board number, a refusal says so;
    (2) the exit summary speaks the GATE's credited total; (3) the panel
    refetches the view on a cadence instead of freezing its timers; (4) the
    cadence line promises the x1.5 the relay actually pays, never 2x."""
    import inspect
    from types import SimpleNamespace
    from tuipet.raidscreen import RaidPanel

    calls = []
    client = SimpleNamespace(state=SimpleNamespace(me_id=1),
                             raid={"boss": {"num": 1, "name": "B", "hp": 1,
                                            "start": 0, "end": 9e9},
                                   "now": 1.0, "board": [], "attempts": 3},
                             raid_reward=None, last_hit=None,
                             raid_get=lambda: calls.append("get"),
                             raid_hit=lambda d: calls.append(("hit", d)))
    pan = RaidPanel.__new__(RaidPanel)
    pan.pet = SimpleNamespace(stage="Mega", bits=0)
    pan.sub = None
    pan.frame_i = 0
    pan.sfx = None
    pan.msg = ""
    pan._dealt = 0
    pan._credited = 0
    pan.client = client
    pan._asked = True

    # neutral report, then the ack credits
    pan._report(SimpleNamespace(dealt=12))
    assert "reporting" in pan.msg and "!" not in pan.msg
    client.last_hit = {"dealt": 1_200_000}
    pan.anim()
    assert "credits 1,200,000" in pan.msg and pan._credited == 1_200_000
    # a refused ack surfaces instead of leaving "reported!" standing
    client.last_hit = {}
    pan.anim()
    assert "refused" in pan.msg
    # exit speaks the gate's number
    done, note = pan.key("escape")
    assert done == "done" and "1,200,000" in note
    # the cadence poll: 50 frames -> at least one refetch
    calls.clear()
    for _ in range(51):
        pan.anim()
    assert "get" in calls, "the open panel must keep the view live"
    # and the promise matches the payout (the cadence line moved into
    # _context_line with the 12-row layout, raid-menu fix 2026-07-19)
    src = inspect.getsource(RaidPanel._context_line)
    assert "weekend claims pay 1.5x" in src and "weekend pays 2x" not in src


def test_claim_key_takes_both_cases():
    """C claims with or without shift/caps, like the lobby's letter keys
    (grammar sweep 2026-07-18: lowercase-only ate the caps-lock press)."""
    for key in ("c", "C"):
        pan = _panel()
        pan.client.raid = _view(_mega(), award={"id": 7})
        pan.key(key)
        assert ("claim", 7) in pan.client.calls, key


def test_the_boss_stands_unclipped(monkeypatch):
    """The reduced 8-row scene must NOT wear the 24px-window clip — it
    chopped the top 6px off every boss (Joel 2026-07-19: 'raid monster
    sprites are getting cut off')."""
    import tuipet.raidscreen as rs
    seen = {}
    real = rs.render_scene

    def spy(placements, cols, rows, *a, **kw):
        seen["rows"], seen["clip"] = rows, kw.get("clip")
        seen["heights"] = [len(p[0]) for p in placements]
        return real(placements, cols, rows, *a, **kw)

    monkeypatch.setattr(rs, "render_scene", spy)
    pan = _panel()
    pan.client.raid = _view(_mega())
    pan.text()
    assert seen["clip"] is None                      # no 24px-window clip
    assert all(h <= seen["rows"] * 2 for h in seen["heights"])   # fits its band


def test_the_ready_bar_is_the_training_sprite():
    """One canon timing bar (Joel 2026-07-19: 'the slide bar should be the
    same sprite as the training slide bar'): the drill delegates to
    strikefx.timing_bar, and the battle/raid ready page renders that pixel
    bar over the arena — the old text-glyph track is gone."""
    from tuipet import strikefx
    from tuipet.training import TrainingPanel
    pan = _panel()
    pan.client.raid = _view(_mega())
    pan.key("space")                                 # open the bout
    pan.sub.key("space")                             # skip the intro
    assert pan.sub.phase == "ready"
    plain = pan.sub.text().plain
    assert len(plain.split("\n")) == 12              # full-LCD scene page
    assert "◆" not in plain and "mega" not in plain  # the glyph track is gone
    drill = TrainingPanel(pan.pet)
    drill.bar = 7
    assert drill._bar_overlay() == strikefx.timing_bar(
        7, drill.mega_lo, drill.mega_hi)             # one pixel-set, shared


def test_weekend_note_follows_the_servers_clock(monkeypatch):
    """The relay pays x1.5 on UTC weekends; the cadence note must key off
    the server's own `now`, not the player's local calendar (cup audit
    2026-07-19: at week edges the local clock lied both ways)."""
    import calendar as _cal
    import datetime as _dt
    pan = _panel()
    utc_sat = _cal.timegm(_dt.datetime(2026, 7, 25, 3, 0).timetuple())
    utc_mon = _cal.timegm(_dt.datetime(2026, 7, 27, 3, 0).timetuple())
    for now, expect in ((utc_sat, True), (utc_mon, False)):
        v = _view(_mega(), start=0.0, now=now)
        v["boss"]["end"] = now + 86400
        pan.client.raid = v
        pan.msg = ""
        line = pan._context_line(v, v["boss"])
        assert ("weekend claims pay 1.5x" in line) is expect, (now, line)


# ---- round 29 pins (raid screen tidy, 2026-07-19) --------------------------

def test_the_refusal_speaks_the_gates_why():
    """The ack carries `why` (fallen boss OR spent attempts) -- the old
    hardcoded "boss is gone" guessed wrong on stale-view attempt races."""
    pan = _panel()
    pan.client.raid = _view(_mega())
    pan.client.last_hit = {"t": "raid_hit", "ok": False,
                           "why": "No attempts left today."}
    pan.anim()
    assert pan.msg == "No attempts left today."
    # and no client-side refetch: the gate re-sends the view with the ack
    assert ("get",) not in pan.client.calls[1:]


def test_the_walk_away_is_not_a_whiff():
    """ESC before the bell rolls no volley and spends nothing -- the old
    "Not a scratch" called it a miss."""
    pan = _panel()
    pan.client.raid = _view(_mega())
    pan.key("space")                                    # into the bout
    r = pan.sub.key("space")                            # skip the intro
    assert pan.sub.phase == "ready"
    pan.key("escape")                                   # walk away at the bar
    assert pan.sub is None
    assert "scratch" not in pan.msg
    assert "attempt keeps" in pan.msg
    assert not any(c[0] == "hit" for c in pan.client.calls)


def test_unranked_shows_a_dash_not_rank_zero():
    pan = _panel()
    v = _view(_mega())
    v["you"] = [0, 0]                                   # not on the board yet
    pan.client.raid = v
    assert "you —" in pan.text().plain
    assert "#0" not in pan.text().plain
    v["you"] = [2, 150000]                              # ranked: the number
    pan.client.raid = None
    pan.client.raid = v
    assert "you #2" in pan.text().plain


def test_the_loading_page_keeps_its_keys_on_the_strip():
    """One layout language per screen family: the loaded page carries keys
    on the strip only, and now the loading page does too."""
    pan = _panel()
    assert "ESC" not in pan.text().plain                # no in-LCD footer
    assert "ESC" in pan.strip()                         # the strip has them


def test_the_weekend_note_names_the_claim():
    import time as _t
    pan = _panel()
    v = _view(_mega())
    # aim `now` at a UTC Saturday so the server-clock note fires
    now = 100.0
    while _t.gmtime(now).tm_wday < 5:
        now += 86400
    v["now"] = now
    v["boss"]["end"] = now + 200000
    pan.client.raid = v
    pan.msg = ""                                        # let the cadence line show
    line = pan._context_line(v, v["boss"])
    assert "weekend claims pay 1.5x" in line


def test_raid_hit_wire_carries_no_stage():
    """The gate binds the multiplier to the roster card's num; the stage
    string was dead wire weight."""
    c = LobbyClient("ws://x/", "joel")
    sent = []
    c._send = lambda m: sent.append(m)
    c.raid_hit(40)
    assert sent == [{"t": "raid_hit", "damage": 40}]
