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
