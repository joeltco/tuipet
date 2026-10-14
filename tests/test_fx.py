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


def _run_out(s):
    """Play the current show to its end at its real pace (the animation
    audit's rates make step counts != frame counts)."""
    k = s.fx["kind"]
    while s.fx and s.fx["kind"] == k:
        s.advance_fx()


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
    _run_out(s)
    assert s.fx is not None and s.fx["kind"] == "cheer", "a filthy wash ends in the sunshine cheer"
    s2 = _FakeScreen()
    s2.start_fx("clean")                 # nothing to wash
    _run_out(s2)
    assert s2.fx is None, "an empty-room wash ends without a cheer"


def test_evolve_chains_into_cheer():
    # DVPet evolFinish(true): every evolution ends in cheer(true, _happy).
    s = _FakeScreen()
    s.start_fx("evolve", old_num=-1)
    _run_out(s)
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
    # the handlers live in appactions since the tier-3 split (2026-07-17)
    src = open(os.path.join(here, "appactions.py")).read()
    # find each `def action_*` body and check the feed/clean guard
    # (the play action left 2026-07-17 with the mood system)
    GUARDED = ["action_feed", "action_clean"]
    missing = []
    for name in GUARDED:
        m = re.search(rf"def {name}\(self.*?\):(.*?)(?=\n    def )", src, re.S)
        body = m.group(1) if m else ""
        if "self.screen_w.fx is not None" not in body:
            missing.append(name)
    assert not missing, f"care actions missing the fx re-trigger guard: {missing}"


def test_the_drills_three_verdicts_route_to_three_fx():
    """Joel 2026-07-25 ("mon is showing happy pose after a normal training
    hit? wheres the frustration poses at???"): _after_train dispatched on a
    two-way anim, so the middle grade took the full cheer.  Each verdict
    pose now routes to its own show -- Cheering / the deserved 4/6 jeer /
    the 10/9 slump."""
    from tuipet import appactions
    from tuipet.pet import Pet

    class _App:
        def __init__(self, anim):
            self.pet = Pet(num=100, stage="Champion")
            self.pet.anim = anim
            self.screen_w = _FakeScreen()
            self.flashed = None
        flash = lambda self, m: setattr(self, "flashed", m)
        repaint = lambda self: None
    _App._after_train = appactions.ActionsMixin._after_train

    shows = {}
    for anim in ("happy", "tantrum", "sad", "refuse"):
        a = _App(anim)
        a._after_train("")
        shows[anim] = (a.screen_w.fx["kind"], a.screen_w.fx.get("good", True))
    assert shows["happy"] == ("cheer", True)      # a PERFECT strike celebrates
    assert shows["tantrum"] == ("jeer", True)     # a solid hit grumbles
    assert shows["sad"] == ("jeer", False)        # a whiff slumps
    assert shows["refuse"][0] == "spit"           # the refusal head-shake, unchanged


def test_gift_fx_ends_for_the_reveal():
    # the amble ends and the app's reveal starts the cheer holding the prize
    # (animation audit 2026-10-14: the reveal came AFTER a 3s cheer before)
    s = _FakeScreen()
    s.start_fx("gift", icon="f:8")
    _run_out(s)
    assert s.fx is None


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


def test_hatch_render_follows_the_canon_beats():
    """Hatch-anim audit 2026-07-05: DVPet hatch() -- the egg rocks +-3 over
    beats 4..15 (smooth +3/+6/+3/0 oscillation), cracks (pose 1) at 16, the
    baby peeks (pose 2) at 19.  int((3.0-t)/0.1) TRUNCATED binary floats and
    made the rock stutter and the crack land a beat late; the beat is rounded
    now.  Pinned through the real paint path on both drive styles (direct
    timer set AND accumulated advance_hatch subtraction)."""
    from tuipet import app as app_mod
    from tuipet import arena as arena_mod   # Screen resolves render_screen here
    from tuipet import egg as egg_mod
    from tuipet.pet import Pet

    cap = {}
    real = arena_mod.render_screen

    def spy(rows, cols, r, on, bg, mirror=False, xshift=0, overlay=None,
            bgimg=None, **kw):
        cap["rows"], cap["xshift"] = rows, xshift
        return real(rows, cols, r, on, bg, mirror=mirror, xshift=xshift,
                    overlay=overlay, bgimg=bgimg, **kw)

    class S(app_mod.Screen):
        def __init__(self):
            self.anim_key = None
            self.frame_i = 0
            self.fx = None
            self.thunder_i = 0

        def update(self, t):
            pass

    old = arena_mod.render_screen
    arena_mod.render_screen = spy
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
            # the ACCELERATING rock (device-exact, GML 2026-07-14): sways on
            # 4/6/8 (0.2s beat), then every interval 10..15 -- the egg
            # quickens as the hatch nears (was a constant [3,6,3,0]*3 walk)
            assert [x for w, x in seq[4:16]] == [3, 3, 6, 6, 3, 3, 0, 3, 6, 3, 0, 3]
            assert all(x == 0 for w, x in seq[:4]) and all(x == 0 for w, x in seq[16:])
    finally:
        arena_mod.render_screen = old


def test_play_hops_on_canon_beats_and_ends_in_cheer():
    """Play-anim audit 2026-07-05: DVPet jumping() -- a 6-beat grounded
    lead-in, three hops launching at 6/20/34 (rise 6 / fall 6 / rest 2, happy
    sting at each launch), and frame 48 chains into Cheering.  tuipet hopped
    instantly with no rests and no chained cheer.  APEX HISTORY: the 07-05 arc
    scaled canon's rise to 12px, which launched half a 16px mon off the 24px
    arena; Joel 2026-07-06 ("jumping way too high") set the apex to the max
    FULL-BODY height instead -- grounded top row 24-16-2 = 6."""
    from tuipet import app as app_mod
    s = _FakeScreen()
    s.start_fx("play", icon="i:0")
    s.fx["rate"] = 1                     # the canon beats (the rate is pacing only)
    assert s.fx["steps"] == 48
    launches = []
    while s.fx and s.fx["kind"] == "play":
        st = s.fx["step"]
        if st >= app_mod.PLAY_LEAD and (st - app_mod.PLAY_LEAD) % app_mod.PLAY_HOP == 0:
            launches.append(st)
        if not s.advance_fx():
            break
    assert launches == [6, 20, 34]
    assert s.fx is not None and s.fx["kind"] == "cheer"   # jumping() -> Cheering
    assert app_mod.PLAY_HOP_H == 24 - 16 - 2              # a real jump that keeps the
    #                                        whole 16px body on the 24px arena (don't
    #                                        re-raise for canon: user-set 2026-07-06)


def test_the_emote_grammar_matches_the_decompile():
    """ICON AUDIT 2026-07-25 (Joel: "do a full blown refactor and audit of all
    the icon sprites that are supposed to appear on screen").  Canon keeps TWO
    emote slots (SpriteAnim.java 1913-1934 / 2323-2334):

      _emotionLabel -- the emote BESIDE THE PET: happy, unhappy, unhappy2,
                       attention, dying, dying2, nap/sleep lights
      _moodLabel    -- the DATA-PAGE mood readout: happy, happy2, unhappy,
                       unhappy2, depressed, depressed2

    and the shows draw from the first: cheer() -> "happy" (15586+),
    jeer() -> "unhappy"/"unhappy2" alternating every 6 beats (15637+),
    badHealthJeer() -> "dying"/"dying2" (15629).

    THE SUN AND THE SMOKE (Joel 2026-07-25, pointing at the art itself).
    `happy` is a SUN -- radiating rays -- and it pops on every up-beat of the
    cheer, which the player sees constantly.  Its opposite is `unhappy` +
    `unhappy2`: THE SMOKE, a big puff and then a small one drifting off as it
    dissipates.  Canon had this right; the sprite was briefly swapped for
    `depressed` (v0.5.270) on a misread of the 1-bit dump -- `depressed` is a
    FACE, canon's status-page mood icon, and never belongs beside the pet.

    Every frustration show wears the smoke now: the lost drill and the scold
    (jeer), the lost battle and the lost cup (losing -- which flashed the
    `dying` SKULL, canon's battle-end icon-row mark, so the two moments a
    player hits most never blew smoke), and the ambient sulk."""
    import inspect

    from tuipet import data
    src = {fn: inspect.getsource(getattr(Screen, fn))
           for fn in ("_fxk_cheer", "_fxk_jeer", "_fxk_losing")}
    assert '"happy"' in src["_fxk_cheer"], "cheer lost the SUN"
    assert '"unhappy"' in src["_fxk_jeer"], "the lost drill lost its SMOKE"
    assert '"unhappy"' in src["_fxk_losing"], "the lost battle lost its SMOKE"
    # the FACE is a status-page icon -- it may never ride a scene show again
    for fn, body in src.items():
        assert '"depressed"' not in body, f"{fn} took the status-page FACE"
    # the smoke is a 2-frame pair that flips on the canon 6-beat
    E = data.load_effects()
    assert len(E["unhappy"]) == 2 and len(E["happy"]) == 2
    seen = {(step // 6) % len(E["unhappy"]) for step in (0, 6, 12, 18, 24)}
    assert seen == {0, 1}, "the frustration emote must flip between both frames"
    # the puff DISSIPATES: frame 2 is the small remnant, lower and lighter --
    # that shrink IS the animation, not a broken crop
    big, small = (sum(r.count("1") for r in f) for f in E["unhappy"])
    assert big > small, "the smoke must thin out on its second frame"


def test_the_frustration_dance_paints_its_smoke_beside_the_pet(monkeypatch):
    """The smoke actually REACHES the screen on both frustration shows, on
    the same beat and in the same slot the cheer's sun uses -- and stays
    inside the 32px window (7px cloud at the pet's right edge, x28..34)."""
    from tuipet import data, grid
    from tuipet.app import PET_BASE_X, SPRITE_W
    E = data.load_effects()
    ink = [sum(r.count("1") for r in f) for f in E["unhappy"]]

    def emote_px(monkeypatch, kind, beats):
        cap = _capture_render(monkeypatch)
        s = _paint_harness()
        for m in ("_fxk_jeer", "_fxk_losing"):     # the harness binds only what it needs
            setattr(s, m, getattr(Screen, m).__get__(s))
        p = _pose_pet()
        seen = {}
        for step in beats:
            s.fx = {"kind": kind, "step": step, "steps": 50, "icon": None,
                    "poop": 0, "old_num": None, "good": True}
            s._paint_fx(p)
            seen[step] = {(x, y) for x, y in cap["overlay"]
                          if x >= PET_BASE_X + SPRITE_W}
        return seen

    for kind in ("jeer", "losing"):
        seen = emote_px(monkeypatch, kind, (0, 6, 12))
        assert all(seen.values()), f"{kind} painted no emote beside the pet"
        assert seen[0] != seen[6], f"{kind} never flipped its pair"
        assert seen[0] == seen[12], f"{kind} broke the 6-beat cycle"
        for step, px in seen.items():
            assert all(grid.X0 <= x < grid.X1 for x, _ in px), \
                f"{kind} smoke left the window at beat {step}"
            assert all(grid.TOP <= y < grid.TOP + 16 for _, y in px), \
                f"{kind} smoke left the 16px band at beat {step}"
            assert len(px) == ink[(step // 6) % 2], \
                f"{kind} beat {step} is not the whole puff"
        # the puff sits high, then the remnant drifts DOWN as it thins
        assert min(y for _, y in seen[0]) == grid.TOP, f"{kind} puff is not at head height"
        assert min(y for _, y in seen[6]) > min(y for _, y in seen[0]), \
            f"{kind} second frame must drift down, not sit on the first"


def test_bad_praise_and_bad_scold_use_their_own_pose_pairs():
    """Cheer/jeer audit 2026-07-05: canon cheer(goodPraise)/jeer(goodScold)
    swap pose pairs by DESERVEDNESS -- Bad_Praise bounces 6/4 (not 5/7),
    Bad_Scold slumps 10/9 (not 4/6).  tuipet played one variant of each.
    (Sound stays angry for every scold: soundConfig maps unhappy -> angry.wav.)"""
    good_cheer = _FakeScreen(); good_cheer.start_fx("cheer")
    bad_cheer = _FakeScreen(); bad_cheer.start_fx("cheer", good=False)
    assert good_cheer.fx["good"] and not bad_cheer.fx["good"]
    good_jeer = _FakeScreen(); good_jeer.start_fx("jeer")
    bad_jeer = _FakeScreen(); bad_jeer.start_fx("jeer", good=False)
    assert good_jeer.fx["snds"] == bad_jeer.fx["snds"] == {6: "angry"}
    assert not bad_jeer.fx["good"]


def test_poop_sound_keys_the_new_piles_size():
    """Poop-anim audit 2026-07-05: canon playPoopSound keys the byte poop()
    returns -- the SIZE of the new pile (1 small / >2 large / else normal) --
    not the pile count.  A small fourth pile used to bark largePoop."""
    import re
    src = open("src/tuipet/app.py").read()
    m = re.search(r'sz = \(p\.poop_sizes\[-1\].*\n.*poop_snd = "smallPoop" if sz == 1 '
                  r'else \("largePoop" if sz > 2 else "poop"\)', src)
    assert m, "the size-keyed mapping is gone (count-keyed again?)"


def test_poopdance_wiggles_then_flips_and_never_chains():
    """DVPet poopDance: nervous wiggle (beats 2..10) then pose 4 flipping its
    mirror every 2 beats (12..18) -- the tell that a poop is coming."""
    s = _FakeScreen()
    s.start_fx("poopdance")
    assert s.fx["steps"] == 21 and not s.fx.get("snds")
    n = 0
    while s.advance_fx():
        n += 1
        assert n < 30
    assert s.fx is None                    # a special idle: ends, no chained fx


def test_battle_defeat_gets_the_wash_sweep_off():
    """Wash-anim audit 2026-07-05: canon endBattle plays Winning/Losing ON THE
    HOME SCREEN -- winning() = cheer with the _win sting; losing() = a 30-beat
    disposition-shaded jeer with the dying emote, then the WASH rolls in and
    sweeps the sore loser clean off the screen.  tuipet played a bare sting."""
    s = _FakeScreen()
    s.start_fx("losing")
    assert s.fx["steps"] == 50 and s.fx["snds"] == {6: "lose"}
    n = 0
    while s.advance_fx():
        n += 1
        assert n < 60
    assert s.fx is None                        # a loss ends unceremonious: no chain


def test_assistant_feed_drops_off_and_chains_the_real_eat():
    """Assist-anim audit 2026-07-05: canon assistantFeed places the meal and
    EXITS LEFT by beat 10 while the STANDARD eat anim runs (eat(Assistant_Feed))
    -- tuipet kept the helper on-screen through a simplified 12-beat chew.
    Now: a 12-step drop-off, then the real eat fx chains with its descent
    stages skipped (the meal is already on the floor)."""
    from tuipet.pet import Pet
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 12 * 60.0
    s = _FakeScreen()
    s.start_fx("assist", pet=p, poop=0, icon="f:44")
    s.fx["act"] = "feed"
    s.fx["steps"] = 12
    s.fx["chain_eat"] = "f:44"
    s.fx["pet_ref"] = p
    n = 0
    while s.fx and s.fx["kind"] == "assist":
        s.advance_fx()
        n += 1
        assert n < 20
    assert s.fx is not None and s.fx["kind"] == "eat"
    assert s.fx["step"] == 6                    # descent skipped: it's already down
    assert s.fx["bite_snds"]                    # the real eat carries its own stings


def test_the_present_rides_the_whole_return_leg():
    """Gift-anim audit 2026-07-05: canon gifting() pushes the present home in
    LOCKSTEP (meatButton.moveRight(3) beside the pet from off-screen left) --
    tuipet popped it in only at the arrival hold."""
    from tuipet import app as app_mod
    from tuipet.pet import Pet
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 12 * 60.0

    class S(app_mod.Screen):
        def __init__(self):
            self.anim_key = None
            self.frame_i = 0
            self.fx = None
            self.thunder_i = 0

        def update(self, t):
            self.last = t

    s = S()
    s.start_fx("gift", icon="f:5")
    s.fx["rate"] = 1                     # walk the canon beats one by one
    mid_pixels = end_pixels = 0
    while s.fx and s.fx["kind"] == "gift":
        st = s.fx["step"]
        s._paint_fx(p)
        n = sum(ch not in " \\n" for ch in s.last.plain)
        if st == app_mod.GIFT_OUT + app_mod.GIFT_BACK // 2:
            mid_pixels = n                    # mid-return: pet + present
        if st == app_mod.GIFT_OUT + app_mod.GIFT_BACK + 2:
            end_pixels = n                    # the hold: pet + present
        s.advance_fx()
    assert s.fx is None                  # the app's reveal starts the cheer
    assert mid_pixels > 0 and end_pixels > 0


# ---- walk-pose + feeding audits (2026-07-08) ---------------------------------
# Canon (SpriteAnim.java): the idle-family specials (yawning/poopDance/
# surprising) play IN PLACE with stateAnims still running every tick, so the
# condition column and filth stay up; idleUnwell resets Y ONLY; and eat() pads
# BOTH the food (x31+pad) and the char (x55+pad) by the FULL filth width.
# tuipet regressions pinned here: the tells teleported the pet to the anchor
# and dropped the status UI; sick/startle re-anchored; a 1-2 pile block (its
# edge == the anchor) let the food descend onto the slots.

def _paint_harness(roamer_x=8.0):
    # x8 sits INSIDE every legal corridor (left of the rail's wall at x12,
    # off the x12 anchor) -- the old 22.0 parked the pet past the grid's own
    # right wall (X1 - sprite = 20), a spot the real roamer can't reach and
    # one the icon-rail sweep's universal clamp now corrects (2026-07-10)
    from tuipet.anim import Roamer
    from tuipet.app import SCREEN_COLS, SPRITE_W
    s = type("_S", (), {})()
    for m in ("paint", "_paint_fx", "_pose_rows", "_pose_rows_idx",
              "_food_frames", "_fx_filth", "_background", "_crossfade",
              "_fxk_yawn", "_fxk_poopdance", "_fxk_eat"):
        setattr(s, m, getattr(Screen, m).__get__(s))
    s.BG_FADE = Screen.BG_FADE
    s.fx = None
    s.frame_i = 0
    s._idle_expr = None
    s.roamer = Roamer(roamer_x, SCREEN_COLS, SPRITE_W)
    s.update = lambda *_: None
    return s


def _pose_pet(**kw):
    p = Pet.new_egg(egg_type=1)
    p._hatch_into_fresh()
    p.num = 29                                    # a Rookie with the full frame set
    p.anim = "idle"
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _capture_render(monkeypatch):
    cap = {}

    def fake(rows, cols, nrows, on, bg, **kw):
        cap.clear()
        cap.update(kw)
        return ""

    monkeypatch.setattr("tuipet.arena.render_screen", fake)
    return cap


def test_yawn_tell_plays_in_place_with_status_ui(monkeypatch):
    from tuipet import grid
    from tuipet.app import COND_W, _filth_right
    cap = _capture_render(monkeypatch)
    s = _paint_harness()
    p = _pose_pet(poop=2, poop_sizes=[2, 2], sick=True)
    s.fx = {"kind": "yawn", "step": 5, "steps": 22, "icon": None,
            "poop": 0, "old_num": None, "good": True}
    s._paint_fx(p)
    # the pose plays at the roamer's spot CLAMPED into the free corridor
    # (Bandai-grammar sweep 2026-07-11): 2 piles are a left wall at x12 and
    # the sick SKULL a right wall at x12 -- the corridor is that one spot
    from tuipet.app import PET_BASE_X, SICK_ZONE, SPRITE_W
    lo = _filth_right(2) - PET_BASE_X
    hi = (grid.X1 - SICK_ZONE - SPRITE_W) - PET_BASE_X
    assert cap["xshift"] == min(max(s.roamer.xshift, lo), max(hi, lo))
    assert cap["mirror"] == s.roamer.mirror       # facing kept (canon getIsMirror())
    xs = {x for x, _ in cap["overlay"]}
    assert any(x >= grid.X1 - COND_W for x in xs), "the sick skull must stay up"
    assert any(grid.X0 <= x < _filth_right(2) for x in xs), "filth piles must stay up"


def test_poopdance_tell_plays_in_place(monkeypatch):
    cap = _capture_render(monkeypatch)
    s = _paint_harness()
    p = _pose_pet(poop=0)
    s.fx = {"kind": "poopdance", "step": 4, "steps": 21, "icon": None,
            "poop": 0, "old_num": None, "good": True}
    s._paint_fx(p)
    assert cap["xshift"] == s.roamer.xshift       # wiggle sways around its own spot
    s.fx["step"] = 6                              # a sway beat (step//2 odd) rides ON the spot
    s._paint_fx(p)
    assert cap["xshift"] == s.roamer.xshift - 1


def test_sick_shuffle_holds_the_roamers_spot(monkeypatch):
    from tuipet import anim as anim_mod
    cap = _capture_render(monkeypatch)
    s = _paint_harness()
    p = _pose_pet(poop=0, sick=True)
    s.paint(p)                                    # canon idleUnwell: Y reset only
    dx = anim_mod.sick_frame(0)[1]
    assert cap["xshift"] == s.roamer.xshift + dx


def test_startle_holds_the_roamers_spot(monkeypatch):
    cap = _capture_render(monkeypatch)
    s = _paint_harness()
    p = _pose_pet(anim="startle")
    s.paint(p)                                    # canon surprising(): jumps where it stands
    assert cap["xshift"] == s.roamer.xshift
    assert cap["mirror"] == s.roamer.mirror


def test_food_descends_beside_the_piles(monkeypatch):
    from tuipet.app import PET_BASE_X, _filth_right
    cap = _capture_render(monkeypatch)
    s = _paint_harness()
    p = _pose_pet(poop=1, poop_sizes=[2])
    s.fx = {"kind": "eat", "step": 0, "steps": 35, "icon": "f:0",
            "poop": 0, "old_num": None, "good": True}
    s._paint_fx(p)
    fw = 8                                        # 24px food downsampled to the LCD
    # canon pad: food+char slide right by the FULL filth width -- the food's
    # left edge (char left - fw) lands exactly at the filth block's right edge
    assert cap["xshift"] == (_filth_right(1) - PET_BASE_X) + fw
    assert PET_BASE_X + cap["xshift"] - fw >= _filth_right(1)


def test_food_descends_uncut_inside_the_window(monkeypatch):
    """Joel 2026-07-12: the descent's left columns were getting cut at the
    matrix edge (the no-poop scene born at x3).  The whole canon-abutted pair
    now slides right instead: every descent beat shows the food's FULL ink,
    entirely inside the 32x16 window."""
    from tuipet import grid
    cap = _capture_render(monkeypatch)
    s = _paint_harness()
    p = _pose_pet(poop=0)
    food = s._food_frames("f:0")
    ink = sum(r.count("1") for r in food[0])
    s.fx = {"kind": "eat", "step": 0, "steps": 35, "icon": "f:0",
            "poop": 0, "old_num": None, "good": True}
    for step in (0, 2, 4, 6):
        s.fx["step"] = step
        s._paint_fx(p)
        pts = cap["overlay"]
        assert len(pts) == ink, (step, len(pts), ink)      # nothing clipped away
        assert all(grid.X0 <= x < grid.X1 and grid.TOP <= y < grid.FLOOR
                   for x, y in pts), step
def test_emote_riders_pop_whole_inside_the_window(monkeypatch):
    """Joel 2026-07-12: 'why is the sun icon getting cut off' -- the cheer/
    jeer/dying emote bubbles were still blitted at the pre-law bezel spot
    (y=1), so the window clip beheaded them.  They now ride the pet's right
    edge at head height (grid.TOP): every up-beat shows the emote's FULL
    ink, entirely inside the 32x16 window."""
    from tuipet import data, grid
    cap = _capture_render(monkeypatch)
    E = data.load_effects()
    for kind, ekey in (("cheer", "happy"), ("jeer", "unhappy"),
                       ("dying", "dying")):
        s = _paint_harness()
        for m in ("_fxk_cheer", "_fxk_jeer", "_fxk_dying"):
            setattr(s, m, getattr(Screen, m).__get__(s))
        p = _pose_pet()
        ink = min(sum(r.count("1") for r in f) for f in E[ekey])
        s.fx = {"kind": kind, "step": 0, "steps": 31, "icon": None,
                "poop": 0, "old_num": None, "good": True}
        seen = False
        for step in range(14):
            s.fx["step"] = step
            s._paint_fx(p)
            pts = cap["overlay"]
            if not pts:
                continue                       # a down-beat: no bubble drawn
            seen = True
            assert len(pts) >= ink, (kind, step, len(pts), ink)
            assert all(grid.X0 <= x < grid.X1 and grid.TOP <= y < grid.FLOOR
                       for x, y in pts), (kind, step)
        assert seen, kind


def test_the_fx_engine_split_holds_its_boundaries():
    """Tier-2 split (2026-07-17): arenafx owns the fx engine; arena owns the
    widget; every old name resolves from arena (and app's re-export), and
    the render_screen patch point still catches fx frames."""
    import inspect
    from tuipet import arena, arenafx
    assert arenafx.FxMixin in arena.Screen.__mro__
    room = inspect.getsource(arena)
    for name in ("start_fx", "advance_fx", "_paint_fx", "_fxk_eat",
                 "_fxk_evolve"):
        assert f"def {name}" not in room, f"{name} crept back into arena"
        assert callable(getattr(arena.Screen, name))       # composed in
    for old in ("SCREEN_COLS", "PET_BASE_X", "GIFT_OUT", "PLAY_HOP",
                "_effect_overlay", "_FxCtx", "hearts", "bar"):
        assert hasattr(arena, old), old                    # re-export law
    # _paint_fx must route render_screen through ARENA (the documented spy)
    assert "_arena.render_screen" in inspect.getsource(arenafx.FxMixin._paint_fx)


def test_the_app_split_holds_its_boundaries():
    """Tier-3 split (2026-07-17): appactions owns every action_*/_after_*
    handler; appboot owns the launch plumbing; app.py is the shell and
    re-exports the old names."""
    import inspect
    from tuipet import app, appactions, appboot
    assert appactions.ActionsMixin in app.TuiPetApp.__mro__
    shell = inspect.getsource(app)
    for name in ("action_feed", "action_shop", "action_lobby",
                 "_after_feed", "_after_cup", "_do"):
        assert f"def {name}" not in shell, f"{name} crept back into the shell"
        assert callable(getattr(app.TuiPetApp, name))
    for name in ("host_platform", "_preflight", "_lobby_uri",
                 "MIN_COLS", "MIN_ROWS"):
        assert hasattr(app, name) and hasattr(appboot, name)


def test_dna_charge_badge_feeds_in_at_chip_scale():
    """The 14x14 field badge art was a small chip on the source's 60px stage
    but NEAR PET-SIZE on our 24px window (Joel 2026-07-22: "enlarged dna item
    sprites during the eating animation" -- the charge's feed-in).  It halves
    like the eat fx's food: every pre-wash frame keeps the badge inside an
    8x8 box, and the whole 44-step fx plays through."""
    from tuipet import arenafx

    class S:
        fx = None
        frame_i = 0
    for name in ("start_fx", "advance_fx", "_fxk_dna_charge",
                 "_pose_rows_idx", "_fx_filth"):
        setattr(S, name, getattr(Screen, name))

    def ctx():
        c = arenafx._FxCtx()
        c.rows = None; c.overlay = []; c.free = []; c.xshift = 0
        c.yshift = 0; c.bg = None; c.bgimg = None; c.px_h = 24; c.mirror = False
        return c

    s = S()
    p = Pet(num=29, stage="Champion", attribute="Vaccine")
    s.start_fx("dna_charge", icon="NatureSpirit", pet=p)
    for step in range(8, 21):                     # badge landed, wash not yet
        c = ctx()
        s._fxk_dna_charge(p, s.fx, step, c)
        xs = {pt[0] for pt in c.overlay}
        ys = {pt[1] for pt in c.overlay}
        assert max(xs) - min(xs) + 1 <= 8, f"step {step}: badge {max(xs)-min(xs)+1} wide"
        assert max(ys) - min(ys) + 1 <= 8, f"step {step}: badge {max(ys)-min(ys)+1} tall"
    # the badge EMERGES from behind the top bezel (window law: it never
    # pops) and the sink tail walks it fully off before the fx ends --
    # at 1px/tick the half-scale chip sat at the floor and blinked out
    # with the last frame (fx audit 2026-07-22)
    def lane_ink(step):
        c = ctx()
        s._fxk_dna_charge(p, s.fx, step, c)
        return sum(1 for pt in c.overlay if 6 <= pt[1] <= 22 and pt[0] < 13)
    assert lane_ink(4) > 0                        # peeking under the bezel
    assert lane_ink(4) < lane_ink(8)              # ...and growing: no pop
    assert lane_ink(43) == 0                      # sunk away before the end
    while s.fx is not None:                       # the full fx plays out
        s.advance_fx()
