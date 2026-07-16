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
             "sil_day", "sil_night", "heart", "energy", "mood", "life", "coin",
             "weather", "phases", "void", "flash"}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def test_every_theme_carries_the_full_key_set():
    for name, t in theme.THEMES.items():
        missing = _REQUIRED - set(t)
        assert not missing, f"{name} lacks {missing}"
        for k in _REQUIRED - {"weather", "phases", "flash"}:
            assert _HEX.match(t[k]), f"{name}.{k} = {t[k]!r} is not a hex colour"
        assert len(t["flash"]) == 3 and all(_HEX.match(c) for c in t["flash"]), \
            f"{name}.flash must be (blend, ink, bg) hex triple"
        ramp = t.get("bg_ramp")
        if ramp:                                  # optional: quantized background art
            assert len(ramp) >= 2 and all(_HEX.match(c) for c in ramp), name
            lums = [(299 * int(c[1:3], 16) + 587 * int(c[3:5], 16)
                     + 114 * int(c[5:7], 16)) // 1000 for c in ramp]
            assert lums == sorted(lums), f"{name}.bg_ramp must run dark -> light"
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
    from tuipet import data
    assert data.load_sprites() is data.load_sprites()
    assert data.load_icons() is data.load_icons()
    assert data.load_effects() is data.load_effects()


# ---- gameboy background palette (Joel 2026-07-05: "gameboy theme uses
# gameboy like palettes for lcd backgrounds") ----------------------------------

_DMG = ("#306230", "#8bac0f", "#9bbc0f")   # the BACKGROUND shades (light three)


def test_gameboy_declares_the_dmg_ramp():
    assert theme.THEMES["gameboy"]["bg_ramp"] == _DMG
    assert theme.THEMES["gameboy"]["void"] == "#0f380f"   # lights-off stays on-palette


def test_gameboy_backgrounds_never_wear_the_sprite_ink():
    """GB layering (redo 2026-07-05: "their blending into the background") --
    the darkest DMG green is the SPRITE ink; background art must never use
    it, so the mon is always the darkest thing on the LCD.  This replaced
    the halo-outline experiment (which boxed the mon)."""
    gb = theme.THEMES["gameboy"]
    assert gb["sil_day"] == gb["on"] == "#0f380f"
    assert gb["sil_day"] not in gb["bg_ramp"]


def test_themed_bg_dithers_only_when_the_theme_declares_a_ramp():
    frame = ["".join("%02x%02x%02x" % (v, v, v) for v in range(0, 240, 30))] * 4
    try:
        theme.apply("grey")
        assert theme.themed_bg(frame) is frame            # full colour passes through
        theme.apply("gameboy")
        out = theme.themed_bg(frame)
        cols = {out[y][x:x + 6] for y in range(4) for x in range(0, len(out[0]), 6)}
        assert cols <= {c[1:] for c in _DMG}, f"off-palette: {cols}"
        assert theme.themed_bg(frame) is out              # memoized per frame
    finally:
        theme.apply("grey")


def test_gameboy_dither_stretches_contrast_across_the_ramp():
    """Absolute luminance collapsed most art into the top two shades (the
    banded first cut Joel bounced) -- a NARROW mid-luminance frame must still
    span the whole ramp after the per-frame stretch, and a smooth gradient
    must dither through more than two shades."""
    frame = ["".join("%02x%02x%02x" % (v, v, v) for v in range(100, 160, 4))] * 8
    try:
        theme.apply("gameboy")
        out = theme.themed_bg(frame)
        cols = {out[y][x:x + 6] for y in range(8) for x in range(0, len(out[0]), 6)}
        assert _DMG[0][1:] in cols and _DMG[-1][1:] in cols, "stretch missing"
        assert len(cols) >= 3, "gradient should dither through the mid shades"
    finally:
        theme.apply("grey")


def test_gameboy_renders_background_art_entirely_on_palette():
    """Every bgimg pixel crosses render._paint_cells -- under gameboy the LCD
    must never show a colour off the 4-shade DMG ramp (sprite ink aside)."""
    import re as _re
    from tuipet.render import render_scene
    rowlen = 8
    frame = ["".join(("%02x%02x%02x" % (17 * i, 9 * i, 23 * i % 256)) for i in range(rowlen))
             for _ in range(4)]                            # 2 char-rows of varied colour
    try:
        theme.apply("gameboy")
        txt = render_scene([], rowlen, 2, theme.LCD_ON, theme.LCD_BG, bgimg=frame)
        colours = set(_re.findall(r"#[0-9a-f]{6}", str(txt.markup)))
        off = colours - set(_DMG) - {theme.LCD_ON}
        assert not off, f"off-palette colours leaked: {off}"
        theme.apply("grey")
        txt = render_scene([], rowlen, 2, theme.LCD_ON, theme.LCD_BG, bgimg=frame)
        colours = set(_re.findall(r"#[0-9a-f]{6}", str(txt.markup)))
        assert "#" + frame[0][0:6] in colours              # grey passes raw art through
    finally:
        theme.apply("grey")


def test_gameboy_render_reserves_the_sprite_ink_for_sprites():
    """End-to-end layering pin: over ANY background art, the darkest green on
    the rendered LCD comes only from sprite/overlay ink -- a sprite-less
    render of dark art must contain no #0f380f at all."""
    from tuipet.render import render_scene
    dark = ["000000" * 12] * 8
    try:
        theme.apply("gameboy")
        t = render_scene([], 12, 4, theme.SIL_DAY, theme.LCD_BG, bgimg=dark)
        assert "#0f380f" not in str(t.markup), "background art wore the sprite ink"
        t = render_scene([(["111", "111"], 5, False)], 12, 4,
                         theme.SIL_DAY, theme.LCD_BG, bgimg=dark)
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


def test_the_arena_backdrop_ships_a_full_time_stack():
    """BackgroundAnim checkBack: tournaments + PvP battles play in front of
    tourneyBack.png -- a 5-frame sheet (morning/noon/sunset/night/precip)
    indexed exactly like the habitat sheets (theme/rendering audit 2026-07-06)."""
    from tuipet import data
    frames = data.load_backgrounds().get("tourneyBack")
    assert frames and len(frames) == 5
    assert all(len(r) == 40 * 6 for fr in frames for r in fr)


def test_background_file_override_picks_the_arena_sheet():
    """Pet.background(file=...) swaps the SHEET while keeping the same
    time-of-day frame pick -- the arena has its own night, not the home's."""
    from tuipet import data
    from tuipet.pet import Pet
    p = Pet(num=-1, stage="Rookie")
    p.weather = "Clear"
    arena = p.background(file="tourneyBack")
    home = p.background()
    sheets = data.load_backgrounds()
    idx = {"dawn": 0, "day": 1, "dusk": 2, "night": 3}[p.day_phase]
    want = theme.weather_tint(sheets["tourneyBack"][idx], "Clear")
    if p.day_phase == "night":                    # a clear night twinkles now
        want = (theme.star_frame("tourneyBack", sheets["tourneyBack"],
                                 p.world_seconds) or want)
    assert arena == want
    assert arena != home


# ---- background quantizer redo (Joel 2026-07-12: "some backgrounds look
# like shit" -- hue-blind luminance banding) + the paper ramp ------------------

_PAPER = ("#8a8274", "#d5cdbb", "#efe9dc")


def test_paper_declares_the_ink_wash_ramp():
    """Joel 2026-07-12: "apply this to the paper theme -- white instead of
    green".  Same law as gameboy: the sprite ink stays off the ramp, so the
    mon is always the darkest thing on the page."""
    pp = theme.THEMES["paper"]
    assert pp["bg_ramp"] == _PAPER
    assert pp["on"] not in pp["bg_ramp"]


def test_quant_splits_equal_luminance_hues():
    """The old banding merged hue-distinct, equal-brightness features (the
    desert dunes vs its sky; digicoreDa dark core vs blue bricks).  A frame
    of two equal-luma colour fields must still render as TWO shades."""
    blue, orange = "3c64c8", "c86414"          # ~equal BT.601 luma, far in RGB
    frame = [blue * 10 + orange * 10] * 8
    try:
        theme.apply("gameboy")
        out = theme.themed_bg(frame)
        left = {out[y][:6] for y in range(8)}
        right = {out[y][-6:] for y in range(8)}
        assert left != right, "equal-luma hues merged into one shade"
    finally:
        theme.apply("grey")


def test_quant_keeps_a_near_flat_frame_flat():
    """The old contrast stretch amplified faint texture noise into random
    blotches; the rank spread later manufactured a dark ring out of
    digicoreVb faint glow.  A near-flat frame must render as ONE shade."""
    a, b = "efefef", "e7e7e7"                  # imperceptible texture
    frame = [(a + b) * 10, (b + a) * 10] * 6
    try:
        theme.apply("gameboy")
        out = theme.themed_bg(frame)
        cols = {out[y][x:x + 6] for y in range(12) for x in range(0, 120, 6)}
        assert len(cols) == 1, f"flat frame blotched into {cols}"
    finally:
        theme.apply("grey")


def test_quant_dominant_field_accents_stay_adjacent():
    """A flat field with an accent (egg10Back door-on-wall) keeps the accent
    VISIBLE but at neighbour contrast -- never the far end of the ramp."""
    field, accent = "e8e8e8", "909090"         # bright wall, mid-grey feature
    rows = [field * 20] * 9 + [field * 6 + accent * 8 + field * 6] * 3
    try:
        theme.apply("gameboy")
        out = theme.themed_bg(rows)
        cols = {out[y][x:x + 6] for y in range(12) for x in range(0, 120, 6)}
        assert len(cols) == 2, "the accent vanished (or blotched)"
        assert _DMG[0][1:] not in cols, "accent jumped to the far dark shade"
    finally:
        theme.apply("grey")
