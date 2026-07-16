"""Standing still on an adventure = the home biome (Joel 2026-07-12), and
shops/training stay town-only there.

- A quietly standing pet draws the same scene actors the home screen does
  (poop, sick skull, weather) instead of just a walking sprite.
- The road bag can use/sell but never TAB into the buy shop; there is no
  training key on the road; the town offers a shop but no training.
"""
from tuipet import arena, grid
from tuipet.adventurescreen import AdventurePanel
from tuipet.shopscreen import ShopPanel
from tuipet.townscreen import TownPanel
from tuipet.pet import Pet


def _adv(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.bits = 9000
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    adv = AdventurePanel(p)
    for _ in range(50):
        adv.anim()
    # force quiet standing
    adv.travelling = False
    adv._scene = adv._care = adv._parade = adv._retreat = adv._trans = adv._pulse = None
    adv._refuse_t = 0
    adv.discovering = False
    for _ in range(4):
        adv.anim()
    return p, adv


def test_quiet_standing_is_recognised():
    _, adv = _adv()
    assert adv._quiet_standing()


def test_standing_scene_draws_poop_and_sick_actors():
    """The bare standing sprite gains the home actors: a dirty/sick pet shows
    the filth block + the sick skull that home draws (the biome, not a walk)."""
    p, adv = _adv()
    p.poop = 3
    p.poop_sizes = [2, 3, 4]
    p.sick = True
    p.anim = "idle"
    for _ in range(4):
        adv.anim()
    # the pure actor overlay is non-empty for this state (what got wired in);
    # .plain can't show it (text export renders every cell as the same block),
    # so pin the actors + that standing routes through the biome renderer
    pts = arena._effect_overlay(p, adv.frame_i // 4, 40, grid.PXH, tick=adv.frame_i)
    assert pts, "no scene actors built for a dirty/sick pet"
    assert adv.text().plain == adv._biome_frame().plain


def test_road_bag_cannot_tab_into_the_shop():
    """Shops are town-only on an adventure: the road bag ('i') never reaches
    the buy shop, even with TAB."""
    p, adv = _adv()
    adv.key("i")
    assert isinstance(adv.sub, ShopPanel) and adv.sub.mode == "bag"
    assert adv.sub.bag_only
    adv.sub.key("tab")
    assert adv.sub.mode == "bag", "TAB leaked the road bag into the shop"
    assert "shop" not in adv.sub.strip().lower()


def test_no_training_on_the_road():
    """There is no training key mid-adventure -- 't' does nothing."""
    p, adv = _adv()
    before = (adv.sub, adv.travelling)
    r = adv.key("t")
    assert r is None
    assert adv.sub is None                       # no panel opened
    assert (adv.sub, adv.travelling) == before


def test_town_has_a_shop_but_no_training():
    p, adv = _adv()
    town_id = next(iter(__import__("tuipet.world", fromlist=["TOWNS"]).TOWNS))
    tp = TownPanel(p, town_id)
    body = tp.strip().lower()
    assert "food" in body or "items" in body or "shop" in body  # a shop is here
    assert "train" not in body                                  # but no training


def test_weather_enabled_iff_habitat_has_a_weather_frame():
    """Joel's rule (2026-07-12): a habitat has weather IFF it has a weather
    frame.  weather_chance (>0) must agree with the artwork (a 5th bg frame)
    for every habitat -- no drift, no hand-maintained exclusion list."""
    from tuipet import data
    habs = data.load_habitats()
    bgs = data.load_backgrounds()
    for hid, h in habs.items():
        has_frame = len(bgs.get(h.get("bg", "")) or []) > 4
        has_weather = h["weather_chance"] > 0
        assert has_frame == has_weather, (
            f"{h['name']}: weather frame={has_frame} but weather={has_weather}")


