"""Coloured precip + the dark-room rule (Joel 2026-07-15: "make it so snow and
rain cant be seen when the lights are off, and give them color").  Rain and
snow ride their own buffer plane (2) and paint in the theme's precip ink; a
lights-off room shows none of it, on every path that rains: paint(), the fx
painter, the grave, and the adventure home wait."""
import random

import tuipet.app as app
from tuipet import arena, menu, render, theme
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


def _spy(monkeypatch):
    cap = {}

    def spy(rows, cols, nrows, on, bg, mirror=False, xshift=0, yshift=0,
            overlay=None, bgimg=None, clip=None, overlay_free=None,
            free_ink=None, baseline=True):
        cap.update(overlay=list(overlay or []), free=list(overlay_free or []),
                   free_ink=free_ink)
        return ""

    monkeypatch.setattr("tuipet.arena.render_screen", spy)
    return cap


def test_every_theme_declares_precip_ink():
    for name, t in theme.THEMES.items():
        for kind in ("rain", "snow"):
            c = t["precip"][kind]
            assert c.startswith("#") and len(c) == 7, f"{name}/{kind}: {c}"


def test_weather_rides_its_own_buffer_plane():
    buf = render.fill_buf(["1"], 8, 8, overlay=[(1, 1)], overlay_free=[(2, 2)])
    assert buf[1][1] == 1 and buf[2][2] == 2


def test_free_ink_colours_the_weather_pixels():
    t = render.render_screen([], 4, 2, on="#111111", bg="#222222",
                             overlay=[(0, 0)], overlay_free=[(1, 0)],
                             free_ink="#a1b2c3")
    styles = t.markup
    assert "#a1b2c3" in styles, "weather pixel not painted in the precip ink"
    assert "#111111" in styles, "sprite ink lost"


def test_precip_ink_follows_weather_and_theme():
    assert arena._precip_ink("Raining") == theme.PRECIP["rain"]
    assert arena._precip_ink("HeavySnow") == theme.PRECIP["snow"]
    assert arena._precip_ink("Clear") is None and arena._precip_ink("Cloudy") is None


def test_lights_off_hides_the_rain(monkeypatch):
    cap = _spy(monkeypatch)
    s = _screen()
    p = _pet(weather="Raining")
    s.paint(p)
    assert cap["free"], "lit room: the rain must fall"
    assert cap["free_ink"] == theme.PRECIP["rain"]
    p.lights = False
    s.paint(p)
    assert cap["free"] == [], "dark room: no rain glitters on the cover"


def test_dark_fx_hides_the_snow_too(monkeypatch):
    cap = _spy(monkeypatch)
    s = _screen()
    p = _pet(weather="Snowing", lights=False)
    s.start_fx("cheer")
    s.paint(p)
    assert cap["free"] == [] and cap["overlay"] == []
    p.lights = True
    s.paint(p)
    assert cap["free"], "lit fx: snow keeps falling over the anim"
    assert cap["free_ink"] == theme.PRECIP["snow"]
    # ...and it falls on the FREE plane: never window-clipped with the props
    assert all(pt not in cap["overlay"] for pt in cap["free"][:3])


def test_the_grave_keeps_the_rule(monkeypatch):
    cap = _spy(monkeypatch)
    s = _screen()
    p = _pet(weather="Raining", dead=True)
    s.paint(p)
    assert cap["free"]
    p.lights = False
    s.paint(p)
    assert cap["free"] == []


def test_adventure_home_wait_keeps_the_rule(monkeypatch):
    from tuipet.adventurescreen import AdventurePanel
    random.seed(3)
    p = Pet.new_egg(egg_type=1)
    p._hatch_into_fresh()
    p.world_seconds = 12 * 60.0
    p.weather = "Raining"
    cap = {}

    def spy(placements, bgimg, **kw):
        cap.update(free=list(kw.get("overlay_free") or []),
                   free_ink=kw.get("free_ink"))
        return ""

    monkeypatch.setattr(menu, "paint", spy)
    pan = AdventurePanel(p)
    pan.travelling = False
    pan._biome_frame()
    assert cap["free"] and cap["free_ink"] == theme.PRECIP["rain"]
    p.lights = False
    pan._biome_frame()
    assert cap["free"] == []
