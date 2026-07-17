"""Background audit 2026-07-15 vs BackgroundAnim.java: the animateBack
dissolve -- plus the BASIC VPET re-pins (2026-07-17): the home scene is the
egg's single-frame DSprite backdrop (phase-invariant), day_phase rides a
FIXED daylight triple, and only the arena's 5-frame sheet still tracks the
clock (the per-habitat triples, weather tints and the winter-sunset quirk
left with their systems)."""
from tuipet import theme
from tuipet.pet import Pet, DAY_LENGTH


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine", energy=24, max_energy=24,
            obedience=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _brightness(frame):
    tot = n = 0
    for row in frame:
        for i in range(0, len(row), 6):
            tot += (int(row[i:i + 2], 16) + int(row[i + 2:i + 4], 16)
                    + int(row[i + 4:i + 6], 16)) / 3
            n += 1
    return tot / n


_WHITE = ["ffffff" * 8] * 4


def test_home_scene_is_phase_invariant_but_the_arena_still_tracks_the_clock():
    # the DSprite home scenes are one look each; tourneyBack keeps its
    # 5-frame sheet, so the ARENA still darkens at night
    p = _pet(egg_type=0)
    hr = DAY_LENGTH / 24
    p.world_seconds = 15 * hr
    home_day, arena_day = p.background(), p.background(file="tourneyBack")
    p.world_seconds = 1 * hr
    home_night, arena_night = p.background(), p.background(file="tourneyBack")
    assert home_day and home_day == home_night      # one look, day or night
    assert _brightness(arena_night) < _brightness(arena_day)


def test_day_phase_rides_the_fixed_triple():
    # checkTime on the fixed (6, 14, 19) triple: Morning/Noon/Night with the
    # last Noon hour as the sunset -> dusk, in EVERY season
    p = _pet()
    hr = DAY_LENGTH / 24
    for day0 in (0.0, 39 * DAY_LENGTH):             # Spring and Winter alike
        for hour, want in ((3, "night"), (7, "dawn"), (15, "day"),
                           (18.5, "dusk"), (20, "night")):
            p.world_seconds = day0 + hour * hr
            assert p.day_phase == want, (day0, hour)


def test_background_swap_dissolves_instead_of_cutting():
    # animateBack: BackgroundOpacityChange -0.05/tick -- a swap eases through
    # intermediate frames and lands exactly on the target
    from tuipet import arena
    s = arena.Screen()
    a = ["000000" * 8] * 4
    b = ["ffffff" * 8] * 4
    assert s._crossfade(a) == a                     # first show: no fade
    mid = s._crossfade(b)
    assert mid != a and mid != b                    # easing, not cutting
    last = mid
    for _ in range(arena.Screen.BG_FADE):
        last = s._crossfade(b)
    assert last == b                                # fade completes on target


def test_crossfade_retargets_from_the_visible_frame():
    # a mid-fade weather flap (rain -> clear -> rain) must fade back from
    # whatever is on screen, never jump
    from tuipet import arena
    s = arena.Screen()
    a = ["000000" * 8] * 4
    b = ["ffffff" * 8] * 4
    s._crossfade(a)
    shown = s._crossfade(b)
    back = s._crossfade(a)                          # flap back mid-fade
    assert _brightness(back) <= _brightness(shown) + 1


# ---- the derived cloudy-night frame (background rebuild 2026-07-15) ----------
# The shipped overcast frame is day-bright, so a clouded night looked like
# noon ("it looks like day cloudy, because thats all we got" -- Joel).  Each
# sheet with an open sky gets a cloudy-night frame derived from its OWN
# pixels: night ground verbatim, the overcast texture posterized into dark
# night-sky tones, the moon and stars covered.

from tuipet import data


def _cells(frame):
    return [(int(r[i:i + 2], 16), int(r[i + 2:i + 4], 16), int(r[i + 4:i + 6], 16))
            for r in frame for i in range(0, len(r), 6)]


