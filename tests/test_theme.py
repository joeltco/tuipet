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
    try:
        name = theme.apply("does-not-exist")
        assert name in theme.THEMES            # falls back, never crashes
    finally:
        theme.apply("grey")                    # restore even on failure


# ---- palette completeness (the 2026-07 theme expansion) ----------------------

_REQUIRED = {"on", "bg", "mid", "accent", "pos", "neg", "border",
             "sil_scene", "sil_lightsoff", "heart", "energy", "care", "life", "coin",
             "void", "flash"}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def test_every_theme_carries_the_full_key_set():
    for name, t in theme.THEMES.items():
        missing = _REQUIRED - set(t)
        assert not missing, f"{name} lacks {missing}"
        for k in _REQUIRED - {"phases", "flash"}:
            assert _HEX.match(t[k]), f"{name}.{k} = {t[k]!r} is not a hex colour"
        assert len(t["flash"]) == 3 and all(_HEX.match(c) for c in t["flash"]), \
            f"{name}.flash must be (blend, ink, bg) hex triple"


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
    from tuipet import data
    assert data.load_sprites() is data.load_sprites()
    assert data.load_icons() is data.load_icons()
    assert data.load_effects() is data.load_effects()


# ---- gameboy background palette (Joel 2026-07-05: "gameboy theme uses
# gameboy like palettes for lcd backgrounds") ----------------------------------

_DMG = ("#306230", "#8bac0f", "#9bbc0f")   # the BACKGROUND shades (light three)


def test_gameboy_render_reserves_the_sprite_ink_for_sprites():
    """End-to-end layering pin: over ANY background art, the darkest green on
    the rendered LCD comes only from sprite/overlay ink -- a sprite-less
    render of dark art must contain no #0f380f at all."""
    from tuipet.render import render_scene
    dark = ["000000" * 12] * 8
    try:
        theme.apply("gameboy")
        t = render_scene([], 12, 4, theme.SIL_SCENE, theme.LCD_BG, bgimg=dark)
        assert "#0f380f" not in str(t.markup), "background art wore the sprite ink"
        t = render_scene([(["111", "111"], 5, False)], 12, 4,
                         theme.SIL_SCENE, theme.LCD_BG, bgimg=dark)
        assert "#0f380f" in str(t.markup)             # the sprite itself still inks
    finally:
        theme.apply("grey")


def test_shell_chrome_keys_all_fall_back():
    """bezel/shell/label/key are OPTIONAL chrome colours deriving from
    border/mid/cyan.  The v0.2.284 putty-shell gameboy experiment was
    REVERTED (Joel: "this looks bad") -- EVERY theme, gameboy included, must
    ride the fallbacks so the chrome renders exactly as it did pre-shell."""
    for name in theme.THEMES:
        d = theme._derive(theme.THEMES[name])
        assert d["BEZEL"] == d["BORDER"] and d["SHELL"] == d["BORDER"], name
        assert d["LABEL"] == d["MID"] and d["KEY"] == "cyan", name


def test_action_bar_letters_keep_cyan_on_every_theme():
    from tuipet.app import keys_markup
    try:
        for name in theme.THEMES:
            theme.apply(name)
            assert "b cyan]" in keys_markup(), name
    finally:
        theme.apply("grey")


def test_the_arena_backdrop_is_one_look_now():
    """BackgroundAnim checkBack: tournaments + PvP battles play in front of
    tourneyBack -- flattened to its single DAY look when the day/night
    system left (BASIC VPET 2026-07-17)."""
    from tuipet import data
    frames = data.load_backgrounds().get("tourneyBack")
    assert frames and len(frames) == 1
    assert all(len(r) == 40 * 6 for fr in frames for r in fr)


def test_background_file_override_picks_the_arena_sheet():
    """Pet.background(file=...) swaps the SHEET -- the arena look, not the
    egg's home scene."""
    from tuipet import data
    from tuipet.pet import Pet
    p = Pet(num=-1, stage="Rookie")
    arena = p.background(file="tourneyBack")
    home = p.background()
    assert arena == data.load_backgrounds()["tourneyBack"][0]
    assert arena != home


# ---- background quantizer redo (Joel 2026-07-12: "some backgrounds look
# like shit" -- hue-blind luminance banding) + the paper ramp ------------------

_PAPER = ("#8a8274", "#d5cdbb", "#efe9dc")


def test_the_background_quantizer_is_gone():
    """Joel 2026-07-18: "get rid of the green and white background pallet
    switcher in gameboy and paper" -- backdrops render full colour on every
    theme; the DMG/ink shades survive only in chrome and sprites."""
    from tuipet import render
    import inspect
    assert not hasattr(theme, "themed_bg")
    assert not hasattr(theme, "_quant_frame")
    for name in ("gameboy", "paper"):
        assert "bg_ramp" not in theme.THEMES[name]
    assert "themed_bg" not in inspect.getsource(render)


def test_theme_choice_rides_the_save_dir(tmp_path, monkeypatch):
    """theme.txt resolves through persistence.SAVE_DIR at call time (naming
    audit 2026-07-19): the old hardcoded ~/.local path ignored the sandbox
    and the iOS dir pick, and erase_all swept a file that wasn't it."""
    from tuipet import persistence, theme
    monkeypatch.setattr(persistence, "SAVE_DIR", str(tmp_path))
    theme.save_choice("amber")
    assert (tmp_path / "theme.txt").read_text() == "amber"
    assert theme.load_choice() == "amber"
    removed = persistence.erase_all()
    assert "theme.txt" in removed          # the erase sweeps the REAL file now


def test_every_theme_carries_the_renamed_schema():
    """The naming audit's renames hold across all themes: care (was mood --
    it tints the care row), sil_scene / sil_lightsoff (was day/night --
    the arena clock is gone)."""
    from tuipet import theme
    for name, t in theme.THEMES.items():
        for key in ("care", "sil_scene", "sil_lightsoff",
                    "heart", "energy", "life", "coin"):
            assert key in t, (name, key)
        assert "mood" not in t and "sil_day" not in t, name
