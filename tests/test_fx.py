"""Care-animation (fx) state machine + re-trigger gating (Workstream C).

The #lcd Screen owns a care-action fx (eat/clean/cheer/...) advanced one step per
frame. Two correctness concerns:
  - an fx must run exactly `steps` frames then end (and 'clean' chains into the
    'cheer' sunshine);
  - a care action must not start a second fx while one is running (the re-trigger
    that caused the old feed-status flicker).

The state machine is tested directly here (methods bound onto a plain object, no
Textual mount). The per-action gating is verified by inspection: action_feed /
_clean / _praise / _scold / _play / _heal each early-return on
`self.screen_w.fx is not None` (and this test guards that the guard is present in
source). Pinning the engine means a refactor can't silently break completion or
the clean->cheer chain.
"""
import os
import re

from tuipet.app import Screen
from tuipet.pet import Pet


class _FakeScreen:
    fx = None
    frame_i = 0     # advance_fx keeps weather/filth animating via frame_i
_FakeScreen.start_fx = Screen.start_fx
_FakeScreen.advance_fx = Screen.advance_fx


def test_fx_runs_exactly_steps_then_ends():
    s = _FakeScreen()
    s.start_fx("cheer")
    assert s.fx is not None
    steps = s.fx["steps"]
    for _ in range(steps - 1):
        assert s.advance_fx() is True, "fx should stay active until the last step"
    s.advance_fx()                       # the final step
    assert s.fx is None, "fx must end after exactly `steps` frames"


def test_clean_chains_into_cheer_only_when_filthy():
    # DVPet clean(): cheer(true) chains ONLY if filth was actually washed;
    # an empty-room wash just ends (no celebration).
    s = _FakeScreen()
    s.start_fx("clean", poop=2)
    for _ in range(s.fx["steps"]):
        s.advance_fx()
    assert s.fx is not None and s.fx["kind"] == "cheer", "a filthy wash ends in the sunshine cheer"
    s2 = _FakeScreen()
    s2.start_fx("clean")                 # nothing to wash
    for _ in range(s2.fx["steps"]):
        s2.advance_fx()
    assert s2.fx is None, "an empty-room wash ends without a cheer"


def test_evolve_chains_into_cheer():
    # DVPet evolFinish(true): every evolution ends in cheer(true, _happy).
    s = _FakeScreen()
    s.start_fx("evolve", old_num=-1)
    for _ in range(s.fx["steps"]):
        s.advance_fx()
    assert s.fx is not None and s.fx["kind"] == "cheer", "evolution ends in the praise cheer"


def test_eat_fx_scales_with_glutton():
    glut = _FakeScreen(); glut.start_fx("eat", "f:0", pet=Pet(num=-1, glutton=1))
    picky = _FakeScreen(); picky.start_fx("eat", "f:0", pet=Pet(num=-1, glutton=-1))
    # a glutton wolfs food (mod 0.9 -> fewer steps); a picky eater dawdles (mod 1.1)
    assert glut.fx["steps"] == int(34 ** 0.9) + 1
    assert picky.fx["steps"] == int(34 ** 1.1) + 1
    assert glut.fx["steps"] < picky.fx["steps"]


def test_advance_with_no_fx_is_safe():
    s = _FakeScreen()
    assert s.advance_fx() is False         # no active fx -> no-op, no crash


def test_care_actions_guard_against_retrigger():
    """Every care action that starts an fx must early-return while one is active."""
    here = os.path.dirname(__import__("tuipet").__file__)
    src = open(os.path.join(here, "app.py")).read()
    # find each `def action_*` body and check feed/clean/praise/scold/play/heal guard
    GUARDED = ["action_feed", "action_clean", "action_praise",
               "action_scold", "action_play", "action_heal"]
    missing = []
    for name in GUARDED:
        m = re.search(rf"def {name}\(self.*?\):(.*?)(?=\n    def )", src, re.S)
        body = m.group(1) if m else ""
        if "self.screen_w.fx is not None" not in body:
            missing.append(name)
    assert not missing, f"care actions missing the fx re-trigger guard: {missing}"


def test_gift_fx_chains_into_cheer():
    # ClockTic.giftEnd: the gifting amble always ends in State.Cheering
    s = _FakeScreen()
    s.start_fx("gift", icon="f:8")
    for _ in range(s.fx["steps"]):
        s.advance_fx()
    assert s.fx is not None and s.fx["kind"] == "cheer"


def test_eat_fx_survives_a_blank_last_food_frame():
    """Joel's Termux launch crash (2026-07-04): 28 foods ship a BLANK 'eaten
    away' final frame that extracts as None; the eat fx crashed on the LAST
    BITE of any of them (_blit(None) -- the index was guarded, the value not).
    The golden always fed f:8 (4 real frames), so it never saw one: exercise
    the exact crashing food, every step."""
    import random
    from tuipet import app as app_mod
    from tuipet import data
    from tuipet.pet import Pet
    frames = data.load_icons()["f:7"]
    assert frames[-1] is None                    # the landmine is real data

    class S(app_mod.Screen):
        def __init__(self):
            self.fx = None
            self.frame_i = 0
            self.roamer = None
        def update(self, t):
            pass

    random.seed(3)
    p = Pet(num=102, name="Devimon", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    s = S()
    s.start_fx("eat", icon="f:7", pet=p)
    for step in range(s.fx["steps"]):            # incl. the last-bite beat
        s.fx["step"] = step
        s.frame_i = step
        s._paint_fx(p)                           # used to TypeError at step 21


def test_bag_toy_plays_the_hop_over_its_real_toy():
    """Play audit 2026-07-05: canon jumping() bounces the pet over its toy
    (the long-flagged unported piece).  A bag toy now hands the app a
    ('play', key) and the fx draws the toy's real frames beside the feet."""
    import random
    from tuipet import app as app_mod
    from tuipet.pet import Pet
    from tuipet.shopscreen import ShopPanel

    random.seed(2)
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=500)
    p.world_seconds = 12 * 60.0
    p.compliance = True
    p.add_item("i:3")                             # the Ball
    pan = ShopPanel(p, start_mode="bag")
    while pan._tabs()[pan.tab] != "toy":
        pan.key("right")
    rows = pan._rows()
    pan.cursor = next(i for i, e in enumerate(rows) if e["key"] == "i:3")
    r = pan.key("enter")
    assert r == ("done", ("play", "i:3"))         # the bag hands off the toy

    class S(app_mod.Screen):
        def __init__(self):
            self.fx = None
            self.frame_i = 0
            self.roamer = None
        def update(self, t):
            pass

    s = S()
    s.start_fx("play", icon="i:3", pet=p)
    c1, c2 = app_mod._FxCtx(), app_mod._FxCtx()
    for c, icon in ((c1, "i:3"), (c2, None)):
        c.px_h = 24
        c.overlay = []
        c.xshift = c.yshift = 0
        c.rows = []
        fx = dict(s.fx, icon=icon, step=3)
        app_mod.Screen._fxk_play(s, p, fx, 3, c)
    assert len(c1.overlay) > len(c2.overlay)      # the toy's pixels are there


def test_hatch_render_follows_the_canon_beats():
    """Hatch-anim audit 2026-07-05: DVPet hatch() -- the egg rocks +-3 over
    beats 4..15 (smooth +3/+6/+3/0 oscillation), cracks (pose 1) at 16, the
    baby peeks (pose 2) at 19.  int((3.0-t)/0.1) TRUNCATED binary floats and
    made the rock stutter and the crack land a beat late; the beat is rounded
    now.  Pinned through the real paint path on both drive styles (direct
    timer set AND accumulated advance_hatch subtraction)."""
    from tuipet import app as app_mod
    from tuipet import egg as egg_mod
    from tuipet.pet import Pet

    cap = {}
    real = app_mod.render_screen

    def spy(rows, cols, r, on, bg, mirror=False, xshift=0, overlay=None, bgimg=None):
        cap["rows"], cap["xshift"] = rows, xshift
        return real(rows, cols, r, on, bg, mirror=mirror, xshift=xshift,
                    overlay=overlay, bgimg=bgimg)

    class S(app_mod.Screen):
        def __init__(self):
            self.anim_key = None
            self.frame_i = 0
            self.fx = None
            self.thunder_i = 0

        def update(self, t):
            pass

    old = app_mod.render_screen
    app_mod.render_screen = spy
    try:
        frames = egg_mod.record(1)["frames"]

        def drive(step_fn, pet):
            seq = []
            for beat in range(30):
                step_fn(pet, beat)
                S.paint(s, pet)
                which = next((i for i, f in enumerate(frames) if f == cap["rows"]), None)
                seq.append((which, cap["xshift"]))
            return seq

        s = S()
        p = Pet.new_egg(egg_type=1)
        p.stage_seconds = 9e9
        p._tick_egg()
        assert p.hatching
        direct = drive(lambda q, b: setattr(q, "_hatch_t", 3.0 - b * 0.1), p)
        p2 = Pet.new_egg(egg_type=1)
        p2.stage_seconds = 9e9
        p2._tick_egg()
        acc = []
        for beat in range(30):
            S.paint(s, p2)
            which = next((i for i, f in enumerate(frames) if f == cap["rows"]), None)
            acc.append((which, cap["xshift"]))
            p2.advance_hatch(0.1)
        for seq in (direct, acc):
            assert [w for w, x in seq[:16]] == [0] * 16          # whole egg
            assert [w for w, x in seq[16:19]] == [1] * 3         # the crack
            assert all(w == 2 for w, x in seq[19:])              # the baby peeks
            assert [x for w, x in seq[4:16]] == [3, 6, 3, 0] * 3  # the smooth rock
            assert all(x == 0 for w, x in seq[:4]) and all(x == 0 for w, x in seq[16:])
    finally:
        app_mod.render_screen = old
