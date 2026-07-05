"""Every panel's text() must RENDER — with a real pet and real inventory.

The v0.2.166-175 feed-screen crash (bitmap_text read FULL/UPPER/LOWER after the
dead-code sweep deleted them) shipped because no test ever executed a panel's
icon path: 357 tests were green while pressing F crashed the app.  This sweep
instantiates every simple-constructor panel, walks its keys, and renders each
state.  It is deliberately shallow — its job is 'does it draw', not 'is it
right'."""
import pytest

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
    """Drive a panel: render, press keys (ignoring exits), re-render each time."""
    _render(panel)
    for k in keys:
        try:
            panel.key(k)
        except TypeError:
            break                                   # panel closed (returned done payload used by app)
        if hasattr(panel, "anim"):
            panel.anim()
        _render(panel)


def test_feed_panel_renders_every_selection():
    from tuipet.feedscreen import FeedPanel
    pan = FeedPanel(_pet())
    assert pan.options                              # the crash needs a selectable food
    for _ in range(len(pan.options) + 1):           # every icon in the list draws
        pan.text()
        pan.key("down")


def test_shop_panel_renders_shop_and_bag():
    from tuipet.shopscreen import ShopPanel
    pan = ShopPanel(_pet())
    _walk(pan, ["down", "down", "i", "down", "down", "r"])   # shop rows, bag rows, a sell


def test_the_simple_panels_all_draw():
    from tuipet.habitatscreen import HabitatPanel
    from tuipet.digicorescreen import DigiCorePanel
    from tuipet.assistscreen import AssistPanel
    from tuipet.dnascreen import DNAPanel
    from tuipet.jogressscreen import JogressPanel
    from tuipet.eggselectscreen import EggSelectPanel
    from tuipet.themescreen import ThemePanel
    from tuipet.deathscreen import DeathPanel
    from tuipet.feedscreen import FeedPanel
    p = _pet()
    _walk(HabitatPanel(p), ["down", "down", "up"])
    _walk(DigiCorePanel(p), ["space", "space", "right", "right", "right",
                             "right", "right", "right", "down", "enter", "down"])
    _walk(AssistPanel(p), ["enter", "enter"])
    _walk(DNAPanel(p), ["down", "right"])
    _walk(JogressPanel(p), ["down"])
    _walk(EggSelectPanel(), ["right", "right", "left"])
    _walk(ThemePanel(), ["down", "up", "escape"])
    dead = _pet(dead=True)
    _walk(DeathPanel(dead), [])
    _walk(FeedPanel(p), ["down", "up"])


def test_town_and_adventure_panels_draw():
    from tuipet.adventurescreen import AdventurePanel
    p = _pet()
    p.sleep_limit = 9e9
    pan = AdventurePanel(p)
    _walk(pan, ["down", "up"])


def test_shop_egg_tab_renders_the_egg_icon():
    """The egg tab's preview slot draws the REAL egg sprite (audit 2026-07-04):
    exercise that icon path with a buyable egg so it can never ship broken."""
    from tuipet import persistence
    from tuipet.shopscreen import ShopPanel
    persistence.wins_add(50)               # sandboxed: Sakumon's license unlocks
    p = _pet()
    pan = ShopPanel(p)
    tabs = pan._tabs()
    assert "egg" in tabs
    for _ in range(len(tabs)):             # walk to the egg tab, rendering as we go
        if tabs[pan.tab] == "egg":
            break
        pan.key("right")
        pan.text()
    assert tabs[pan.tab] == "egg"
    pan.text()                             # the egg icon path executes
    pan.key("down")
    pan.text()


def test_scene_screens_fit_the_physical_lcd_in_every_state():
    """Box-clip audit 2026-07-04: the visual sweep's scene screens stacked
    header/note/footer INSIDE the LCD and ran 15-17 lines into the physical
    12-row box -- the live compositor clipped everything below the arena
    (the town errand strip, adventure controls, drill gauges, the epitaph)
    while the PNG raster harness rendered the full Text.  Scene chrome now
    rides the #msg strip (panel.strip()); this walks the REAL deep states
    through the _render budget so the box can never be overflowed again."""
    import random
    random.seed(3)
    p = _pet()

    from tuipet.training import TrainingPanel, GAMES
    for gi in range(len(GAMES)):
        pan = TrainingPanel(p)
        pan.gi = gi
        _render(pan)
        pan.key("enter")                        # into the drill
        for _ in range(30):                     # play ticks + a few presses
            pan.anim()
            _render(pan)
            pan.key("space")
        pan.strip()                             # the gauge renders

    from tuipet.adventurescreen import AdventurePanel
    pan = AdventurePanel(p)
    for _ in range(60):                         # travel: encounters may open battle subs
        pan.anim()
        _render(pan)
    pan.sub = None; pan._pending = None
    pan.discovering, pan.travelling = True, False
    _render(pan); assert pan.strip()
    pan.key("enter")                            # investigate playbook end-to-end
    for _ in range(60):
        pan.anim()
        _render(pan)
        pan.strip()

    from tuipet.townscreen import TownPanel
    pan = TownPanel(p, 0)
    _render(pan); assert "Food" in pan.strip()
    for key in ("food", "items", "sell", "cups"):
        pan.phase, pan.cursor = key, 0
        _render(pan)
    from tuipet import tournament as tmod
    tr = next((t for t in (tmod.trophy_by_id(i) for i in range(40)) if t), None)
    pan.phase = "menu"
    pan.tourney = tmod.Tournament(p, tr)
    _render(pan); assert "fight" in pan.strip()
    pan.key("space")                            # the bout opens (battle sub renders)
    for _ in range(20):
        pan.anim()
        _render(pan)

    from tuipet.dnascreen import DNAPanel
    pan = DNAPanel(p)
    pan.phase, pan.bet = "mash", 10
    for _ in range(15):
        pan.anim()
        _render(pan)
        pan.key("space")
    assert "mash" in pan.strip()

    from tuipet.deathscreen import DeathPanel
    dead = _pet(dead=True)
    pan = DeathPanel(dead)
    _render(pan)
    assert "R.I.P." in pan.strip()


def test_feed_screen_surfaces_the_dp_meter():
    """Audit 2026-07-04: a strength food banks +1 DP toward a jogress (Pen20),
    but nothing on the feed screen said so -- protein's whole point was
    invisible.  The header carries the meter; strength foods carry the tag."""
    from tuipet import data
    from tuipet.feedscreen import FeedPanel, _effect_line
    p = _pet()
    p.dp = 2
    pan = FeedPanel(p)
    assert "DP 2/4" in pan.text().plain
    prot = next(f for f in data.load_foods() if f.get("strength", 0) > 0)
    assert "DP+1" in _effect_line(prot)
    plain = next(f for f in data.load_foods() if f.get("strength", 0) == 0 and f.get("show"))
    assert "DP" not in _effect_line(plain)


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
    jogress EMPTY (fusions are data-rare) -- the real pick/fusing/fused states
    ran 15-16 lines and clipped.  Scene-only now; the strip carries the pick."""
    from tuipet.jogressscreen import JogressPanel, FUSE_STEPS
    p = _pet()
    pan = JogressPanel(p)
    pan.options = [{"num": 4, "name": "Agumon", "attribute": "Vaccine",
                    "stage": "Champion", "partners": ["Vaccine"],
                    "partner_num": 7, "partner_name": "Gabumon"}]
    _render(pan)
    assert "Gabumon" in pan.strip() and "1/1" in pan.strip()
    pan.phase, pan.old_num, pan.partner_num = "fusing", 100, 7
    for s in range(FUSE_STEPS):
        pan.fuse_step = pan.frame_i = s
        _render(pan)
    assert pan.strip() == "DNA... connect!"
    pan.phase = "fused"
    pan.fused, pan.result_msg = pan.options[0], "Jogress! Fused into Agumon!"
    _render(pan)
    assert "Fused into" in pan.strip()
