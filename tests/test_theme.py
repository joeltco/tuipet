"""Theme propagation across screens (Workstream C).

theme.apply() pushes the active palette into every module that imported colour
names by copy (`from .theme import INK, ...`).  Refactor 2026-07-05: the
binders are DISCOVERED from sys.modules (any tuipet module carrying LCD_ON or
INK), retiring the hand-maintained _SCREEN_MODULES tuple whose omissions
failed silently (a forgotten registration = stale colours on theme switch).
These tests pin the discovery: every source-level binder must actually carry
the new palette after a switch.
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


def test_every_theme_binder_is_discovered_and_retinted():
    """Every module that copies theme colour names must ACTUALLY carry the new
    palette after apply() -- the behavioral contract the old _SCREEN_MODULES
    census only approximated.  Discovery requires LCD_ON or INK as the gate,
    so a binder that imports only exotic names would leak: pin that every
    real binder binds one of the gate names too."""
    binders = _modules_binding_theme_names()
    assert binders, "the source scan found no binders at all (regex broke?)"
    import importlib as _il
    try:
        expected = theme._derive(theme.THEMES["amber"])
        checked = 0
        for mname, names in binders.items():
            mod = _il.import_module(f"tuipet.{mname}")
            theme.apply("amber")               # retint after any fresh import
            # only MODULE-LEVEL bindings need propagation (the source scan also
            # sees function-local lazy imports, which read live values)
            carried = {n for n in names if hasattr(mod, n)}
            if not carried:
                continue
            assert carried & {"LCD_ON", "INK"}, (
                f"{mname} binds {sorted(carried)} but neither LCD_ON nor INK, "
                f"so apply()'s discovery gate skips it (stale-theme leak)")
            for n in sorted(carried):
                assert getattr(mod, n) == expected[n], f"{mname}.{n} kept stale colours"
                checked += 1
        assert checked > 20, "the sweep barely checked anything (scan broke?)"
    finally:
        theme.apply("grey")


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


def test_load_sprites_cache_is_intact():
    """Refactor 2026-07-05 near-miss: inserting a helper above load_sprites
    STOLE its @lru_cache decorator -- every call re-parsed the gzip atlas and
    the app crawled (the suite 'hang').  Pin cache identity for the hot atlas
    loaders so a displaced decorator can never ship again."""
    from tuipet import data, egg, lines
    assert data.load_sprites() is data.load_sprites()
    assert data.load_icons() is data.load_icons()
    assert data.load_effects() is data.load_effects()
