"""The TUIPET shop/bag (catalog authored 2026-07-18): the 29-item CATALOG
table -- DSprite's mechanics grammar wearing DVPet art on every cell --
plus the classic EGG shelf and HONORS board riding the last tabs."""

from tuipet import shop
from tuipet.pet import Pet, FULL_HUNGER
from tuipet.shopscreen import ShopPanel


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", bits=100000)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_catalog_is_the_authored_tuipet_shelf():
    cat = shop.catalog()
    keys = {e["key"] for e in cat}
    assert {"energy_drink", "steak", "revive_floppy", "ball",
            "dna_crystal", "egg_of_courage"} <= keys
    assert all(e["price"] > 0 for e in cat)
    # the theme skins, storage drive and retired vitems never reach the shelf
    assert not any(k.startswith("theme_") for k in keys)
    assert "best_fruit" not in keys and "premium_meat" not in keys
    # birthday treats are never SOLD
    assert {"cupcake", "cookie", "candy"} & keys == set()


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

    q = _pet(hunger=1, energy=0)
    q.add_item("tuna")
    q.use_item("tuna")
    assert q.hunger == 3 and q.energy == 1

    r = _pet(care_mistakes=2)
    r.add_item("textbook")
    r.use_item("textbook")
    assert r.care_mistakes == 0                # the Textbook studies ALL away


def test_a_refusal_keeps_the_item():
    p = _pet(care_mistakes=0)
    p.add_item("textbook")
    out = p.use_item("textbook")
    assert p.inventory.get("textbook") == 1   # not consumed


def test_the_poison_mushroom_lives_up_to_the_label():
    p = _pet()
    p.add_item("poison_mushroom")
    p.use_item("poison_mushroom")
    assert p.dead


def test_revive_floppy_only_works_on_the_dead():
    p = _pet()
    p.add_item("revive_floppy")
    out = p.use_item("revive_floppy")
    assert p.inventory.get("revive_floppy") == 1         # refused, kept
    p.dead = True
    p.use_item("revive_floppy")
    assert not p.dead and not p.inventory


def test_steak_satiety_gates_hunger_decay():
    p = _pet(hunger=2)
    p.add_item("steak")
    p.use_item("steak")
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
    pan.tab = 1                               # the Items tab
    rows = pan._rows()
    pan.cursor = next(i for i, e in enumerate(rows)
                      if e.get("key") == "energy_drink")
    plain = pan.text().plain
    assert "x2" in plain                      # the held marker on the row
    assert "hold x2" in plain                 # and the dossier info row


def test_the_info_prices_a_shortfall():
    p = _pet(bits=100)
    pan = ShopPanel(p)
    pan.tab = 1                               # Items: a 300b good sits early
    row = next(e for e in pan._rows() if e.get("price") == 300)
    info = pan._info(row, 26)
    assert any("short 200b" in line for line in info)


def test_buy_feedback_actually_renders_now():
    """self.msg was never drawn anywhere -- the verdict flashes for a beat
    (the eggselect _flash pattern).  Round 31: it rides the STRIP now,
    verdict > wave tease > hints, and hints return when it expires."""
    p = _pet()
    pan = ShopPanel(p)
    pan.key("enter")                          # buy the first Food row
    assert "Bought" in pan.strip()
    pan.msg_t = 0
    assert "Bought" not in pan.strip()        # the flash expires
    assert "ENTER" in pan.strip()             # ...and the keys return


def test_the_bag_dossier_shows_resale():
    p = _pet()
    p.inventory["energy_drink"] = 1
    pan = ShopPanel(p, start_mode="bag")
    pan.msg_t = 0
    pan.tab = 1                               # Items tab holds the drink
    plain = pan.text().plain
    from tuipet.app import _hud_plain
    assert "R sell" in _hud_plain(pan.strip())   # keys ride the STRIP (round 31)
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


def test_every_item_wears_its_own_dvpet_art():
    """TUIPET catalog 2026-07-18 ("you can make the items whatever you want
    using the sprites"): EVERY cell is illustrated with a real DVPet strip --
    the capsule-placeholder era is over."""
    from tuipet import data
    ic = data.load_icons()
    assert shop.ICON_KEYS["energy_drink"] == "f:17"   # exact name matches
    assert shop.ICON_KEYS["sleeping_pill"] == "f:34"
    assert shop.ICON_KEYS["x_antibody"] == "i:79"
    assert shop.ICON_KEYS["music_player"] == "i:9"    # the alarm's heir
    assert shop.ICON_KEYS["textbook"] == "i:0"        # the eraser's heir
    assert shop.ICON_KEYS["grow_capsule"] == "i:78"   # the gear's heir
    for k, ak in shop.ICON_KEYS.items():
        assert ic.get(ak), (k, ak)                    # every mapping resolves
    assert "i:68" not in shop.ICON_KEYS.values()      # no capsule pods left
    pan = ShopPanel(_pet())
    for pan.tab in range(len(pan._tabs()) - 1):       # every goods tab
        assert all(any(l.strip() for l in pan._icon(e))
                   for e in pan._rows() if not e.get("header"))


def test_the_toys_turn_live_dials():
    """The toy law (Joel 2026-07-18 "so the toys are worthless?"): exercise
    sheds weight, couch time buys energy at a weight price -- all on live
    meters, and the show is the panel's business."""
    p = _pet(weight=30, energy=0)
    for k in ("ball", "skateboard", "television"):
        p.add_item(k)
    p.use_item("ball")
    assert p.weight == 29
    p.use_item("skateboard")
    assert p.weight == 27 and p.energy == -1
    p.use_item("television")
    assert p.weight == 28 and p.energy == 2
    q = _pet()
    q.poop, q.poop_sizes = 2, [1, 2]
    q.add_item("bubble_bath")
    q.use_item("bubble_bath")
    assert q.poop == 0                          # the stylish clean is real


def test_the_dna_crystal_banks_own_field():
    p = _pet()
    p.add_item("dna_crystal")
    field = p.field
    p.use_item("dna_crystal")
    assert p.dna_owned.get(field) == 10
    p.dna_owned[field] = 99                     # full bank refuses, keeps it
    p.add_item("dna_crystal")
    out = p.use_item("dna_crystal")
    assert p.inventory.get("dna_crystal") == 1


def test_legacy_bags_migrate_one_to_one():
    """The shelf turnover loses nobody's goods: every old key maps to its
    heir at load (shop.LEGACY_KEYS drives the save-heal)."""
    from tuipet import persistence
    p = _pet()
    save = persistence.to_save_dict(p)
    save["inventory"] = {"best_fruit": 2, "alarm_clock": 1, "time_gear": 3,
                         "energy_drink": 1}
    healed, _ = persistence.pet_from_save(save)
    assert healed is not None
    inv = healed.inventory
    assert inv.get("tuna") == 2 and inv.get("music_player") == 1
    assert inv.get("grow_capsule") == 3 and inv.get("energy_drink") == 1
    assert "best_fruit" not in inv and "alarm_clock" not in inv


def test_timed_items_deliver_the_hours_on_the_label():
    """The words won (Joel 2026-07-19, round 17): steak = 12 REAL hours of
    satiety, potty = 24 REAL hours of auto-clean, grow capsule = 120 REAL
    minutes of growth.  The old tick-denominated values delivered 1/60th
    while the labels promised hours -- the eat card's own countdown
    contradicted the steak message live."""
    p = _pet()
    p.add_item("steak"); p.use_item("steak")
    assert p.full_until - p.world_seconds == 12 * 3600.0
    p.add_item("port_potty"); p.use_item("port_potty")
    assert p.auto_clean_until - p.world_seconds == 24 * 3600.0
    s0 = p.stage_seconds
    p.add_item("grow_capsule"); p.use_item("grow_capsule")
    assert p.stage_seconds - s0 == 7200.0


def test_short_icons_anchor_to_the_baseline_not_the_ceiling():
    """Joel's report 2026-07-19: "giga meal sprite might be getting cut off
    in shop?"  The 24x18 rip is COMPLETE (the atlas gutters around f:28 are
    empty -- verified against spritesFood0.png); the lie was icon_cell
    top-floating short art over a dead bottom row.  Foods sit on plates:
    short art bottom-aligns, full-height art is untouched."""
    from tuipet import data, menu
    icons = data.load_icons()
    giga = menu.icon_cell(icons["f:28"][0])          # 24x18: one short row
    assert giga[0].strip() == ""                     # the dead row is on TOP...
    assert giga[-1].strip() != ""                    # ...the plate is on the floor
    steak = menu.icon_cell(icons["f:8"][0])          # 24x24: full height
    assert all(l.strip() for l in steak)             # unchanged, fills the cell


# ---- round 31 pins (shop screen tidy, 2026-07-19) ---------------------------

def test_the_shelf_fills_the_lcd_and_keys_left_the_footer():
    """The in-LCD footer doubled the strip's keys; its row feeds the shelf
    now -- header 2 + tab bar 1 + dossier 4 + list 5 = 12 rows exactly."""
    p = _pet()
    for mode in ("shop", "bag"):
        pan = ShopPanel(p, mode)
        pan.msg_t = 0
        lines = pan.text().plain.split("\n")
        assert len(lines) == 12
        assert "ENTER" not in lines[-1]           # no key footer in the LCD


def test_the_honors_tab_strip_says_wear():
    from tuipet.app import _hud_plain
    p = _pet()
    pan = ShopPanel(p)
    pan.msg_t = 0
    pan.tab = pan._tabs().index("Honors")
    s = _hud_plain(pan.strip())
    assert "ENTER wear" in s and len(s) <= 40


def test_refusals_and_shortfalls_sound_like_refusals():
    """A kept item (a _Refused) and "Not enough bits." both played the
    happy confirm chirp (round 31)."""
    p = _pet()
    pan = ShopPanel(p)
    pan.tab = pan._tabs().index("Honors")
    p.bits = 0
    pan.key("enter")                              # can't afford the honor
    assert pan.sfx == "error" and "Not enough bits" in pan.msg
    p.bits = 10**7                                # rich beyond any honor
    pan.key("enter")                              # now it buys fine
    assert pan.sfx == "confirm" and "Earned" in pan.msg


def test_escape_carries_a_live_verdict_home():
    """Keying on self.sfx was dead -- the app consumes sfx every frame, so
    buy-then-leave never showed its verdict.  msg_t is the live flash."""
    p = _pet()
    pan = ShopPanel(p)
    pan.msg_t = 0
    pan.key("enter")                              # buy: the flash is live
    pan.sfx = None                                # ...the app consumed the sfx
    done, note = pan.key("escape")
    assert done == "done" and "Bought" in note
    pan2 = ShopPanel(p)
    pan2.msg_t = 0                                # no live flash
    assert pan2.key("escape") == ("done", None)


def test_bag_header_counts_only_what_the_shelves_show():
    """An inventory key the catalog doesn't know (a newer build's item riding
    cloud sync past the bag heal) must not inflate the header: "8 items" over
    5 visible read as a broken bag (deep-state sweep 2026-07-22)."""
    from tuipet.shopscreen import ShopPanel
    from tuipet.pet import Pet
    p = Pet(num=29, stage="Champion", attribute="Vaccine")
    p.inventory = {"cupcake": 2, "sleeping_pill": 3, "from_the_future": 7}
    pan = ShopPanel(p, start_mode="bag", bag_only=True)
    head = pan.text().plain.split("\n")[0]
    assert "5 items" in head          # the unknown key is not counted...
    assert p.inventory["from_the_future"] == 7   # ...and not destroyed
