"""The status rail (icon-rail redesign 2026-07-10) -- tuipet's own layout,
off DVPet's creature-tracking scheme, with ONE hard invariant swept at the
pixel level: sprites never draw on top of each other.

Zones: filth block bottom-left (settled; always wins floor space), the pet's
corridor between the piles and the rail, every icon in the fixed right-edge
rail (Zzz -> conditions -> one reaction slot).  When 3-4 piles leave no 16px
corridor the rail yields (sky-strip icons only) and the HUD carries status."""
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
            overlay=None, bgimg=None):
        cap.update(rows=rows, mirror=mirror, xshift=xshift,
                   overlay=list(overlay or []))
        return ""

    monkeypatch.setattr("tuipet.arena.render_screen", spy)
    return cap


# every icon-bearing state x filth loads (weather Clear so the captured
# overlay is exactly the effect overlay -- rain is ambient, not a sprite)
SCENARIOS = [
    {},
    {"sick": True, "sick_length": 99.0},
    {"med_lapse": 30.0},
    {"inj_length": 99.0, "bandage_lapse": 30.0},
    {"fatigue_length": 99.0, "vitamin_lapse": 30.0},
    {"sick": True, "sick_length": 99.0, "med_lapse": 30.0, "inj_length": 99.0,
     "bandage_lapse": 30.0, "vitamin_lapse": 30.0, "fatigue_length": 99.0},
    {"asleep": True},
    {"asleep": True, "nap": True},
    {"asleep": True, "lights": False},
    {"asleep": True, "sick": True, "sick_length": 99.0},
    {"anim": "happy"}, {"anim": "sad"}, {"anim": "exhausted"},
    {"praise_flag": True},
    {"hunger": 0},                                   # the care-call '!'
]
LOADS = [(0, []), (1, [2]), (2, [2, 3]), (3, [2, 3, 1]), (4, [3, 3, 2, 1])]


def test_no_sprite_ever_draws_on_another(monkeypatch):
    """THE sweep: for every state x filth load x 30 ticks, the pet's ink and
    the overlay's ink (piles + rail icons) are disjoint pixel sets."""
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


def test_icons_are_fixed_nothing_follows_the_pet(monkeypatch):
    """The DVPet tracking mechanic is gone: the overlay is a pure function of
    pet STATE -- park the roamer anywhere, the icons don't move."""
    for kw in ({"anim": "happy"}, {"asleep": True}, {"sick": True,
                "sick_length": 99.0}, {"praise_flag": True}):
        p = _pet(weather="Clear", **kw)
        a = arena._effect_overlay(p, 2, 40, 24, tick=8)
        b = arena._effect_overlay(p, 2, 40, 24, tick=8)   # same state, same spot
        assert a == b
    # and the signature itself takes no pet position anymore
    import inspect
    assert "pet_right" not in inspect.signature(arena._effect_overlay).parameters


def test_rail_stacks_right_aligned_top_down():
    p = _pet(sick=True, sick_length=99.0, inj_length=99.0)
    pts = arena._effect_overlay(p, 0, 40, 24, tick=0)
    rail = [pt for pt in pts if pt[0] >= grid.X1 - arena.RAIL_W]
    assert rail and all(x < grid.X1 for x, _ in rail)
    ys = {y for _, y in rail}
    assert min(ys) <= 1 and len(ys) > 7          # two 7px icons stacked from the top
    #      (<=1: the state.png art keeps a blank padding row inside its cell)
    assert 7 not in ys                           # the 1px slot gap


def test_rail_overflow_takes_turns_instead_of_dropping():
    """Six conditions cannot fit the 24px rail; the old column silently
    dropped the surplus -- now the last slot cycles through them."""
    p = _pet(sick=True, sick_length=99.0, med_lapse=30.0, inj_length=99.0,
             bandage_lapse=30.0, vitamin_lapse=30.0, fatigue_length=99.0)
    assert len(arena._rail_items(p, 0, 0)) >= 6   # 6 conditions (+ the care-call slot)
    frames = {frozenset(pt for pt in arena._effect_overlay(p, 0, 40, 24, tick=t)
                        if pt[1] >= 16)          # the last slot's band
              for t in range(0, 140, 14)}
    assert len(frames) > 2                       # genuinely cycling, not stuck


def test_crowded_filth_pins_the_pet_and_the_rail_yields(monkeypatch):
    """3-4 piles leave no 16px corridor: poop tiles WIN -- the pet stands
    beside them and no band-height icon may share its floor."""
    cap = _paint_capture(monkeypatch)
    p = _pet(weather="Clear", poop=4, poop_sizes=[3, 3, 2, 1],
             sick=True, sick_length=99.0)
    s = _screen()
    s.paint(p)
    assert cap["xshift"] == arena._filth_right(4) - arena.PET_BASE_X
    pts = arena._effect_overlay(p, 0, 40, 24, tick=0)
    assert not [pt for pt in pts if pt[0] >= grid.X1 - arena.RAIL_W], \
        "band-height icons must yield when crowded (the HUD carries them)"
    # ...but the sky strip still works: a sleeper's Zzz fits above the band
    q = _pet(weather="Clear", poop=4, poop_sizes=[3, 3, 2, 1], asleep=True)
    zz = [pt for pt in arena._effect_overlay(q, 0, 40, 24, tick=0)
          if pt[0] >= grid.X1 - arena.RAIL_W]
    assert zz and all(y < grid.TOP for _, y in zz)
    assert not arena._rail_reserved(q)           # crowded: no corridor claim


def test_rail_reservation_is_one_shared_predicate(monkeypatch):
    """advance()'s roamer wall and paint()'s clamp both key off
    _rail_reserved -- a sick pet parked far right snaps into the corridor."""
    cap = _paint_capture(monkeypatch)
    p = _pet(weather="Clear", sick=True, sick_length=99.0)
    assert arena._rail_reserved(p)
    s = _screen()
    s.roamer.x = 20.0                            # fell ill standing at the right wall
    s.paint(p)
    assert cap["xshift"] <= (grid.X1 - arena.RAIL_W - arena.SPRITE_W) - arena.PET_BASE_X
    calm = _pet(weather="Clear")
    calm.hunger, calm.strength = 4, 4            # no care-call: rail empty
    assert not arena._rail_reserved(calm)


def test_hud_carries_the_badge_conditions():
    """The rail can yield (crowded) -- the HUD status line is the always-on
    truth, so the badge conditions joined it."""
    p = _pet(med_lapse=30.0, bandage_lapse=30.0, vitamin_lapse=30.0)
    assert p.has_medicine() and p.has_bandage() and p.has_vitamin()
    import inspect
    src = inspect.getsource(app.Stats.paint)
    assert "+med" in src and "+bnd" in src and "+vit" in src
