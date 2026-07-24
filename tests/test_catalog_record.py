"""THE CATALOG RECORD — items refactor P1 (2026-07-23).

Joel: "take all items, make sure theyre in catagories, and we gotta redo
them all to fit everything we got going on."  P1 is the mechanical half:
the authored 6-tuple becomes a NAMED record so consumers stop saying
`v[3]` and start saying `.category`.

These pins guard the two things P1 promises -- that the rename is
BEHAVIOUR-FREE, and that the field order is the authored order (P2 widens
this record, and a silent field reshuffle would corrupt every read).
"""
import pytest

from tuipet import shop


def test_every_entry_is_the_named_record():
    assert shop.CATALOG, "the catalog is empty"
    for key, v in shop.CATALOG.items():
        assert isinstance(v, shop.Item), key


def test_field_order_matches_the_authored_table():
    """P2 appends fields; it must never REORDER them.  The authored
    literal is positional, so the order IS the contract."""
    assert shop.Item._fields == (
        "name", "icon", "price", "category", "effect", "flavor")


def test_the_wrap_changed_no_data():
    """Every wrapped entry equals the tuple it was authored as -- the
    whole claim of P1 (a rename, not a behaviour change)."""
    assert set(shop._AUTHORED) == set(shop.CATALOG)
    for key, raw in shop._AUTHORED.items():
        assert tuple(shop.CATALOG[key]) == tuple(raw), key


def test_index_access_still_works():
    """Back-compat: still a tuple.  Anything downstream (or a save-era
    caller) that indexes positionally must keep working."""
    for key, v in shop.CATALOG.items():
        assert v[0] == v.name and v[1] == v.icon and v[2] == v.price, key
        assert v[3] == v.category and v[4] == v.effect and v[5] == v.flavor


def test_six_field_unpack_still_works():
    """The one unpacking site (plan audit A4) -- pinned so P2's widening
    fails HERE, loudly, instead of at import time in the app."""
    for key, v in shop.CATALOG.items():
        name, icon, price, cat, eff, flavor = v
        assert name and icon and cat, key


def test_no_positional_catalog_reads_remain_in_shop():
    """The point of P1: shop.py reads by NAME now.  A new `v[3]` sneaking
    back in is the drift this phase exists to stop."""
    import inspect
    import re
    src = inspect.getsource(shop)
    # strip the docstrings/comments that legitimately quote the old form
    body = "\n".join(ln for ln in src.splitlines()
                     if not ln.lstrip().startswith("#"))
    body = re.sub(r'""".*?"""', "", body, flags=re.S)
    assert not re.search(r"\bv\[\d\]", body), "positional catalog read is back"


def test_derived_views_agree_with_the_record():
    for key, v in shop.CATALOG.items():
        assert shop.EFFECTS[key] == v.effect, key
        assert shop.ICON_KEYS[key] == v.icon, key
        assert shop.FLAVORS[key] == v.flavor, key
    assert shop.FOOD_KEYS == frozenset(
        k for k, v in shop.CATALOG.items() if v.category == "Food")


@pytest.mark.parametrize("key", sorted(shop.CATALOG))
def test_every_icon_resolves_back_to_its_key(key):
    """key_for_icon is the loot->bag bridge; the wrap must not have
    disturbed the icon index."""
    icon = shop.CATALOG[key].icon
    assert shop.key_for_icon(icon) is not None, key
