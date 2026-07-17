"""The DSprite shop/bag (BASIC VPET 2026-07-16): the fixed vitems catalog,
the classic EGG shelf and HONORS board riding the last tabs, and the
17-item Pet.use_item effect table."""
import random

from tuipet import shop
from tuipet.pet import Pet, FULL_HUNGER
from tuipet.shopscreen import ShopPanel


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", bits=100000)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_catalog_is_the_fixed_vitems_shelf():
    cat = shop.catalog()
    keys = {e["key"] for e in cat}
    assert {"energy_drink", "premium_meat", "revive_floppy",
            "egg_of_courage"} <= keys
    assert all(e["price"] > 0 for e in cat)
    # the theme skins and storage drive never reach the shelf
    assert not any(k.startswith("theme_") for k in keys)


def test_buy_bags_it_and_sell_returns_half():
    p = _pet()
    e = shop.entry("energy_drink")
    msg, sfx = shop.buy(p, e)
    assert sfx == "confirm" and p.inventory.get("energy_drink") == 1
    msg, sfx = shop.sell(p, e)
    assert sfx == "confirm" and "energy_drink" not in p.inventory


def test_the_item_effects_apply():
    p = _pet(energy=0)
    p.add_item("energy_drink")
    assert "Energy" in p.use_item("energy_drink")
    assert p.energy == p.max_energy and not p.inventory

    q = _pet(hunger=1, strength=0)
    q.add_item("best_fruit")
    q.use_item("best_fruit")
    assert q.hunger == 2 and q.strength == 1

    r = _pet(care_mistakes=2)
    r.add_item("care_mistake_eraser")
    r.use_item("care_mistake_eraser")
    assert r.care_mistakes == 1


def test_a_refusal_keeps_the_item():
    p = _pet(care_mistakes=0)
    p.add_item("care_mistake_eraser")
    out = p.use_item("care_mistake_eraser")
    assert p.inventory.get("care_mistake_eraser") == 1   # not consumed


def test_deadly_fruit_lives_up_to_the_label():
    p = _pet()
    p.add_item("deadly_fruit")
    p.use_item("deadly_fruit")
    assert p.dead


def test_revive_floppy_only_works_on_the_dead():
    p = _pet()
    p.add_item("revive_floppy")
    out = p.use_item("revive_floppy")
    assert p.inventory.get("revive_floppy") == 1         # refused, kept
    p.dead = True
    p.use_item("revive_floppy")
    assert not p.dead and not p.inventory


def test_premium_meat_satiety_gates_hunger_decay():
    p = _pet(hunger=2)
    p.add_item("premium_meat")
    p.use_item("premium_meat")
    assert p.hunger == FULL_HUNGER
    assert p.full_until > p.world_seconds
    h0 = p.hunger
    p._tick_hunger(600.0)                                # satiety holds the line
    assert p.hunger == h0


def test_crest_egg_maps_to_the_classic_digimental():
    """The JP/EN dub swap, CORRECTED (armor canon audit 2026-07-18): the EN
    Reliability egg is JP Sincerity 誠実 = the WATER family (item 20,
    Submarimon); the EN Sincerity egg is JP Purity 純真 (item 18, Shurimon).
    v0.5.5 had them backwards."""
    from tuipet.pet import Pet as _P
    assert _P._CREST_IDS["egg_of_reliability"] == 20     # water armors
    assert _P._CREST_IDS["egg_of_sincerity"] == 18       # ninja/plant armors
    assert _P._CREST_IDS["egg_of_destiny"] == 25         # Fate
    assert len(_P._CREST_IDS) == 11


def test_shop_panel_walks_every_tab_and_the_bag():
    p = _pet()
    pan = ShopPanel(p)
    assert "Honors" in pan.tabs and shop.EGGS_CATEGORY in pan.tabs
    for _ in range(len(pan.tabs)):
        assert pan.text().plain
        pan.key("right")
    pan.key("tab")                       # the bag
    assert pan.text().plain


def test_citramon_is_reachable_by_timed_care_now():
    """Joel 2026-07-16: the food lock is unlocked -- the corpus' one
    food-locked form competes like everyone since the orange left with the
    food catalog."""
    from tuipet import data, evolution
    citra = next((n for n, r in data.load_requirements().items()
                  if r.get("evol_food", -1) != -1), None)
    assert citra is not None, "the food-locked row vanished from the data"
    src = __import__("inspect").getsource(evolution.check)
    assert "evol_food" not in src.replace("EvolFood", "")  # the gate is gone
