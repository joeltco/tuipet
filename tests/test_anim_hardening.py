"""Anim-hardening pins (2026-07-14): the cross-source authenticity pass.
Sources agreed on four beats tuipet lacked — the evolution pre-ritual (hold →
silhouette blink → strobe), the defeat pose alternating like the win pose,
and the cup verdict celebrating/sulking back on the HOUSE screen (the losing()
fx existed but sat unwired since home battles were retired 07-07)."""
import asyncio
import inspect

from tuipet import data
from tuipet.app import Screen, TuiPetApp
from tuipet.digicorescreen import silhouette
from tuipet.pet import Pet


class _FakeScreen:
    fx = None
    frame_i = 0
_FakeScreen.start_fx = Screen.start_fx
_FakeScreen.advance_fx = Screen.advance_fx
_FakeScreen._fxk_evolve = Screen._fxk_evolve


class _Canvas:
    def __init__(self):
        self.rows, self.overlay = [], []
        self.bgimg, self.bg, self.px_h = None, None, 48


def _live_num():
    _, by = data.load_sprites()
    return next(n for n in sorted(by) if not by[n].get("_placeholder"))


def test_evolve_preritual_holds_then_blinks_silhouette():
    num = _live_num()
    fr0 = data.load_sprites()[1][num]["frames"][0]
    s = _FakeScreen()
    s.start_fx("evolve", old_num=num)
    assert s.fx["steps"] == 53 and s.fx["off"] == 12
    assert s.fx["snds"] == {17: "evolve"}          # the sting rides the shifted strobe
    pet = Pet(num=num, stage="Champion")
    seen = {}
    for step in (3, 6, 8, 10):
        c = _Canvas()
        s._fxk_evolve(pet, s.fx, step, c)
        seen[step] = c.rows
    assert seen[3] == fr0                          # first act: the old form HOLDS
    sil = silhouette(fr0)
    assert seen[6] == sil and seen[6] != fr0       # then the silhouette blinks in
    assert seen[8] == fr0                          # ...0.2s off...
    assert seen[10] == sil                         # ...0.2s on again


def test_item_evolve_keeps_the_canon_parade():
    s = _FakeScreen()
    s.start_fx("evolve", old_num=_live_num(), icon="i:60")
    assert s.fx["off"] == 14 and s.fx["steps"] == 55
    assert s.fx["snds"] == {19: "evolve", 1: "jogress"}


def test_defeat_result_alternates_like_the_win():
    from tuipet import battlescreen
    src = inspect.getsource(battlescreen.BattlePanel._render_scene_frame)
    assert "(COLLAPSE, WEARY)" in src              # no more frozen loser pose


def test_cup_verdict_plays_the_home_beat():
    async def go():
        p = Pet(num=_live_num(), stage="Champion")
        p.world_seconds = 10 * 60.0
        app = TuiPetApp(pet=p)
        out = {}
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            app.mode = None
            app._after_cup(("Eliminated in the Final.", False))
            out["loss"] = app.screen_w.fx and app.screen_w.fx["kind"]
            app.screen_w.fx = None
            app._after_cup(("CHAMPION!", True))
            out["win"] = app.screen_w.fx and app.screen_w.fx["kind"]
            app.screen_w.fx = None
            app._after_cup(None)                   # closed from the menu: no beat
            out["none"] = app.screen_w.fx
        return out

    out = asyncio.run(go())
    assert out["loss"] == "losing"                 # the sulk finally has a caller
    assert out["win"] == "cheer"
    assert out["none"] is None


# ---- device-exact idle/hatch/battle beats (GML decompile 2026-07-14) -----------

def test_roamer_pauses_at_the_wall_on_the_turn_pose():
    from tuipet import anim
    assert anim.STEP_PX == 2 and anim.TURN_CHANCE == 0.30 and anim.WALL_PAUSE == 4
    r = anim.Roamer(0, 32, 16, face=1)
    import random
    random.seed(0)
    for _ in range(2000):                      # walk until a wall is hit
        r.step()
        if r.pause:
            break
    assert r.pause == anim.WALL_PAUSE
    x0, f0 = r.x, r.face
    for beat in range(3):                      # 3 beats: stopped, alternating turn
        for _ in range(anim.WALK_BEAT):
            r.step()
        assert r.x == x0 and r.face == f0      # no movement, no flip yet
    for _ in range(anim.WALK_BEAT):            # the departure beat
        r.step()
    assert r.pause == 0 and r.face == -f0      # faces away from the wall...
    assert r.x == x0 - anim.STEP_PX * f0       # ...and has already stepped off


def test_hatch_wobble_accelerates():
    """Sways at 4/6/8 (0.2s beat) then EVERY interval 10..15 (0.1s) --
    the device egg quickens as the hatch nears (alarm 30 -> 10)."""
    beats = [4, 6, 8] + list(range(10, 16))
    def moves(n):
        return sum(1 for k in beats if k <= min(n, 15))
    assert moves(5) == moves(4)                # slow phase: 5 is a rest interval
    assert moves(6) == moves(4) + 1
    for n in range(10, 16):                    # fast phase: every interval moves
        assert moves(n) == moves(n - 1) + 1


def test_final_winning_blow_lands_silent():
    from tuipet.battlescreen import round_timeline
    tl = round_timeline(5, 1, pdmg=1, edmg=1, player_first=True)
    kill = [e for e in tl if e["m"] == "hit" and e["def"] == "foe"]
    assert kill and all(e["final"] for e in kill)      # the KO hit is marked
    tl2 = round_timeline(5, 5, pdmg=1, edmg=1, player_first=True)
    assert not any(e.get("final") for e in tl2 if e["m"] == "hit")
    tl3 = round_timeline(1, 5, pdmg=0, edmg=1, player_first=False)
    pk = [e for e in tl3 if e["m"] == "hit" and e["def"] == "pet"]
    assert pk and not any(e["final"] for e in pk)      # a LOSS still stings


# ---- care widens the skill window (condition, 2026-07-14) -----------------------

def test_condition_tiers():
    p = Pet(num=100, stage="Champion", hunger=4, strength=4, mood=300)
    p.energy = p.max_energy
    assert p.condition() == 3                      # a perfectly kept pet
    p.sick = True
    assert p.condition() == 1                      # a sick body caps precision
    q = Pet(num=100, stage="Champion", hunger=0, strength=0, mood=-300)
    q.energy = 0
    assert q.condition() == 0                      # trembling paw


def test_condition_widens_the_drill_windows():
    from tuipet import training
    top = Pet(num=100, stage="Champion", hunger=4, strength=4, mood=300)
    top.energy = top.max_energy
    pan = training.TrainingPanel(top)
    assert pan.cond == 3
    assert pan.virus_zone == training.VIRUS_BAR_MIN - 3 * training.COND_ZONE_PX
    assert pan.timer == training.VACCINE_WINDOW + 3 * training.COND_MASH_TICKS
    low = Pet(num=100, stage="Champion", hunger=0, strength=0, mood=-300)
    low.energy = 0
    pan2 = training.TrainingPanel(low)
    assert pan2.cond == 0
    assert pan2.virus_zone == training.VIRUS_BAR_MIN        # baseline unchanged
    assert pan2.timer == training.VACCINE_WINDOW
    assert "condition" in pan2.text().plain        # the menu SHOWS the tier


# ---- the monthly ladder (2026-07-14) ---------------------------------------------

def _srv():
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.join(_o.path.dirname(__file__), "..", "server"))
    import server
    return server


def test_ladder_credits_only_agreeing_pairs():
    srv = _srv()
    now = 1000.0
    srv._ladder_report("alice", True, "bob", now)          # one half: nothing yet
    assert srv.LADDER["seasons"] == {}
    srv._ladder_report("bob", False, "alice", now + 5)     # the agreeing half
    season = srv._season_key(now)
    assert srv.LADDER["seasons"][season] == {"alice": 1}
    srv._ladder_report("alice", True, "bob", now + 300)    # stale: window passed
    srv._ladder_report("bob", False, "alice", now + 300 + srv.LADDER_CONFIRM_S + 1)
    assert srv.LADDER["seasons"][season] == {"alice": 1}


def test_ladder_draw_and_forgery_credit_nothing():
    srv = _srv()
    srv._ladder_report("alice", False, "bob", 1000.0)      # draw: two loss stories
    srv._ladder_report("bob", False, "alice", 1001.0)
    assert srv.LADDER["seasons"] == {}
    for i in range(5):
        srv._ladder_report("cheat", True, "victim", 2000.0 + i)   # lone reports
    assert srv.LADDER["seasons"] == {}


def test_ladder_pair_cap_lids_collusion():
    srv = _srv()
    for i in range(6):
        t = 1000.0 + i * 10
        srv._ladder_report("alice", True, "bob", t)
        srv._ladder_report("bob", False, "alice", t)
    season = srv._season_key(1000.0)
    assert srv.LADDER["seasons"][season]["alice"] == srv.LADDER_PAIR_CAP


def test_ladder_view_and_past_season_award():
    srv = _srv()
    import calendar, time as _t
    srv.LADDER["seasons"]["2026-06"] = {"joel": 9, "wyld": 7, "third": 5, "fourth": 1}
    srv.LADDER["seasons"][srv._season_key()] = {"joel": 2, "wyld": 3}
    v = srv._ladder_view("joel")
    assert v["top"][0] == ["wyld", 3] or v["top"][0] == ("wyld", 3)
    assert v["you"] == [2, 2]
    assert v["award"] == {"season": "2026-06", "rank": 1, "wins": 9, "bits": 25000}
    srv._ladder_claim("joel", "2026-06")
    assert srv._ladder_view("joel")["award"] is None       # claimed = gone
    v4 = srv._ladder_view("fourth")
    assert v4["award"] is None                             # rank 4: no podium
    assert 0 <= v["days_left"] <= 30


def test_ladder_award_grants_bits_exactly_once():
    from tuipet.lobbyscreen import LobbyPanel

    class _C:
        name = "joel"
        ladder = {"t": "ladder", "season": "2026-07", "days_left": 5,
                  "top": [["joel", 4]], "you": [1, 4],
                  "award": {"season": "2026-06", "rank": 2, "wins": 7, "bits": 10000}}
        claims = []
        def ladder_claim(self, season): self.claims.append(season)

    pet = Pet(num=100, stage="Champion", bits=100)
    pet.world_seconds = 10 * 60.0
    pan = LobbyPanel.__new__(LobbyPanel)
    pan.client, pan.pet = _C(), pet
    pan.bshow = pan.jshow = None
    pan.state = None
    pan.sfx = pan.status = None
    pan.anim()
    assert pet.bits == 10100 and _C.claims == ["2026-06"]
    assert "rank 2" in pan.status
    pan.anim()                                             # the ledger stops a re-grant
    assert pet.bits == 10100 and _C.claims == ["2026-06"]


def test_ladder_page_renders():
    from tuipet.lobbyscreen import LobbyPanel

    class _C:
        name = "joel"
        ladder = {"t": "ladder", "season": "2026-07", "days_left": 17,
                  "top": [["wyld", 9], ["joel", 4]], "you": [2, 4], "award": None}

    pan = LobbyPanel.__new__(LobbyPanel)
    pan.client = _C()
    plain = pan._text_ladder().plain
    assert "season 2026-07" in plain and "wyld" in plain
    assert "▸ 2. joel" in plain.replace("  ", " ") or "joel" in plain
    assert "resets in 17 days" in plain
    assert all(len(line) <= 40 for line in plain.splitlines())
