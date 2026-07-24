"""HOLIDAY DECORATIONS — a festival prop on the home arena (2026-07-24).

Joel: "wire it up".  The functional festival system (double bits, town
sales, festival eggs) was already live; this adds the missing VISUAL layer
-- a small prop in the arena's top-left corner on each of the four holiday
days.

Three ride real ripped icons already aboard (candy, cake, a Digi-crest for
the Odaiba anniversary); the present is the one drawn prop (design A).  The
food icons are stored at 3x, so they are downsampled back to native 8x8 --
reversing a clean integer upscale, not a lossy shrink.
"""
import datetime

from tuipet import arenafx, grid
from tuipet.pet import Pet
from tuipet.render import blit as _blit

DATES = {
    "Halloween Festival": datetime.date(2026, 10, 31),
    "Christmas Festival": datetime.date(2026, 12, 25),
    "Odaiba Memorial Day": datetime.date(2026, 8, 1),
    "New Year Festival": datetime.date(2026, 1, 1),
}


def test_every_holiday_maps_to_a_decoration():
    from tuipet import tournament
    for name in tournament.HOLIDAYS.values():
        assert name in arenafx.HOLIDAY_DECOR, name
        assert arenafx._holiday_decor(DATES[name]) is not None, name


def test_an_ordinary_day_has_no_decoration():
    for d in (datetime.date(2026, 6, 15), datetime.date(2026, 3, 3)):
        assert arenafx._holiday_decor(d) is None


def test_each_decoration_is_corner_sized_and_in_window():
    for name, d in DATES.items():
        deco = arenafx._holiday_decor(d)
        w = max(len(r) for r in deco)
        h = len(deco)
        assert w <= 10 and h <= 10, (name, w, h)     # fits a corner
        for x, y in _blit(deco, grid.X0, grid.TOP):
            assert grid.X0 <= x < grid.X1, (name, "x", x)
            assert grid.TOP <= y < grid.FLOOR, (name, "y", y)


def test_the_present_is_the_drawn_prop():
    assert arenafx.HOLIDAY_DECOR["Christmas Festival"] == "present"
    assert arenafx._holiday_decor(DATES["Christmas Festival"]) == arenafx._PRESENT
    assert len(arenafx._PRESENT) == 8 and all(len(r) == 8 for r in arenafx._PRESENT)


def test_the_food_props_are_recovered_native_not_upscaled():
    """candy/cake are 3x food cells; the decoration must be the 8x8 native,
    not the 24px focal icon (which would fill half the band)."""
    for name in ("Halloween Festival", "New Year Festival"):
        deco = arenafx._holiday_decor(DATES[name])
        assert max(len(r) for r in deco) <= 8, name


def test_the_decoration_draws_on_the_home_arena_only_on_a_holiday():
    import tuipet.tournament as T
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    plain = arenafx._effect_overlay(p, 0, arenafx.SCREEN_COLS, grid.PXH, tick=0)
    _orig = T.holiday
    T.holiday = lambda today=None: "Christmas Festival"
    try:
        fest = arenafx._effect_overlay(p, 0, arenafx.SCREEN_COLS, grid.PXH, tick=0)
    finally:
        T.holiday = _orig
    assert len(fest) > len(plain), "the decoration did not draw"


def test_the_decoration_clears_a_resting_pet():
    """It sits far-left; a centred pet's body (x~12..28) does not reach it,
    so it reads as a corner ornament, not a smudge on the pet."""
    deco = arenafx._holiday_decor(DATES["Christmas Festival"])
    pts = _blit(deco, grid.X0, grid.TOP)
    assert max(x for x, _y in pts) < 12


def test_a_dead_pet_shows_no_decoration():
    import tuipet.tournament as T
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.dead = True
    _orig = T.holiday
    T.holiday = lambda today=None: "Halloween Festival"
    try:
        pts = arenafx._effect_overlay(p, 0, arenafx.SCREEN_COLS, grid.PXH, tick=0)
    finally:
        T.holiday = _orig
    assert pts == []                                   # the grave has no festival


def test_the_festival_bonuses_are_unchanged_underneath():
    """The decoration is purely visual -- the double bits / sales / festival
    egg machinery is the same holiday() the decor reads, untouched."""
    from tuipet import adventure
    assert adventure.active_holiday(DATES["Christmas Festival"]) == "Christmas Festival"
    assert adventure.HOLIDAY_BITS_MULT == 2
