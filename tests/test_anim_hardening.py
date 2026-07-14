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
