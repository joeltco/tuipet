"""Every panel's text() must RENDER — with a real pet and real inventory.

The v0.2.166-175 feed-screen crash (bitmap_text read FULL/UPPER/LOWER after the
dead-code sweep deleted them) shipped because no test ever executed a panel's
icon path: 357 tests were green while pressing F crashed the app.  This sweep
instantiates every simple-constructor panel, walks its keys, and renders each
state.  It is deliberately shallow — its job is 'does it draw', not 'is it
right'."""

from tuipet.pet import Pet
from tuipet.render import bitmap_text


def _pet(**kw):
    p = Pet(num=100, stage="Adult", attribute="Vaccine")

    p.bits = 5000
    p.hunger = 0
    p.add_item("f:54")          # a bag item -> the shop bag icon path runs
    p.add_item("i:32")
    p.digimemory = {"name": "Elder", "num": 29, "vaccine": 5, "data": 3, "virus": 1, "seconds": 60.0}
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_bitmap_text_renders_pixels():
    lines = bitmap_text(["1100", "1011", "0111", "0001"], "#ffffff", "#000000")
    assert len(lines) == 2
    assert any(ch in lines[0].plain for ch in "▀▄█")   # actual blocks, not blanks


# The PHYSICAL LCD content box: #lcd CSS 44x14 minus border and padding.
# The 2026-07-04 town audit found the errand strip 58 wide and the whole
# scene grammar 15-17 lines tall -- the live compositor CLIPPED the bottom
# five lines (strip, note, footer) of every scene screen while the PNG
# raster harness happily rendered the full Text.  Pixels aren't the box.
LCD_ROWS, LCD_COLS = 12, 40


def _render(panel):
    """Render a panel state AND enforce the physical LCD budget."""
    t = panel.text()
    lines = t.plain.split("\n")
    name = type(panel).__name__
    assert len(lines) <= LCD_ROWS, f"{name}: {len(lines)} lines overflow the {LCD_ROWS}-row LCD"
    wide = max(map(len, lines))
    assert wide <= LCD_COLS, f"{name}: {wide} cols overflow the {LCD_COLS}-col LCD"
    return t


def _walk(panel, keys, renders=6):
    """Drive a panel: render, press keys, re-render each time.  Stops at a
    ("done", ...) payload like the app does -- the old `except TypeError:
    break` treated ANY TypeError inside a key handler as "panel closed",
    silently ending the walk on exactly the crash class this file exists
    to catch (test audit 2026-07-13)."""
    _render(panel)
    for k in keys:
        r = panel.key(k)
        if isinstance(r, tuple) and r and r[0] == "done":
            break                                   # the app closes the mode here
        if hasattr(panel, "anim"):
            panel.anim()
        _render(panel)


def test_feed_panel_renders_every_selection():
    from tuipet.feedscreen import FeedPanel, ROWS_MENU
    pan = FeedPanel(_pet())
    seen = []
    for _ in range(len(ROWS_MENU)):
        t = _render(pan)                       # canon on-LCD icon scene, within budget
        assert any(ch in t.plain for ch in "▀▄█"), "feed menu drew no pixels"
        # half-block cells are all the same glyph -- the cursor shows as a
        # COLOUR span, so fingerprint the styled spans, not the plain text
        seen.append([(s.start, s.end, str(s.style)) for s in t.spans])
        pan.key("down")
    # the cursor row moves between meat and pill -> the two scenes differ
    assert seen[0] != seen[1], "feed cursor did not move between meat and pill"
def test_shop_panel_renders_shop_and_bag():
    from tuipet.shopscreen import ShopPanel
    pan = ShopPanel(_pet())
    _walk(pan, ["down", "down", "i", "down", "down", "r"])   # shop rows, bag rows, a sell


def test_the_simple_panels_all_draw():
    from tuipet.backgroundscreen import BackgroundPanel
    from tuipet.jogressscreen import JogressPanel
    from tuipet.eggselectscreen import EggSelectPanel
    from tuipet.themescreen import ThemePanel
    from tuipet.deathscreen import DeathPanel
    from tuipet.feedscreen import FeedPanel
    from tuipet.creditscreen import CreditsPanel
    p = _pet()
    _walk(BackgroundPanel(p), ["down", "down", "up"])
    _walk(JogressPanel(p, p.num, p.num, p.num), ["space"])
    _walk(EggSelectPanel(), ["right", "right", "left"])
    _walk(ThemePanel(), ["down", "up", "escape"])
    _walk(CreditsPanel(p), ["down", "down", "up"])
    from tuipet.optionsscreen import KeysPanel
    _walk(KeysPanel((("f", "feed", "Feed"), ("q", "quit", "Quit"))),
          ["down", "up"])
    dead = _pet(dead=True)
    _walk(DeathPanel(dead, hold=0), [])
    _walk(FeedPanel(p), ["down", "up"])


def test_scene_screens_fit_the_physical_lcd_in_every_state():
    """Box-clip audit: every deep scene state stays within the 12-row LCD."""
    import random
    random.seed(3)
    p = _pet()
    from tuipet.training import TrainingPanel
    pan = TrainingPanel(p)
    _render(pan)
    pan.key("space")                       # lock the bar -> the strike plays
    for _ in range(80):
        pan.anim()
        _render(pan)
    from tuipet.battlescreen import BattlePanel
    bp = BattlePanel(p, {"num": 40, "name": "Foe", "stage": "Child",
                         "attribute": "Free"}, wild=True)
    for _ in range(200):
        bp.anim()
        _render(bp)
        if bp.phase == "ready":
            bp.key("space")
        if bp.phase == "result":
            break
def test_jogress_states_fit_the_lcd_with_real_options():
    """Box-clip stragglers (audit 2026-07-04): every earlier probe measured
    jogress EMPTY (fusions are data-rare) -- the real fusing/fused states ran
    15-16 lines and clipped.  Scene-only now (the offline picker died with the
    home jogress, v0.2.348); the LOBBY strip carries the prompts, pinned in
    test_menu_bounds."""
    from tuipet.jogressscreen import JogressPanel, FUSE_STEPS
    p = _pet()
    pan = JogressPanel(p, 100, 7, 4)
    for s in range(FUSE_STEPS):
        pan.fuse_step = pan.frame_i = s
        _render(pan)
    pan.phase = "fused"
    _render(pan)
    # the picker surface stays dead (the strip arc): no pick phase, no strip
    assert not hasattr(pan, "strip") and not hasattr(pan, "options")


def test_habitat_picker_is_a_scene_with_a_strip():
    """Habitat audit 2026-07-04: habitats ARE scenery, but the picker was a
    text list -- you bought a backdrop sight unseen.  The LCD now shows the
    pet standing in the browsed habitat (render-only preview); the picker
    line rides the strip; details live on the status card."""
    from tuipet.backgroundscreen import BackgroundPanel
    p = _pet()
    pan = BackgroundPanel(p)
    _render(pan)
    assert len(pan.text().plain.split("\n")) == 12   # the scene fills the LCD
    here = pan.text().markup
    assert "here" in pan.strip()                     # standing on the picked scene
    picked = p.bg_current
    pan.key("right")                                 # browse: the VIEW changes...
    _render(pan)
    assert pan.text().markup != here
    assert p.bg_current == picked                    # ...but browsing never re-hangs it
    assert "ENTER ESC" in pan.strip()         # menu-bounds rewording 2026-07-07


def test_title_boot_flashes_dissolves_then_settles():
    """Title audit 2026-07-04: the power-on sequence was unpinned — all
    segments flash, static thins into the wordmark, then only the mascot's
    gentle //4 bob moves.  Budget-checked every frame."""
    import random
    from tuipet.titlescreen import TitlePanel, BOOT_BLIP, BOOT_FADE
    random.seed(11)
    pan = TitlePanel()
    frames = []
    for _ in range(BOOT_BLIP + BOOT_FADE + 9):
        t = _render(pan)
        frames.append(t.markup)
        pan.anim()
    flash = frames[0]
    assert flash.count("▀") == 12 * 40            # all segments lit
    assert frames[BOOT_BLIP] != flash             # the static wipe differs...
    assert frames[BOOT_BLIP] != frames[BOOT_BLIP + 2]   # ...and thins each beat
    settled = frames[BOOT_BLIP + BOOT_FADE:]
    # the mascot's two bob poses (some species ship identical walk frames)
    assert 1 <= len(set(settled)) <= 2


def test_every_drill_completes_through_its_strike_within_budget():
    from tuipet.training import TrainingPanel
    p = _pet()
    p.energy = p.max_energy
    pan = TrainingPanel(p)
    pan.key("space")                     # lock -> shoot
    for _ in range(120):
        if pan.phase == "done":
            break
        pan.anim()
    assert pan.phase == "done"
    assert p.trainings_cur_stage >= 1    # the attempt counted
