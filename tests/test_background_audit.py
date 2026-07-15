"""Background audit 2026-07-15 vs BackgroundAnim.java: the precip frame's
time-of-day tint (getBackgroundTint), the animateBack dissolve, and
isSunset's winter-triple quirk."""
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


def test_night_precip_tint_darkens_past_the_day_tint():
    # getBackgroundTint: Night bumps the precip overlay alpha 40 -> 80 --
    # the day-bright shared precip frame must render darker at night
    for w in ("Raining", "LightSnow"):
        day = _brightness(theme.weather_tint(_WHITE, w, "day"))
        night = _brightness(theme.weather_tint(_WHITE, w, "night"))
        assert night < day, f"{w}: night precip no darker than day"


def test_dawn_and_dusk_precip_get_their_canon_casts():
    # Morning blue=80, sunset red=60 (changeColor(red, 0, blue, alpha))
    def rgb_means(frame):
        r = g = b = n = 0
        for row in frame:
            for i in range(0, len(row), 6):
                r += int(row[i:i + 2], 16); g += int(row[i + 2:i + 4], 16)
                b += int(row[i + 4:i + 6], 16); n += 1
        return r / n, g / n, b / n
    day = rgb_means(theme.weather_tint(_WHITE, "Raining", "day"))
    dawn = rgb_means(theme.weather_tint(_WHITE, "Raining", "dawn"))
    dusk = rgb_means(theme.weather_tint(_WHITE, "Raining", "dusk"))
    assert dawn[2] - dawn[0] > day[2] - day[0]      # dawn: bluer than day
    assert dusk[0] - dusk[2] > day[0] - day[2]      # dusk: redder than day


def test_cloudy_gets_no_phase_tint():
    # canon: only precip is phase-modulated -- Cloudy already shows the
    # normal time-of-day frame under the flat base tint
    assert (theme.weather_tint(_WHITE, "Cloudy", "night")
            == theme.weather_tint(_WHITE, "Cloudy", "day"))


def test_night_rain_background_is_darker_than_day_rain():
    # end to end: the same habitat sheet, rain at noon vs rain at midnight
    p = _pet(habitat=2, weather="Raining")
    hr = DAY_LENGTH / 24
    p.world_seconds = 15 * hr                       # inside Plains' 14-19 day band
    day = p.background()
    p.world_seconds = 1 * hr
    night = p.background()
    assert day and night
    assert _brightness(night) < _brightness(day)


def test_winter_sunset_reads_the_winter_triple():
    # isSunset's Winter case is getWinterTime()[2]-1 while checkTime's bands
    # ride the Fall triple -- Plains winter: dusk at 16:00, DAY again 17-18
    p = _pet(habitat=2)
    p.world_seconds = 39 * DAY_LENGTH               # day 39 = Winter (13-day seasons)
    assert p.season == "Winter"
    hr = DAY_LENGTH / 24
    times = p.habitat_obj()["times"]
    w_sunset = times["Winter"][2] - 1               # 16 on Plains
    f_sunset = times["Fall"][2] - 1                 # 18 on Plains
    assert w_sunset != f_sunset                     # the quirk is observable here
    p.world_seconds = 39 * DAY_LENGTH + (w_sunset + 0.5) * hr
    assert p.day_phase == "dusk"
    p.world_seconds = 39 * DAY_LENGTH + (f_sunset + 0.5) * hr
    assert p.day_phase == "day"


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
