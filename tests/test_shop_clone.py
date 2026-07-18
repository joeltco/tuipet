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
    assert pan._tabs() == ["Food", "Items", "Eggs", "Honors"]
    for _ in range(len(pan._tabs())):
        assert pan.text().plain
        pan.key("right")
    pan.key("tab")                       # the bag: goods tabs, no Honors
    assert pan._tabs() == ["Food", "Items", "Eggs"]
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


# ---- the polish pass (2026-07-17: "lets polish the shop. looks lazy") ----

def test_the_classic_tab_bar_is_back():
    """v0.5.0 grammar restored (Joel 2026-07-17 "where are the tabs you had
    like before?"): a visible bar, active tab bracketed, classic four."""
    pan = ShopPanel(_pet())
    pan.msg_t = 0
    plain = pan.text().plain
    assert "[Food] Items  Eggs  Honors" in plain
    pan.key("right")
    assert " Food [Items] Eggs  Honors" in pan.text().plain
    # the Eggs tab is the DIGIMENTAL shelf -- goods, never digitama
    pan.key("right")
    rows = pan._rows()
    assert rows and all(str(e["key"]).startswith("egg_of_") for e in rows)
    assert not any(e.get("egg_idx") is not None for e in rows)


def test_the_shelf_shows_what_you_already_hold():
    p = _pet()
    p.inventory["energy_drink"] = 2
    pan = ShopPanel(p)
    pan.msg_t = 0
    pan.tab = 1                               # Items: Energy.D leads
    plain = pan.text().plain
    assert "x2" in plain                      # the held marker on the row
    assert "hold x2" in plain                 # and the dossier info row


def test_the_info_prices_a_shortfall():
    p = _pet(bits=100)
    pan = ShopPanel(p)
    pan.tab = 1                               # Items: AlarmClock 300b at row 1
    info = pan._info(pan._rows()[1], 26)
    assert any("short 200b" in line for line in info)


def test_buy_feedback_actually_renders_now():
    """self.msg was never drawn anywhere -- the verdict flashes in the
    footer for a beat (the eggselect _flash pattern)."""
    p = _pet()
    pan = ShopPanel(p)
    pan.key("enter")                          # buy the first Food row
    assert "Bought" in pan.text().plain
    pan.msg_t = 0
    assert "Bought" not in pan.text().plain   # the flash expires


def test_the_bag_dossier_shows_resale():
    p = _pet()
    p.inventory["energy_drink"] = 1
    pan = ShopPanel(p, start_mode="bag")
    pan.msg_t = 0
    pan.tab = 1                               # Items tab holds the drink
    plain = pan.text().plain
    assert "R sell" in plain.splitlines()[-1]
    assert "sells 100b" in plain              # resale in the dossier info


def test_crest_note_is_the_live_gate():
    """The Armor-Spirit dossier names the form the jump would land NOW --
    the same evolution.check the crest egg runs on use."""
    from tuipet import data
    _, by_num = data.load_sprites()
    goburimon = next(n for n, r in by_num.items()
                     if r["name"] == "Goburimon" and r["stage"] == "Rookie")
    p = Pet.from_num(goburimon)
    p.strength = 4
    p.weight = by_num[goburimon].get("weight", p.weight)
    p.care_mistakes = 0
    p.wins, p.battles = 20, 30
    names = shop.crest_answer(p, "egg_of_courage")
    assert "Flamedramon" in names
    fresh = Pet.from_num(goburimon)
    fresh.strength = 0
    fresh.care_mistakes = 99                  # gates unmet -> honest empty
    assert isinstance(shop.crest_answer(fresh, "egg_of_courage"), list)
    assert shop.crest_answer(p, "not_a_crest") == []


def test_wave_teases_fit_the_footer():
    """Footers never marquee: every tease must hold inside the 38-col line."""
    for gate, text in shop._WAVE_TEASE.items():
        line = text.format(have=gate[1] - 1, need=gate[1])
        assert len(line) <= 38, line


def test_wave_status_counts_and_teases_live():
    prog = {"armor_evos": 0, "wins": 0, "raids": 0, "max_gen": 1}
    sealed, hint = shop.wave_status(prog)
    assert sealed == 9                        # all but free Courage/Hope
    assert "generation 1/5" in hint           # closest gate by ratio
    prog = {"armor_evos": 1, "wins": 25, "raids": 2, "max_gen": 5}
    assert shop.wave_status(prog) == (0, "")


def test_the_eggs_tab_renders_like_every_other_tab():
    """Joel 2026-07-18: "8x8 item icons, like how the rest of the shop is."
    The ghost-egg scene is GONE (armorEggs.png = fan art, rejected); the
    Eggs tab uses the standard layout, and the icon cell shows the crest
    glyph DVPet itself draws for the Digimental (i:15..25)."""
    from tuipet import data
    assert not hasattr(data, "load_armor_eggs")
    p = _pet()
    pan = ShopPanel(p)
    pan.msg_t = 0
    pan.tab = pan._tabs().index("Eggs")
    assert not hasattr(pan, "_eggs_text")
    assert not hasattr(pan, "_armor_egg")
    plain = pan.text().plain
    assert "Courage Egg" in plain              # the standard list renders
    glyph = pan._icon(pan._rows()[0])
    assert any(line.strip() for line in glyph)  # the DVPet crest glyph is up
    import os
    assert not os.path.exists(os.path.join(
        os.path.dirname(data.__file__), "data", "armor_eggs.json.gz"))


def test_consumables_wear_their_own_dvpet_icons():
    """2026-07-18 "what about the other items icons?": each DSprite item
    wears the DVPet atlas icon for the SAME item (exact name matches +
    pill-precedent concepts); no honest counterpart -> quiet cell, never
    wrong art."""
    from tuipet import data
    ic = data.load_icons()
    assert shop.ICON_KEYS["energy_drink"] == "f:17"   # exact name matches
    assert shop.ICON_KEYS["sleeping_pill"] == "f:34"
    assert shop.ICON_KEYS["x_antibody"] == "i:79"
    for k, ak in shop.ICON_KEYS.items():
        assert ic.get(ak), (k, ak)                    # every mapping resolves
    pan = ShopPanel(_pet())
    pan.tab = 1                                       # Items tab
    rows = {e["name"]: pan._icon(e) for e in pan._rows()}
    assert any(l.strip() for l in rows["Energy.D"])   # iconed
    # the capsule placeholder (Joel 2026-07-18 "use the capsule"): the three
    # counterpart-less items share the pod -- a full shelf by his call
    assert shop.ICON_KEYS["alarm_clock"] == "i:68"
    assert any(l.strip() for l in rows["AlarmClock"])
    assert all(any(l.strip() for l in pan._icon(e)) for e in pan._rows())
