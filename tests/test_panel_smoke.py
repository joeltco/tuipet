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
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
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
    assert len(ROWS_MENU) == 2                      # meat + pill
    for _ in range(3):                              # both selections draw
        pan.text()
        pan.key("down")


def test_shop_panel_renders_shop_and_bag():
    from tuipet.shopscreen import ShopPanel
    pan = ShopPanel(_pet())
    _walk(pan, ["down", "down", "i", "down", "down", "r"])   # shop rows, bag rows, a sell


def test_the_simple_panels_all_draw():
    from tuipet.digicorescreen import DigiCorePanel
    from tuipet.assistscreen import AssistPanel
    from tuipet.dnascreen import DNAPanel
    from tuipet.jogressscreen import JogressPanel
    from tuipet.eggselectscreen import EggSelectPanel
    from tuipet.themescreen import ThemePanel
    from tuipet.deathscreen import DeathPanel
    from tuipet.feedscreen import FeedPanel
    p = _pet()
    _walk(DigiCorePanel(p), ["space", "space", "right", "right", "right",
                             "right", "right", "right", "down", "enter", "down"])
    _walk(AssistPanel(p), ["enter", "enter"])
    _walk(DNAPanel(p), ["down", "right"])
    # the Divergence roads page (hard rule: every phase gets a text() walk)
    dna = DNAPanel(p)
    dna.phase = "roads"
    _walk(dna, ["down", "down", "up", "escape"])
    _walk(JogressPanel(p, p.num, p.num, p.num), ["space"])
    _walk(EggSelectPanel(), ["right", "right", "left"])
    _walk(ThemePanel(), ["down", "up", "escape"])
    from tuipet.optionsscreen import KeysPanel
    _walk(KeysPanel((("f", "feed", "Feed"), ("enter", "gift", "Accept gift"))),
          ["down", "up"])
    dead = _pet(dead=True)
    _walk(DeathPanel(dead), [])
    _walk(FeedPanel(p), ["down", "up"])


def test_shop_has_no_digitama_shelf():
    """The licence cut (2026-07-17): the shop sells goods only.  The classic
    Eggs TAB returned with the v0.5.0 bar (polish 2026-07-17), but it is the
    DIGIMENTAL shelf -- walk every tab and prove no bank digitama survives."""
    from tuipet.shopscreen import ShopPanel
    from tuipet import shop as _shop
    p = _pet()
    pan = ShopPanel(p)
    assert not hasattr(_shop, "EGGS_CATEGORY")
    for _ in range(len(pan._tabs())):      # every tab still renders clean
        pan.text()
        assert not any(e.get("egg_idx") is not None for e in pan._rows())
        pan.key("right")
    pan.text()


# (test_drill_hints_wrap... left with the classic training system -- 0.5 TRAINING 2026-07-17)


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


def test_the_home_scene_is_wired_to_the_egg():
    """Habitats left (BASIC VPET 2026-07-16): the scene behind the mon comes
    from the EGG the pet hatched from -- two pets from different eggs stand
    in different DSprite backdrops, and the same pet's scene never moves."""
    from tuipet import backgrounds
    a, b = _pet(), _pet()
    a.egg_type, b.egg_type = 0, 5                    # greenhills vs datatunnel
    sa, sb = a.background(), b.background()
    assert sa and sb and sa != sb
    assert backgrounds.scene_for_egg(0) != backgrounds.scene_for_egg(5)
    assert a.background() == sa                      # the home scene stands still
    assert a.background(file="tourneyBack") != sa    # the arena override still wins


def test_title_boot_flashes_transitions_then_settles_for_every_fx():
    """Title audit 2026-07-04, extended 2026-07-20: the power-on flash is
    common, then a per-launch random BOOT_FX transition plays the title in.
    EVERY effect must break the flash on its first step, keep moving, and
    settle to only the mascot's //4 bob.  Budget-checked every frame."""
    import random
    from tuipet.titlescreen import TitlePanel, BOOT_BLIP, BOOT_FADE, BOOT_FX
    random.seed(11)
    fresh = TitlePanel()
    assert fresh.fx in BOOT_FX                    # launch draws from the fx pool
    assert fresh.sfx == "boot"                    # the power-on jingle rides the flash
    for fx in BOOT_FX:
        pan = TitlePanel()
        pan.fx = fx
        frames = []
        for _ in range(BOOT_BLIP + BOOT_FADE + 9):
            t = _render(pan)
            frames.append(t.markup)
            pan.anim()
        flash = frames[0]
        assert flash.count("▀") == 12 * 40        # all segments lit
        name = fx.__name__
        assert frames[BOOT_BLIP] != flash, name          # step 0 breaks the flash...
        assert frames[BOOT_BLIP] != frames[BOOT_BLIP + 2], name   # ...and keeps moving
        settled = frames[BOOT_BLIP + BOOT_FADE:]
        assert len(set(settled)) == 2, name       # only the two bob poses remain


def test_title_attract_cycles_mascots_and_the_prompt_pulses():
    """Title polish 2026-07-20: every CYCLE frames the mascot dissolves to a
    DIFFERENT mon (the boot dither reused), and the PRESS ENTER prompt pulses
    bold/dim at constant visible width so the centred strip never jumps."""
    import random
    from tuipet.titlescreen import TitlePanel, BOOT_BLIP, BOOT_FADE, CYCLE
    random.seed(11)
    pan = TitlePanel()
    phases, nums = set(), []
    for f in range(CYCLE + BOOT_FADE + 2):
        _render(pan)                              # every frame renders in budget
        if f > BOOT_BLIP + BOOT_FADE:
            phases.add(pan.strip().split("▸")[0])
        if not nums or nums[-1] != pan.num:
            nums.append(pan.num)
        pan.anim()
    assert len(nums) == 2 and nums[0] != nums[1]  # exactly one swap, a new face
    assert pan._fade == 0                         # ...whose dissolve has settled
    assert phases == {"[b]", "[dim]"}             # both pulse phases showed
    stripped = pan.strip()
    assert "ENTER" in stripped
    if pan.version:                               # source runs carry no metadata
        assert f"v{pan.version}" in stripped


def test_assist_card_prices_match_canon_and_toggle_names_a_helper():
    """Assist audit 2026-07-05: drawAutoCareValidation mirror — per-stage visit
    prices (config AutoCareStage*Price col 1) + the stage-scaled retainer
    (half the visit ladder, bit-sink design 2026-07-14); toggling ON rolls a
    REAL helper from the CanAssist pool."""
    import random
    from tuipet.assistscreen import AssistPanel
    from tuipet.pet import AUTO_CARE_VISIT_PRICE, AUTO_CARE_HOUR_PRICE
    assert AUTO_CARE_VISIT_PRICE == {"Egg": 50, "Fresh": 50, "InTraining": 100,
                                     "Rookie": 200, "Champion": 400,
                                     "Ultimate": 800, "Mega": 1600}
    assert AUTO_CARE_HOUR_PRICE["InTraining"] == 0 and AUTO_CARE_HOUR_PRICE["Rookie"] == 100
    random.seed(2)
    p = _pet()
    pan = AssistPanel(p)
    _render(pan)
    assert "400b/care" in pan.text().plain        # Champion rates on the card
    assert "200b/hour" in pan.text().plain
    pan.key("enter")                              # hire
    _render(pan)
    assert p.auto_care and p.assistant_num >= 0
    assert "on duty" in pan.text().plain
    pan.key("enter")                              # dismiss
    assert not p.auto_care
    assert "dismissed" in pan.msg


# (test_every_drill_completes... (test_training_clone covers the one drill) left with the classic training system -- 0.5 TRAINING 2026-07-17)


# (test_every_drill_strip... left with the classic training system -- 0.5 TRAINING 2026-07-17)


