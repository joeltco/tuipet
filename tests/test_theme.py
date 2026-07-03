"""Theme propagation across screens (Workstream C).

theme.apply() pushes the active palette into every module that imported colour
names by copy (`from .theme import INK, ...`) -- but only those listed in
theme._SCREEN_MODULES. A screen that binds colour names yet is missing from that
list keeps the default (grey) palette after a switch: a stale-theme leak.

Audit result: the list is currently complete and minimal. These tests pin that
(so a new screen can't silently leak) and verify a switch actually propagates.
"""
import importlib
import os
import re


from tuipet import theme


_COLOR_NAMES = set(theme._NAMES)


def _modules_binding_theme_names():
    here = os.path.dirname(importlib.import_module("tuipet").__file__)
    out = {}
    for fn in sorted(os.listdir(here)):
        if not fn.endswith(".py"):
            continue
        mod = fn[:-3]
        s = open(os.path.join(here, fn)).read()
        for m in re.finditer(r"from \.theme import ([^\n]+(?:\n[^\n)]+)*)", s):
            names = {x.strip() for x in re.split(r"[,\s()]+", m.group(1)) if x.strip()}
            hit = names & _COLOR_NAMES
            if hit:
                out.setdefault(mod, set()).update(hit)
    return out


def test_every_theme_binder_is_propagated():
    """Any module that copies a theme colour name must be in _SCREEN_MODULES."""
    binders = _modules_binding_theme_names()
    missing = sorted(m for m in binders if m not in theme._SCREEN_MODULES)
    assert not missing, (
        f"these modules bind theme colours but aren't in _SCREEN_MODULES, so a "
        f"theme switch won't reach them (stale-theme leak): {missing}")


def test_screen_modules_list_has_no_dead_entries():
    """Every listed module actually binds a theme name (keeps the list honest)."""
    binders = _modules_binding_theme_names()
    # 'app' and 'menu' always bind; a listed module that binds nothing is dead weight
    dead = sorted(m for m in theme._SCREEN_MODULES if m not in binders)
    assert not dead, f"_SCREEN_MODULES lists modules that bind no theme names: {dead}"


def test_apply_propagates_to_a_screen_module():
    from tuipet import menu
    theme.apply("grey")                       # known baseline
    grey_ink = menu.INK
    try:
        theme.apply("amber")
        assert menu.INK != grey_ink, "INK should change with the theme"
        expected = theme._derive(theme.THEMES["amber"])["INK"]
        assert menu.INK == expected
    finally:
        theme.apply("grey")
    assert menu.INK == grey_ink, "switching back restores the palette"


def test_apply_unknown_theme_falls_back():
    name = theme.apply("does-not-exist")
    assert name in theme.THEMES                # falls back, never crashes
    theme.apply("grey")


# ---- palette completeness (the 2026-07 theme expansion) ----------------------

_REQUIRED = {"on", "bg", "mid", "accent", "pos", "neg", "border",
             "sil_day", "sil_night", "heart", "energy", "mood", "life", "coin",
             "weather", "phases"}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def test_every_theme_carries_the_full_key_set():
    for name, t in theme.THEMES.items():
        missing = _REQUIRED - set(t)
        assert not missing, f"{name} lacks {missing}"
        for k in _REQUIRED - {"weather", "phases"}:
            assert _HEX.match(t[k]), f"{name}.{k} = {t[k]!r} is not a hex colour"
        assert set(t["phases"]) == {"dawn", "day", "dusk", "night"}, name
        for ph, (on, bg) in t["phases"].items():
            assert _HEX.match(on) and _HEX.match(bg), f"{name}.phases.{ph}"
        assert set(t["weather"]) == {"rain", "snow", "cloud"}, name
        for w, (col, a) in t["weather"].items():
            assert _HEX.match(col) and 0.0 < a < 1.0, f"{name}.weather.{w}"


def test_every_theme_derives_and_applies_cleanly():
    try:
        for name in theme.names():
            theme.apply(name)
            assert theme.LCD_ON == theme.THEMES[name]["on"]
    finally:
        theme.apply("grey")


def test_the_picker_fits_the_lcd_with_every_theme():
    from tuipet.themescreen import ThemePanel
    pan = ThemePanel()
    assert pan.text().plain.count("\n") <= 12   # the #lcd box is 12 content rows
    for name in theme.names():                  # walking previews never crashes
        pan.key("down")
    pan.key("escape")
    assert theme.current() == "grey"
