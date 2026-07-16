"""Twinkling stars (background polish 2026-07-15): a CLEAR night's starfield
shimmers -- each detected star dims toward the flat night sky and back on its
own offset of a 4-beat cycle.  Every pixel derives from the sheet's own night
frame (nothing is drawn); starless sheets keep the plain frame; cloudy nights
never twinkle (the overcast deck covers the stars)."""
from tuipet import data, theme
from tuipet.pet import Pet, DAY_LENGTH


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine", energy=24, max_energy=24,
            obedience=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _cells(frame):
    return [(int(r[i:i + 2], 16), int(r[i + 2:i + 4], 16), int(r[i + 4:i + 6], 16))
            for r in frame for i in range(0, len(r), 6)]


def test_every_open_sky_sheet_has_a_starfield():
    bgs = data.load_backgrounds()
    starless = [k for k, fr in bgs.items() if fr and len(fr) > 4
                and theme._find_stars(fr) is None]
    assert sorted(starless) == ["egg10Back", "egg7Back"], starless
    # the twinkle's stricter LONE-star mask (the gate's dots are moon rims
    # and cloud edges as often as stars): Lake's dots are all rim, so it
    # holds still with the wall and the seafloor
    still = [k for k, fr in bgs.items() if fr and len(fr) > 4
             and theme._twinkle_stars(fr) is None]
    assert sorted(still) == ["egg10Back", "egg6Back", "egg7Back"], still


def test_twinkle_touches_only_lone_star_pixels():
    bgs = data.load_backgrounds()
    frames = bgs["egg1Back"]
    stars, nsky = theme._twinkle_stars(frames)
    night = frames[3]
    W = len(night[0]) // 6
    dimmed = flared = 0
    for beat in range(theme._TW_BEATS):
        tw = theme._build_twinkle(frames, stars, nsky, beat)
        diff = [(x, y) for y in range(len(night)) for x in range(W)
                if tw[y][x * 6:(x + 1) * 6] != night[y][x * 6:(x + 1) * 6]]
        assert diff, f"beat {beat}: nothing shimmers"
        assert set(diff) <= set(stars), f"beat {beat}: non-star pixels changed"
        for x, y in diff:
            was = theme._luma(theme._cell(night, x, y))
            now = theme._luma(theme._cell(tw, x, y))
            if now < was:
                dimmed += 1
            elif now > was:
                flared += 1
    # the curve swings BOTH ways -- faint stars need the flare to read
    assert dimmed and flared
    # the moon never twinkles: its bright rim is not a lone star
    moon = [(x, y) for y in range(len(night)) for x in range(W)
            if theme._luma(theme._cell(night, x, y)) > 200]
    assert not set(moon) & set(stars)


def test_each_beat_is_distinct_deterministic_and_cached():
    bgs = data.load_backgrounds()
    frames = bgs["desert"]
    seen = [theme.star_frame("desert", frames, b * theme._TW_STEP)
            for b in range(theme._TW_BEATS)]
    assert len({tuple(f) for f in seen}) == theme._TW_BEATS
    again = theme.star_frame("desert", frames, 0.0)
    assert again is seen[0]                       # cached object, not a rebuild
    # the cycle wraps: beat N == beat 0
    assert theme.star_frame(
        "desert", frames, theme._TW_BEATS * theme._TW_STEP) is seen[0]


def test_clear_night_background_twinkles():
    p = _pet(habitat=2, weather="Clear")          # Plains: a starfield sheet
    hr = DAY_LENGTH / 24
    p.world_seconds = 1 * hr                      # 1:00 -- deep night
    assert p.day_phase == "night"
    key = p.habitat_obj()["bg"]
    frames = data.load_backgrounds()[key]
    assert p.background() == theme.star_frame(key, frames, p.world_seconds)
    a = p.background()
    p.world_seconds += theme._TW_STEP             # next beat: the sky moved
    b = p.background()
    assert a != b
    assert a != frames[3] or b != frames[3]       # it really is a variant


def test_starless_nights_do_not_twinkle():
    hr = DAY_LENGTH / 24
    p = _pet(habitat=8)                           # Underwater: no stars
    p.world_seconds = 1 * hr
    f = data.load_backgrounds()[p.habitat_obj()["bg"]]
    assert p.background() == f[3]                 # the plain night frame


def test_daytime_never_twinkles():
    p = _pet(habitat=2)
    p.world_seconds = 15 * DAY_LENGTH / 24        # inside Plains' day band
    assert p.day_phase == "day"
    key = p.habitat_obj()["bg"]
    frames = data.load_backgrounds()[key]
    assert p.background() == frames[1]
