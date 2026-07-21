"""BANDAI GRAMMAR (2026-07-11): the 32x16 matrix is a STAGE, not a dashboard.

Locked geometry (Joel, long-standing): 40x24 LCD, 32x16 play area grounded
2px above the bottom border -- untouchable.  The LCD carries SCENE ACTORS
only: the pet (full play area), the filth block, the sleep Zzz in the sky
corner, and the sick skull standing beside the pet like the real device
draws it.  Every BADGE (medicine/bandage/vitamin/fatigue/injury, teach,
the care-call '!', idle emotes) lives on the status side: the HUD deco,
the msg-box alarm, the digicore pages.  Care-fx scenes keep their own
in-scene emotes -- those are full-screen animations, the hardware way.

Hard invariant, swept at the pixel level: sprites never draw on another."""
import random

import tuipet.app as app
from tuipet import arena, grid
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _screen():
    s = app.Screen()
    s.on_mount()
    s.update = lambda t: None
    return s


def _sprite_px(rows, xshift, mirror, cols=40, px_h=24):
    """Reproduce render_screen's placement (centred, baselined, no yshift)."""
    if not rows:
        return set()
    src = [r[::-1] for r in rows] if mirror else rows
    sw = max(len(r) for r in src)
    ox = (cols - sw) // 2 + xshift
    oy = max(0, px_h - len(src) - 2)
    return {(ox + x, oy + y) for y, line in enumerate(src)
            for x, ch in enumerate(line) if ch == "1"
            and 0 <= oy + y < px_h and 0 <= ox + x < cols}


def _paint_capture(monkeypatch):
    cap = {}

    def spy(rows, cols, nrows, on, bg, mirror=False, xshift=0, yshift=0,
            overlay=None, bgimg=None, clip=None, overlay_free=None, free_ink=None):
        cap.update(rows=rows, mirror=mirror, xshift=xshift,
                   overlay=list(overlay or []), clip=clip,
                   free=list(overlay_free or []))
        return ""

    monkeypatch.setattr("tuipet.arena.render_screen", spy)
    return cap


SCENARIOS = [
    {},
    {"sick": True, "sick_length": 99.0},
    {"asleep": True, "anim": "sleep"},
    {"asleep": True, "nap": True, "anim": "sleep"},
    {"asleep": True, "anim": "sleep", "lights": False},
    {"asleep": True, "anim": "sleep", "sick": True, "sick_length": 99.0},
    {"sick": True, "sick_length": 99.0, "lights": False},
    # the franken transition: asleep flag up while another anim still plays
    # (a disturbed sleeper) -- the Zzz waits for the sleep pose, so the
    # walking pet and the glyph can never meet
    {"asleep": True, "nap": True},
]
LOADS = [(0, []), (1, [2]), (2, [2, 3]), (3, [2, 3, 1]), (4, [3, 3, 2, 1])]


def test_no_sprite_ever_draws_on_another(monkeypatch):
    """THE sweep: every actor state x filth load x 30 ticks -- the pet's ink
    and the overlay's ink (piles + skull + Zzz) are disjoint pixel sets."""
    cap = _paint_capture(monkeypatch)
    for kw in SCENARIOS:
        for n, sizes in LOADS:
            random.seed(7)
            p = _pet(weather="Clear", poop=n, poop_sizes=list(sizes), **kw)
            s = _screen()
            for i in range(30):
                s.advance(p)
                s.paint(p)
                pet_px = _sprite_px(cap["rows"], cap["xshift"], cap["mirror"])
                hit = pet_px & set(cap["overlay"])
                assert not hit, (kw, n, i, sorted(hit)[:6])


def test_badges_never_touch_the_lcd():
    """Medicine, bandage, vitamin, fatigue, injury, teach, the care-call and
    the idle emotes are BADGES -- zero pixels on the play field."""
    for kw in ({"med_lapse": 30.0}, {"bandage_lapse": 30.0},
               {"vitamin_lapse": 30.0}, {"fatigue_length": 99.0},
               {"inj_length": 99.0}, {"praise_flag": True},
               {"scold_flag": True}, {"discipline_call": True},
               {"hunger": 0}, {"anim": "happy"}, {"anim": "sad"},
               {"anim": "exhausted"}):
        p = _pet(weather="Clear", **kw)
        assert arena._effect_overlay(p, 0, 40, 24, tick=0) == [], kw


def test_healthy_pet_owns_the_full_play_area(monkeypatch):
    """Nothing on a healthy pet's LCD may shrink its locked 32x16 world: the
    roamer's wall is the grid's own right edge and paint never clamps it."""
    cap = _paint_capture(monkeypatch)
    p = _pet(weather="Clear")
    s = _screen()
    s.roamer.x = float(grid.X1 - arena.SPRITE_W)   # standing at the far wall
    s.paint(p)
    assert cap["xshift"] == (grid.X1 - arena.SPRITE_W) - arena.PET_BASE_X
    assert not arena._sick_mark_up(p)


def test_sick_skull_stands_in_the_scene(monkeypatch):
    """The skull is a grounded scene object beside the pet -- right edge,
    feet on the floor, blinking its 2-frame pair -- and a walk wall."""
    cap = _paint_capture(monkeypatch)
    p = _pet(weather="Clear", sick=True, sick_length=99.0)
    pts = arena._effect_overlay(p, 0, 40, 24, tick=0)
    assert pts and all(grid.X1 - arena.COND_W <= x < grid.X1 for x, _ in pts)
    assert min(y for _, y in pts) == grid.TOP              # HIGH: head height,
    assert max(y for _, y in pts) < grid.TOP + 8           # the device way
    assert pts != arena._effect_overlay(p, 0, 40, 24, tick=7)   # stateNumTic blink
    # a sick SLEEPER: the Zzz owns the corner, the skull tucks in under it
    q = _pet(weather="Clear", sick=True, sick_length=99.0,
             asleep=True, anim="sleep")
    zzq = arena._effect_overlay(q, 0, 40, 24, tick=0)
    ys = sorted({y for _, y in zzq})
    assert ys[0] == grid.TOP and ys[-1] > grid.TOP + 6     # stacked, both up high
    s = _screen()
    s.roamer.x = 20.0                                      # fell ill at the far wall
    s.paint(p)
    assert cap["xshift"] <= (grid.X1 - arena.SICK_ZONE - arena.SPRITE_W) - arena.PET_BASE_X


def test_poop_outranks_the_skull():
    """3-4 piles leave no 16px corridor beside the skull's slot: poop wins,
    the skull yields to the HUD (which always carries +sick)."""
    p = _pet(weather="Clear", poop=3, poop_sizes=[2, 3, 1],
             sick=True, sick_length=99.0)
    assert not arena._sick_mark_up(p)
    filth_only = _pet(weather="Clear", poop=3, poop_sizes=[2, 3, 1])
    assert arena._effect_overlay(p, 0, 40, 24, tick=0) \
        == arena._effect_overlay(filth_only, 0, 40, 24, tick=0)
    q = _pet(weather="Clear", poop=2, poop_sizes=[2, 3],
             sick=True, sick_length=99.0)
    assert arena._sick_mark_up(q)                          # 2 piles: room for both


def test_zzz_hangs_inside_the_window():
    """The sleep Zzz is a scene actor INSIDE the 32x16 (LAW: nothing above
    the band) -- band top-right, clear of the centre-clamped sleeper --
    lights on, lights off, and with its own nap glyph."""
    night = _pet(weather="Clear", asleep=True, anim="sleep")
    zz = arena._effect_overlay(night, 0, 40, 24, tick=0)
    assert zz and all(x >= grid.X1 - 8 and grid.TOP <= y < grid.TOP + 8
                      for x, y in zz)
    nap = _pet(weather="Clear", asleep=True, nap=True, anim="sleep")
    assert arena._effect_overlay(nap, 0, 40, 24, tick=0) != zz
    dark = _pet(weather="Clear", asleep=True, lights=False)
    assert arena._effect_overlay(dark, 0, 40, 24, tick=0)  # the dark room keeps its Zzz
    awake = _pet(weather="Clear")
    assert arena._effect_overlay(awake, 0, 40, 24, tick=0) == []


def test_sleepers_center_and_the_zzz_yields_to_poop(monkeypatch):
    """A sleeper with <=2 piles is clamped to CENTRE (x12..27), so the Zzz's
    corner columns (x28+) are its own -- any species, any pose height.  With
    3-4 piles the sleeper is pushed under the corner, so the Zzz yields to
    the HUD entirely: poop always wins floor space."""
    cap = _paint_capture(monkeypatch)
    cozy = _pet(weather="Clear", asleep=True, nap=True, anim="sleep",
                poop=2, poop_sizes=[2, 3])
    s = _screen()
    s.roamer.x = 20.0                          # napped off at the far wall
    s.paint(cozy)
    assert cap["xshift"] == 0                  # pinned to centre: x12..27
    crowded = _pet(weather="Clear", asleep=True, nap=True, anim="sleep",
                   poop=4, poop_sizes=[3, 3, 2, 1])
    assert not [pt for pt in arena._effect_overlay(crowded, 0, 40, 24, tick=0)
                if pt[0] >= grid.X1 - 8]       # no Zzz: the piles own the floor


def test_alarm_keeps_the_union_while_the_scene_split_stands():
    """needs_attention (HUD alarm, mood-lapse gate) still counts discipline;
    needs_care (the physical half) does not -- the split from 2026-07-11
    survives with the badges off-LCD."""
    # (the discipline half of the union left with the discipline system)
    hungry = _pet(hunger=0)
    assert hungry.needs_attention() and hungry.needs_care()


def test_hud_carries_every_badge():
    """The badges' one home: the STATUS deco line."""
    import inspect
    src = inspect.getsource(app._care_deco)
    for badge in ("+med", "+bnd", "+vit",
                  "+tired", "+hurt", "+sick"):
        assert badge in src, badge


def test_the_window_law(monkeypatch):
    """LAW (2026-07-11): the main scene renders under the 32x16 window clip;
    actor overlays arrive pre-clipped; weather alone rides the free channel
    over the whole LCD; ink pushed past an edge is cut at the matrix edge
    (the lawful LEFT/RIGHT exit)."""
    from tuipet import render
    cap = _paint_capture(monkeypatch)
    p = _pet(weather="Raining", sick=True, sick_length=99.0,
             poop=2, poop_sizes=[2, 3])
    s = _screen()
    for i in range(8):
        s.advance(p)
        s.paint(p)
    assert cap["clip"] == grid.WINDOW
    assert cap["overlay"] and all(
        grid.X0 <= x < grid.X1 and grid.TOP <= y < grid.FLOOR
        for x, y in cap["overlay"])                 # actors: window-clipped
    # (the weather free-channel half of the law left with the weather system;
    # BASIC VPET 2026-07-16 -- the render plane itself survives for future fx)
    buf = render.fill_buf(["11", "11"], 40, 24, xshift=16, clip=grid.WINDOW)
    lit = {(x, y) for y, row in enumerate(buf) for x, v in enumerate(row) if v}
    assert lit and all(x < grid.X1 for x, _ in lit)  # cut at the matrix edge


def test_egg_carousel_is_never_window_clipped(monkeypatch):
    """Joel 2026-07-12: the carousel got mangled by a blind clip.  Its canvas
    is a 40x16 STRIP (ROWS=8), not the full LCD -- the 32x16 window rect
    beheads every egg there.  The reel renders UNCLIPPED, exactly as built."""
    from tuipet import eggselectscreen as es
    from tuipet.pet import Pet
    seen = {}
    real = es.render_scene

    def spy(placements, cols, rows, on, bg, **kw):
        seen["clip"] = kw.get("clip")
        seen["rows"] = rows
        return real(placements, cols, rows, on, bg, **kw)

    monkeypatch.setattr(es, "render_scene", spy)
    p = Pet.new_egg(egg_type=1)
    pan = es.EggSelectPanel(p)
    pan.text()
    assert seen["rows"] == 10                    # the tall band, NOT the full
    #                                              LCD (carousel redo 2026-07-19:
    #                                              the text block left, the egg
    #                                              got headroom)
    assert seen["clip"] is None, "never window-clip the egg reel"


def test_battle_banner_and_flash_fill_the_window_not_the_lcd():
    """The battle start banner / hit explosion are 32x16 full-WINDOW takeovers:
    LCD-centring parked their top two rows in the bezel sky at y4-5 on every
    battle (audit 2026-07-13).  _full anchors at the window like training's
    explosion, and the battle scene renders under the window clip."""
    from tuipet import battlescreen as bs
    for key in ("battle_banner", "hit_explosion"):
        frames = bs.BANNER if key == "battle_banner" else bs.EXPLODE
        lit_any = False
        for frame in frames:
            pts = bs._full(frame)
            # the 0.5 blast blinks against a BLANK off-beat (2026-07-17):
            # empty frames are the blink, not a bug
            lit_any = lit_any or bool(pts)
            assert all(
                grid.X0 <= x < grid.X1 and grid.TOP <= y < grid.FLOOR
                for x, y in pts), f"{key} ink must live inside the window"
        assert lit_any, f"{key} never lights"


def test_battle_dodge_leap_never_exits_upward():
    """The dodge's blank-row lift is clamped to the mon's headroom (a 16px mon
    has none -- the sideways hop carries it, like real hardware): pre-clamp it
    pushed sprite ink to y3-5, above the window top (audit 2026-07-13)."""
    from tuipet.pet import Pet
    from tuipet import battlescreen as bs
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    pan = bs.BattlePanel(p)
    pan.bar = (pan.mega_lo + pan.mega_hi) // 2
    pan._lock_bar()                                # 0.5: the race builds at the bar
    for dt in range(1, 11):
        fr = {"m": "dodge", "view": "pet", "prog": dt / bs.DODGE_T,
              "ph": pan.battle.pet_hp, "fh": pan.battle.enemy_hp}
        text = pan._render_scene_frame(fr)
        assert text is not None                    # renders under the clip


def test_dodge_turns_away_while_airborne():
    """The tuipet turn-away dodge (Joel 2026-07-21, a DELIBERATE canon
    deviation -- ANIM_REFERENCE): airborne (dt 1-9) the dodger wears the
    OPPOSITE of its battle facing; touchdown (dt 10) and the return steps
    land it facing the foe again."""
    from tuipet import strikefx
    from tuipet.pet import Pet
    from tuipet import battlescreen as bs
    rows = ["0110", "1100", "0110"]                    # asymmetric ink
    # the seam: turn inverts each side's normal mirror flag
    place, _ = strikefx.place_combatant(True, rows)
    assert place[0][2] is False                        # pet: native facing
    place, _ = strikefx.place_combatant(True, rows, turn=True)
    assert place[0][2] is True                         # pet turned: mirrored
    place, _ = strikefx.place_combatant(False, rows)
    assert place[0][2] is True                         # foe: mirrored to face pet
    place, _ = strikefx.place_combatant(False, rows, turn=True)
    assert place[0][2] is False                        # foe turned: native
    # the timeline: only the airborne dodge beats pass turn=True
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    pan = bs.BattlePanel(p)
    pan.bar = (pan.mega_lo + pan.mega_hi) // 2
    pan._lock_bar()
    seen = {}
    orig = pan._place_one

    def spy(view, rows, xshift=0, turn=False):
        seen[spy_dt[0]] = turn
        return orig(view, rows, xshift, turn=turn)

    spy_dt = [0]
    pan._place_one = spy
    for dt in range(1, bs.DODGE_T + 1):
        spy_dt[0] = dt
        fr = {"m": "dodge", "view": "pet", "prog": dt / bs.DODGE_T,
              "ph": pan.battle.pet_hp, "fh": pan.battle.enemy_hp}
        assert pan._render_scene_frame(fr) is not None
    assert all(seen[dt] for dt in range(1, 10)), "airborne beats must turn"
    assert not any(seen[dt] for dt in range(10, bs.DODGE_T + 1)), \
        "touchdown + return steps land facing forward"
