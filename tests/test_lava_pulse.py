"""The lava ember pulse (background polish 2026-07-15, after the twinkle):
Volcano's flow breathes -- ember pixels dim toward deep red and flare toward
yellow-white on a slow ripple.  Lava is detected on the NIGHT frame (self-
luminous in the dark), which is what keeps desert sand and dusk skies still;
the pulse then rides every look of the sheet: phase picks, the overcast
deck, and the star-twinkle beats."""
from tuipet import data, theme
from tuipet.pet import Pet, DAY_LENGTH


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine", energy=24, max_energy=24,
            obedience=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _volcano_hab():
    return next(hid for hid, h in data.load_habitats().items()
                if h["bg"] == "volcano")


def test_only_the_volcano_holds_embers():
    bgs = data.load_backgrounds()
    flows = [k for k, fr in bgs.items() if fr and len(fr) > 4
             and theme._find_lava(fr)]
    assert flows == ["volcano"], flows


def test_pulse_touches_only_ember_pixels_and_swings_both_ways():
    bgs = data.load_backgrounds()
    frames = bgs["volcano"]
    coords = theme._find_lava(frames)
    day = frames[1]
    W = len(day[0]) // 6
    dimmed = flared = 0
    for beat in range(theme._EM_BEATS):
        em = theme._apply_embers(day, coords, beat)
        diff = [(x, y) for y in range(len(day)) for x in range(W)
                if em[y][x * 6:(x + 1) * 6] != day[y][x * 6:(x + 1) * 6]]
        assert diff, f"beat {beat}: the flow held still"
        assert set(diff) <= set(coords), f"beat {beat}: non-ember pixels moved"
        for x, y in diff:
            was = theme._luma(theme._cell(day, x, y))
            now = theme._luma(theme._cell(em, x, y))
            dimmed += now < was
            flared += now > was
    assert dimmed and flared


def test_ember_frames_are_deterministic_and_cached():
    bgs = data.load_backgrounds()
    frames = bgs["volcano"]
    a = theme.ember_frame("volcano", frames, frames[1], ("f", 1), 0.0)
    assert theme.ember_frame("volcano", frames, frames[1], ("f", 1), 0.0) is a
    b = theme.ember_frame("volcano", frames, frames[1], ("f", 1),
                          theme._EM_STEP)
    assert a != b                                 # the next beat moved
    # a sheet with no flow passes the frame through untouched
    pf = bgs["egg1Back"]
    assert theme.ember_frame("egg1Back", pf, pf[1], ("f", 1), 0.0) is pf[1]


def test_volcano_background_breathes_day_and_night():
    hab = _volcano_hab()
    hr = DAY_LENGTH / 24
    bgs = data.load_backgrounds()
    frames = bgs["volcano"]
    p = _pet(habitat=hab, weather="Clear")
    day_hr = next(h for h in range(24)
                  if [setattr(p, "world_seconds", h * hr)]
                  and p.day_phase == "day")
    p.world_seconds = day_hr * hr
    assert p.background() == theme.ember_frame(
        "volcano", frames, frames[1], ("f", 1), p.world_seconds)
    a = p.background()
    p.world_seconds += theme._EM_STEP
    assert p.background() != a                    # the flow breathed
    # night: the twinkle AND the pulse compose on the same frame
    p.world_seconds = 1 * hr
    assert p.day_phase == "night"
    tw = theme.star_frame("volcano", frames, p.world_seconds)
    assert tw is not None
    assert p.background() == theme.ember_frame(
        "volcano", frames, tw, ("tw", theme.tw_beat(p.world_seconds)),
        p.world_seconds)


