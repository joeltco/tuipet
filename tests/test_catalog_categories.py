"""CATEGORIES — items refactor P3 + P4 (2026-07-23).

Joel: "r1 b, r2 yes rename them".

P3 re-cut the category set so each name maps to a LIVE system instead of
to vibes.  The two that LIED are gone: "Medical" held death and
inheritance (never a med), and "Evolution" held the dumbbell.

P4 makes the set visible the way R1=b asked -- as dim sub-headers INSIDE
the Items tab, not as more tabs.  The tab bar is 38 cells and silently
truncates (plan audit A2), so eight tabs would simply vanish; sub-headers
scroll with the list and are not capped at all.

The pins below guard the thing the plan called goal 1: ONE grouping, not
three.  Before this arc the catalog said six categories, use_item's
comments said five, and the tab bar said four.
"""
from tuipet import shop, shopscreen
from tuipet.pet import Pet
from tuipet.shopscreen import ShopPanel

ITEM_CATEGORIES = ("Food", "Medicine", "Care", "Training", "Play",
                   "Evolution", "Legacy", "Adventure")


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", **kw)
    p.bits = 99999
    return p


# ---- P3: the set itself ----------------------------------------------------

def test_the_category_set_is_exactly_the_ruled_one():
    assert {v.category for v in shop.CATALOG.values()} == set(ITEM_CATEGORIES)


def test_the_lying_names_are_gone():
    """"Medical" never held a medicine and "Toy" undersold what the toys
    do; both were renamed by R2.  If either comes back, something has
    re-authored a category by hand."""
    live = {v.category for v in shop.CATALOG.values()}
    assert "Medical" not in live
    assert "Toy" not in live
    assert "Fruit" not in live          # never existed; the dead branch


def test_category_order_covers_every_live_category():
    live = {v.category for v in shop.CATALOG.values()}
    assert live <= set(shop.CATEGORY_ORDER)
    assert shop.ARMOR_CATEGORY in shop.CATEGORY_ORDER   # eggs, untouched


def test_medicine_holds_the_ailment_cures_and_legacy_holds_the_dead():
    assert shop.CATALOG["bandage"].category == "Medicine"
    assert shop.CATALOG["vitamin"].category == "Medicine"
    assert shop.CATALOG["revive_floppy"].category == "Legacy"
    assert shop.CATALOG["digimemory"].category == "Legacy"


def test_training_holds_the_body_items():
    for k in ("dumbbell", "slim_drink", "energy_drink"):
        assert shop.CATALOG[k].category == "Training", k


# ---- goal 1: ONE grouping, not three ---------------------------------------

def test_the_tab_grammar_names_only_real_categories():
    """The pin that would have caught "Fruit" years ago: every category
    named in the tab map must exist in the catalog (or be the egg
    category, which is applied to dynamic rows)."""
    live = {v.category for v in shop.CATALOG.values()} | {shop.ARMOR_CATEGORY}
    for _tab, cats in shopscreen.GROUPS:
        for c in cats or ():
            assert c in live, f"tab grammar names dead category {c!r}"


def test_every_category_has_a_tab_home():
    tabbed = set()
    for _tab, cats in shopscreen.GROUPS:
        tabbed |= set(cats or ())
    assert {v.category for v in shop.CATALOG.values()} <= tabbed


# ---- P4: the sub-headers ---------------------------------------------------

def test_the_items_tab_groups_under_sub_headers():
    p = _pet()
    for k in shop.CATALOG:
        p.add_item(k)
    pan = ShopPanel(p, start_mode="bag")
    pan.tab = pan._tabs().index("Items")
    rows = pan._rows()
    heads = [r["header"] for r in rows if r.get("header")]
    assert heads, "the Items tab lost its sub-headers"
    # headers appear in CATEGORY_ORDER order, never duplicated
    assert heads == sorted(heads, key=shop.CATEGORY_ORDER.index)
    assert len(heads) == len(set(heads))
    # every non-header row sits under its OWN header
    current = None
    for r in rows:
        if r.get("header"):
            current = r["header"]
        else:
            assert r["category"] == current, (r["name"], current)


def test_flat_tabs_get_no_headers():
    """A header over a single-category list is noise."""
    p = _pet()
    for k in shop.CATALOG:
        p.add_item(k)
    pan = ShopPanel(p, start_mode="bag")
    for i, name in enumerate(pan._tabs()):
        if name == "Items":
            continue
        pan.tab = i
        assert not any(r.get("header") for r in pan._rows()), name


def test_a_header_is_never_selectable():
    """The navigation contract: down, up and the page leaps all step OVER
    a sub-header, from every starting row, in both modes."""
    p = _pet()
    for k in shop.CATALOG:
        p.add_item(k)
    for mode in ("shop", "bag"):
        pan = ShopPanel(p, start_mode=mode)
        pan.tab = pan._tabs().index("Items")
        pan.cursor = 0
        pan._normalize_cursor(pan._rows())
        n = len(pan._rows())
        for k in (["down"] * (n + 2) + ["up"] * (n + 2)
                  + ["pagedown", "pagedown", "pageup", "pageup"]):
            pan.key(k)
            rows = pan._rows()
            assert not rows[pan.cursor].get("header"), (mode, k)


def test_a_cursor_parked_on_a_header_is_snapped_off_before_acting():
    """First line of defence: key() normalizes on entry, so a cursor left
    on a label by anything (session memory, a list that shrank) is moved
    to a real row before ENTER is interpreted."""
    p = _pet()
    p.add_item("bandage")
    pan = ShopPanel(p, start_mode="bag")
    pan.tab = pan._tabs().index("Items")
    rows = pan._rows()
    pan.cursor = next(i for i, r in enumerate(rows) if r.get("header"))
    pan.key("down")
    assert not pan._rows()[pan.cursor].get("header")


def test_acting_on_a_header_does_nothing(monkeypatch):
    """Second line of defence, tested in isolation.  With the snap
    disabled, ENTER and R on a label must still refuse -- so the guard
    holds even if some future path reaches the branch un-normalized."""
    p = _pet()
    p.add_item("bandage")
    pan = ShopPanel(p, start_mode="bag")
    pan.tab = pan._tabs().index("Items")
    monkeypatch.setattr(ShopPanel, "_normalize_cursor",
                        lambda self, rows: None)
    rows = pan._rows()
    hdr = next(i for i, r in enumerate(rows) if r.get("header"))
    pan.cursor = hdr
    assert pan.key("enter") is None
    pan.cursor = hdr
    assert pan.key("r") is None
    assert p.inventory.get("bandage") == 1      # nothing was consumed or sold


def test_the_panel_still_fits_the_lcd_with_headers():
    """The layout law: 38 cells wide, no more than 13 lines."""
    p = _pet()
    for k in shop.CATALOG:
        p.add_item(k)
    for mode in ("shop", "bag"):
        for town in (None, 3):
            pan = ShopPanel(p, start_mode=mode, town_id=town)
            for i in range(len(pan._tabs())):
                pan.tab = i
                pan._normalize_cursor(pan._rows())
                lines = pan.text().plain.split("\n")
                assert len(lines) <= 13, (mode, town, i, len(lines))
                for ln in lines:
                    assert len(ln) <= 38, (mode, town, i, repr(ln))


def test_the_dossier_goes_quiet_rather_than_pricing_a_label():
    p = _pet()
    p.add_item("bandage")
    pan = ShopPanel(p, start_mode="bag")
    pan.tab = pan._tabs().index("Items")
    rows = pan._rows()
    pan.cursor = next(i for i, r in enumerate(rows) if r.get("header"))
    txt = pan.text().plain            # must render, not raise
    assert "BAG" in txt
