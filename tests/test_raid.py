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
   generate_raid contract) -- but a THROWN volley bills the BODY at the
   report seam (Joel 2026-07-28: "bill the body only", the L17 online
   shape) -- and the old MapComplete rows gate on felled raids now
   (map N -> N+1 bosses)
"""
import json
import os
import sys


from tuipet import data, egg, persistence
from tuipet.net import LobbyClient
from tuipet.pet import Pet
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
    login_failed = None
    error = None


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


def _view(mega, hp=1000, start=0.0, now=100.0, attempts=3, award=None,
          you=(2, 150000), top=(("kai", 2000000),)):
    return {"t": "raid", "now": now,
            "boss": {"num": mega, "name": "BossMon", "hp": hp, "max_hp": 1000,
                     "start": start, "end": start + 604800},
            "top": [list(t) for t in top], "you": list(you),
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
    # the LCD is PURE SCENE since the uncramp (2026-07-23): the boss +
    # ONE context line; POOL/standing/tries live on the status card
    assert "BossMon" in plain and "POOL" not in plain
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
    for _ in range(6):
        pan.sub.anim()                                      # past the mash-arm window
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


def test_the_pool_break_plays_the_win_fanfare():
    """The break is an EDGE, never a state: a felled boss archives on the
    felling hit (_raid_hit rotates immediately), so no view ever shows hp 0.
    The panel reads the kill as boss-changed-with-time-left; an escape
    (rotation past `end`) stays quiet (Joel 2026-07-26: win.wav -> the
    pool break)."""
    pan = _panel()
    pan.client.raid = _view(_mega(), hp=700, start=0.0, now=100.0)
    pan.anim()                                              # record the standing boss
    pan.sfx = None
    # the kill: a NEW boss (different start) while the old window had time
    pan.client.raid = _view(_mega(), hp=1000, start=5000.0, now=200.0)
    pan.anim()
    assert pan.sfx == "win" and "broken" in pan.msg
    pan.sfx = None
    pan.anim()                                              # same boss again: one fanfare only
    assert pan.sfx is None


def test_the_kill_holds_a_defeat_moment_then_hands_off_to_the_claim():
    """The felled boss owns the arena for the hold (Joel 2026-07-28:
    "wheres the defeat an8mations???? why did it just blink over to the
    next boss") -- the server archives on the felling blow, so without the
    hold the incoming boss replaced the kill in one frame.  The hold ends
    on the claim nudge: the purse ("what did i win???") pays on C."""
    pan = _panel()
    pan.client.raid = _view(_mega(), hp=700, start=0.0, now=100.0)
    pan.anim()                                              # record the standing boss
    v2 = _view(_mega(), hp=1000, start=5000.0, now=200.0,
               award={"id": "r1", "boss": "BossMon", "bits": 9000,
                      "items": 1, "defeated": True, "rank": 1})
    v2["boss"]["name"] = "NextMon"
    pan.client.raid = v2
    pan.anim()                                              # the kill edge
    assert pan._fell is not None
    plain = pan.text().plain
    # the FALLEN boss holds the stage and the fall line holds the note --
    # the incoming boss waits its turn
    assert "BossMon" in plain and "NextMon" not in plain
    assert "falls — the pool is broken!" in plain
    for _ in range(41):                                     # ~4s at the anim beat
        pan.anim()
    assert pan._fell is None
    assert "press C to claim" in pan.msg and pan.sfx == "confirm"
    assert "NextMon" in pan.text().plain                    # the stage hands over


def test_the_claim_reveal_pins_the_prize_line_and_cheers_the_pet():
    """The prize toast printed once and the context alternation talked over
    it (Joel 2026-07-28: "i didnt know what i got last time either") -- a
    felled claim now holds the PET on the arena in its victory cheer with
    the full prize line pinned for ~12s.  An escaped claim pins its
    consolation line but leaves the stage alone."""
    pan = _panel()
    pan.pet.name = "Blitz"
    pan.client.raid = _view(_mega(), hp=700, start=0.0, now=100.0)
    pan.anim()
    pan.client.raid_reward = {"ok": True, "bits": 5000, "items": ["vitamin"],
                              "defeated": True, "rank": 1, "boss": "Sleipmon X"}
    pan.anim()
    assert pan._won is not None and pan._won[1] is True
    plain = pan.text().plain
    assert "Blitz" in plain                       # the champion owns the stage
    assert "Rank 1: 5000b" in plain               # the head of the line shows
    assert "Vitamin" in pan.msg                   # the FULL line marquees
    for _ in range(115):                          # the whole hold: the prize
        pan.anim()                                # line stays pinned -- the
        assert "weekly boss" not in pan.text().plain   # cadence never talks over
        assert "Rank 1: 5000b" in pan.msg
    for _ in range(6):
        pan.anim()
    assert pan._won is None                       # the reveal lets go
    assert "Blitz" not in pan.text().plain
    # the escaped claim: pinned line, no cheer takeover
    pan.client.raid_reward = {"ok": True, "bits": 100, "defeated": False}
    pan.anim()
    assert pan._won is not None and pan._won[1] is False
    plain = pan.text().plain
    assert "consolation" in plain and "Blitz" not in plain


def test_an_escape_rotation_stays_quiet():
    pan = _panel()
    pan.client.raid = _view(_mega(), hp=700, start=0.0, now=100.0)
    pan.anim()                                              # end = start + 604800
    pan.sfx = None
    # the escape: the new boss arrives only AFTER the old window closed
    pan.client.raid = _view(_mega(), hp=1000, start=700000.0, now=650000.0)
    pan.anim()
    assert pan.sfx is None and "broken" not in pan.msg


def test_a_raid_bout_writes_nothing_on_the_pet():
    """The BOUT OBJECT stays pure (the clone's generate_raid contract):
    replaying it touches no counter AND no body stat.  The body bill lives
    at the panel's report seam alone (Joel 2026-07-28 "bill the body
    only" -- see test_a_thrown_volley_bills_the_body_only), so a
    precompute, a preview or a test replay can never double-bill."""
    from tuipet import battle as battle_mod
    import random
    random.seed(3)
    p = _pet()
    before = (p.battles, p.wins, p.exercise_today, p.energy, p.weight)
    bout = battle_mod.RaidBout(p, {"num": _mega(), "stage": "Mega", "boss": True})
    while not bout.over:
        bout.play_round()
    assert (p.battles, p.wins, p.exercise_today, p.energy, p.weight) == before


def test_a_thrown_volley_bills_the_body_only():
    """Joel 2026-07-28 ("shouldnt participating in a raid drain enrgy?" ->
    "yeah do it, bill the body only").  A raid was the ONE fight door that
    spent nothing bodily; now a THROWN volley pays exactly the L17 online
    shape -- BATTLE_ENERGY_COST energy + weight-to-base, and NOT ONE
    progression channel (battles, log, exp, trainings, injury roll) --
    while the walk-away before the bell still costs nothing at all."""
    import random
    from tuipet.petbase import BATTLE_ENERGY_COST, BATTLE_WEIGHT_COST

    random.seed(3)
    pan = _panel()
    pan.client.raid = _view(_mega())
    # walk away at the ready bar: no bill, no report
    pan.key("space")
    p = pan.pet
    e0, w0 = p.energy, p.weight
    before = (p.battles, p.stage_battles, tuple(p.battle_log), p.exp,
              p.stage_trainings, p.total_trainings, p.wins)
    pan.sub.key("space")                                    # skip the intro
    for _ in range(6):
        pan.sub.anim()                                      # past the mash-arm window
    pan.key("escape")                                       # walked away before the bell
    assert pan.sub is None
    assert (p.energy, p.weight) == (e0, w0), "the walk-away was billed"
    # throw the volley for real
    pan.key("space")
    pan.sub.key("space")
    for _ in range(6):
        pan.sub.anim()
    pan.sub.bar = (pan.sub.mega_lo + pan.sub.mega_hi) // 2
    pan.sub.key("space")                                    # lock: RaidBout builds
    for _ in range(3000):
        pan.sub.anim()
        if pan.sub.phase == "result":
            break
    pan.key("space")                                        # close -> report seam
    assert pan.sub is None
    assert p.energy == max(0, e0 - BATTLE_ENERGY_COST), "the volley did not bill energy"
    assert p.weight == max(p._base_weight(), w0 - BATTLE_WEIGHT_COST), \
        "the volley did not bill weight (base-floored)"
    assert (p.battles, p.stage_battles, tuple(p.battle_log), p.exp,
            p.stage_trainings, p.total_trainings, p.wins) == before, \
        "a raid volley fed a progression channel"


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

def _prog(raids=0, maps=None):
    prog = persistence.get_progress()
    prog["raids"] = raids
    prog["maps"] = set(maps or ())
    return prog


def test_map_rows_gate_on_felled_raids_now():
    rules = data.load_egg_unlock()
    row = next(r for r in rules.values() if r.get("map") == 0)
    deep = next(r for r in rules.values() if r.get("map") == 3)
    assert not egg._conditions_met(row, _prog(raids=0))
    assert egg._conditions_met(row, _prog(raids=1))
    assert not egg._conditions_met(deep, _prog(raids=3))
    assert egg._conditions_met(deep, _prog(raids=4))


def test_map_rows_tell_the_adventure_or_raid_story():
    # map-N eggs now open by clearing adventure region N OR the raid fallback
    # (adventure rebuild 2026-07-20 -- the map rows always meant region cleared)
    rules = data.load_egg_unlock()
    idx = next(i for i, r in rules.items() if r.get("map") == 1)
    # ONE story (guide inconsistency 2026-07-28): the raid-era desc rewrite
    # ("Fell 2 raid bosses") went stale when the adventure rebuild restored
    # the map door -- desc now speaks the same dual sentence as the live goal
    assert rules[idx]["desc"] == "clear adventure map 2 (or fell 2 raid bosses)"
    assert egg.unlock_progress(idx, _prog(raids=1)) == \
        "clear adventure map 2 (or fell 2 raid bosses)"
    assert egg.unlock_ratio(idx, _prog(raids=1)) == 0.5        # 1/2 raids, map uncleared
    # clearing the adventure region unlocks it outright
    assert egg.unlock_progress(idx, _prog(maps={1})) == ""
    assert egg.unlock_ratio(idx, _prog(maps={1})) == 1.0


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
    pan.pet = SimpleNamespace(stage="Mega", bits=0,
                              record_battle=lambda *a, **k: "")
    pan.sub = None
    pan.frame_i = 0
    pan.sfx = None
    pan.msg = ""
    pan._dealt = 0
    pan._credited = 0
    pan._fell = None
    pan._won = None
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
    """The rule moved to the CARD with the numbers (uncramp 2026-07-23)."""
    from tuipet import statusbox

    class _W:
        txt = ""
        border_subtitle = ""
        def update(self, t):
            self.txt = t

    pan = _panel()
    v = _view(_mega())
    v["you"] = [0, 0]                                   # not on the board yet

    class _A:
        pet = pan.pet
        mode = pan
        stats_w = _W()

    pan.client.raid = v
    statusbox.raid(_A())
    assert "not on the board" in _A.stats_w.txt
    assert "#0" not in _A.stats_w.txt
    v["you"] = [2, 150000]                              # ranked: the number
    statusbox.raid(_A())
    assert "#2" in _A.stats_w.txt


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


# ---- raid audit 2026-07-23 (Joel: "raid system is garbage... garbled mess,
# boss at 5hp") -----------------------------------------------------------------

def test_the_page_never_exceeds_the_lcd_in_cols_or_rows():
    """The garble's root: the stats line ran 42 cols with a real tamer
    name, WRAPPED in the box, and shoved the page past 12 rows.  Pre-fit
    now: worst-case rank/damage/name, every row <= 40, exactly <= 12 rows,
    no trailing 13th."""
    pan = _panel()
    pan.client.raid = _view(_mega(), you=(999, 99_000_000),
                            top=[("Wxyzabcdefghij", 99_000_000)])
    lines = pan.text().plain.split("\n")
    assert len(lines) <= 12, f"{len(lines)} rows"
    wide = [(i, len(l)) for i, l in enumerate(lines) if len(l) > 40]
    assert not wide, f"over-40 rows: {wide}"


def test_the_volley_card_shows_the_pool_never_the_stub():
    """The status card during a raid volley showed the boss at 5/5 —
    RaidBout's display stub leaking through the battle card.  The card
    shows the COMMUNITY POOL now, and the player fights from 10."""
    from tuipet import statusbox
    pan = _panel()
    pan.client.raid = _view(_mega())
    pan.anim()
    pan.key("space")                            # mount the volley
    assert pan.sub is not None and pan.sub.raid

    class _W:
        txt = ""
        border_subtitle = ""
        def update(self, t):
            self.txt = t

    class _A:
        pet = pan.pet
        mode = pan
        stats_w = _W()

    statusbox.painter_for(pan)(_A())
    card = _A.stats_w.txt
    assert "raid" in card and "Pool" in card
    assert "5/5" not in card                    # the stub is dead
    assert "/10" in card or "10/10" in card     # the raid tank


def test_the_boss_scene_backdrop_is_floor_anchored():
    """The reduced 16px scene painted the TOP of the 24px arena art — sky
    band, floor gone, the boss floating.  The crop anchors to the floor."""
    from tuipet import raidscreen
    seen = {}
    real = raidscreen.render_scene

    def spy(placements, cols, rows, *a, **kw):
        seen["bgimg"] = kw.get("bgimg")
        seen["rows"] = rows
        return real(placements, cols, rows, *a, **kw)

    pan = _panel()
    pan.client.raid = _view(_mega())
    raidscreen.render_scene = spy
    try:
        pan.text()
    finally:
        raidscreen.render_scene = real
    full = pan.pet.background(file="tourneyBack")
    assert seen["bgimg"] == full[-seen["rows"] * 2:]   # the BOTTOM slice


def test_the_intro_never_shows_the_classic_five_on_a_raid_tank():
    """Joel 2026-07-23: 'my mons hp say 5/10 when starting, then goes to
    10/10 when the battle starts' — the banner/reveal frames carry no HP
    and fell back to the classic literal 5.  The fallback is the panel's
    own raid-aware hud now: 10/10 from the first banner frame."""
    from tuipet.battle import RAID_PLAYER_HP
    pan = _panel()
    pan.client.raid = _view(_mega())
    pan.anim()
    pan.key("space")                              # mount the volley
    sub = pan.sub
    assert sub is not None and sub.raid
    for _ in range(6):                            # the banner/reveal intro
        sub.text()
        assert sub.hud_php == RAID_PLAYER_HP, sub.hud_php
        sub.i += 1


def test_the_board_pre_warns_what_the_volley_would_refuse():
    """Joel 2026-07-25 "do i get any kind of warning?": the body gate only
    answered AFTER the press.  The rally line now runs the same gate
    read-only -- a drained/sick/sleeping pet sees the reason on the board
    before spending a keypress, and the check never wakes or bills."""
    pan = _panel()
    pan._no_account = False                             # the stub client is "in"
    pan.pet.energy = 1                                  # under BATTLE_MIN_ENERGY
    pan.client.raid = _view(_mega())
    pan.anim()
    assert "Too drained" in pan.msg and "boss stands" in pan.msg
    # the sleeper's warning is read-only: no wake, no disturb billed
    pan2 = _panel()
    pan2._no_account = False
    pan2.pet.asleep = True
    d = pan2.pet.disturb
    pan2.client.raid = _view(_mega())
    pan2.anim()
    assert "asleep" in pan2.msg.lower()
    assert pan2.pet.asleep and pan2.pet.disturb == d
    # a fit pet still gets the rally cry
    pan3 = _panel()
    pan3._no_account = False
    pan3.client.raid = _view(_mega())
    pan3.anim()
    assert "SPACE to raid" in pan3.msg


# ---- the pool stays LIVE through the volley (Joel 2026-07-30) --------------------

def _card(pan, pet):
    """Render whatever card the dispatcher lends this panel, markup stripped."""
    import re
    from tuipet import statusbox

    class _Stats:
        def __init__(self):
            self.txt, self.border_subtitle = "", ""

        def update(self, t):
            self.txt = str(t)

    class _App:
        def __init__(self):
            self.pet, self.mode, self.stats_w = pet, pan, _Stats()
            self.sound = False

    app = _App()
    statusbox.painter_for(pan)(app)
    return [re.sub(r"\[/?[^\[\]]*\]", "", ln) for ln in app.stats_w.txt.split("\n")]


def _pool_line(pan, pet):
    return next(ln for ln in _card(pan, pet) if ln.startswith("Pool"))


def _volleying():
    """A panel with a raid volley on screen, boss at full pool."""
    pan = _panel()
    pan._no_account = False
    pan.client.raid = _view(_mega(), hp=1000)
    pan.anim()
    pan.key("space")
    assert pan.sub is not None
    return pan


def test_the_pool_bar_tracks_the_gate_while_the_volley_plays():
    """The panel's whole clock used to stop at sub_anim(), so the battle card
    wore the pool SNAPSHOT taken when SPACE was pressed: a bar that could not
    move for the length of a fight while the community chipped the same boss
    down.  Status-box liveness law -- cards show LIVE data."""
    pan = _volleying()
    assert "100%" in _pool_line(pan, pan.pet)
    n = len(pan.client.calls)
    # the community lands 40% of the pool WHILE we swing
    pan.client.raid = _view(_mega(), hp=600)
    for _ in range(120):                                    # 12s of fight
        pan.anim()
    assert len(pan.client.calls) > n                        # the gate is asked
    assert "60%" in _pool_line(pan, pan.pet)                # ...and answered on the card


def test_a_boss_that_rotates_mid_volley_stops_the_copy():
    """Felled by someone else (or its window ran out): the live pool belongs
    to a DIFFERENT boss now, so printing it under this one's name would lie."""
    pan = _volleying()
    pan.client.raid = _view(_mega(), hp=1000, start=5000.0, now=5100.0)
    for _ in range(30):
        pan.anim()
    line = _pool_line(pan, pan.pet)
    assert "gone" in line and "%" not in line
    assert max(len(ln) for ln in _card(pan, pan.pet)) <= 26     # the card budget
    # and it STAYS gone -- a later view for the new boss never re-arms the bar
    pan.client.raid = _view(_mega(), hp=400, start=5000.0, now=5200.0)
    for _ in range(30):
        pan.anim()
    assert "gone" in _pool_line(pan, pan.pet)


def test_a_dark_view_holds_the_last_pool_instead_of_blanking():
    """raid_hit drops the stale view (net.py) and a refetch takes a beat: the
    bar holds its last truth rather than flashing empty or crashing."""
    pan = _volleying()
    pan.client.raid = _view(_mega(), hp=300)
    for _ in range(30):
        pan.anim()
    assert "30%" in _pool_line(pan, pan.pet)
    pan.client.raid = None
    for _ in range(30):
        pan.anim()
    assert "30%" in _pool_line(pan, pan.pet)


def test_the_pump_leaves_a_non_raid_sub_alone():
    """_pump_pool keys on the enemy dict carrying a pool: the panel's other
    children (and a raid sub mid-teardown) must not be written into."""
    pan = _panel()
    pan.sub = type("X", (), {"anim": lambda self: None, "sfx": None})()
    pan._pump_pool()                                        # no enemy dict: a no-op
    assert pan._pump_i == 0 and pan.client.calls == []
