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


def _walk(panel, keys, renders=6):
    """Drive a panel: render, press keys (ignoring exits), re-render each time."""
    panel.text()
    for k in keys:
        try:
            panel.key(k)
        except TypeError:
            break                                   # panel closed (returned done payload used by app)
        if hasattr(panel, "anim"):
            panel.anim()
        panel.text()


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
