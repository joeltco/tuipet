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


def test_shop_egg_tab_renders_the_egg_icon():
    """The egg tab's preview slot draws the REAL egg sprite (audit 2026-07-04):
    exercise that icon path with a buyable egg so it can never ship broken."""
    from tuipet import persistence
    from tuipet.shopscreen import ShopPanel
    persistence.wins_add(50)               # sandboxed: Sakumon's license unlocks
    p = _pet()
    pan = ShopPanel(p)
    from tuipet import shop as _shop
    tabs = pan.tabs
    assert _shop.EGGS_CATEGORY in tabs
    for _ in range(len(tabs)):             # walk to the egg tab, rendering as we go
        if tabs[pan.tab] == _shop.EGGS_CATEGORY:
            break
        pan.key("right")
        pan.text()
    assert tabs[pan.tab] == _shop.EGGS_CATEGORY
    pan.text()                             # the egg icon path executes
    pan.key("down")
    pan.text()


def test_drill_hints_wrap_clean_on_the_status_card():
    """Audit 2026-07-04: the card wraps hints at 26 cols -- each hint must
    split on its triple-space gap with the KEY staying beside its action
    (the old hard [:26] slice cut every hint mid-word)."""
    from tuipet.training import TrainingPanel, GAMES
    p = _pet()
    for gi in range(len(GAMES)):
        pan = TrainingPanel(p)
        pan.gi = gi                              # gkey derives from the pick
        parts = [w.strip() for w in pan._hint().split("   ") if w.strip()]
        assert len(parts) >= 2 and all(len(w) <= 26 for w in parts)


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
    a.egg_type, b.egg_type = 0, 6                    # greenhills vs datatunnel
    sa, sb = a.background(), b.background()
    assert sa and sb and sa != sb
    assert backgrounds.scene_for_egg(0) != backgrounds.scene_for_egg(6)
    assert a.background() == sa                      # the home scene stands still
    assert a.background(file="tourneyBack") != sa    # the arena override still wins


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
    assert len(set(settled)) == 2                 # only the two bob poses remain


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


def test_every_drill_completes_through_its_strike_within_budget():
    """Training-anim audit 2026-07-05: the 30-tick smoke never reached the
    strike volley or the score reveal -- drive all four drills to DONE with
    every frame inside the 12x40 arena (menu -> play -> strike -> done)."""
    import random
    from tuipet.training import TrainingPanel

    plays = {
        "vaccine": lambda pan: pan.key("space"),
        "data": lambda pan: (pan.key("down" if pan.tt_shield[pan.tt_round] else "up")
                             if not pan.fired else None),
        "virus": lambda pan: pan.key("space") if getattr(pan, "pos", 0) > 80 else None,
        "hp": lambda pan: (setattr(pan, "hp_pick", pan.hp_target), pan.key("enter")),
    }
    moves = {"vaccine": ["2"], "data": ["3"],       # digits jump-start a drill
             "virus": ["4"], "hp": ["1"]}              # (the menu browses with arrows)
    for game, mv in moves.items():
        random.seed(5)
        p = _pet()
        p.energy = p.max_energy
        p._set_mood(100)
        p.obedience = 900
        pan = TrainingPanel(p)
        for m in mv:
            pan.key(m)
        assert pan.phase == "play", f"{game} never entered play"
        frames = 0
        while pan.phase != "done":
            pan.anim()
            _render(pan)
            if pan.phase == "play":
                plays[game](pan)
            frames += 1
            assert frames < 3000, f"{game} wedged in phase {pan.phase}"
        assert pan.result                      # the score reveal landed


def test_every_drill_strip_follows_the_one_formula():
    """Consistency audit (Joel 2026-07-06): every drill's strip = action cue
    (+ progress + meter where the drill has them) -- game objects live in the
    LCD, numbers on the status card.  data/virus carry NO raw numbers (the
    old virus gauge trailed the bar position; the old data gauge echoed the
    card's shield row)."""
    import re
    from tuipet.training import TrainingPanel
    p = _pet()
    p.obedience = 500
    for gi, gk in ((0, "hp"), (1, "vaccine"), (2, "data"), (3, "virus")):
        pan = TrainingPanel(p)
        pan.gi = gi
        pan.key("enter")
        g = pan._gauge()
        assert "[b]" in g, f"{gk}: no bold action cue"
        assert "▸" not in g and "●" not in g and "■" not in g and "▲" not in g, \
            f"{gk}: game glyphs leaked into the strip"
        if gk in ("data", "virus"):
            assert not re.search(r"\d", g), f"{gk}: raw numbers belong on the card: {g!r}"
