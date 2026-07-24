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


AUTHORED_FIELDS = ("name", "icon", "price", "category", "effect", "flavor")


def test_field_order_matches_the_authored_table():
    """Later phases APPEND fields; they must never REORDER them.  The
    authored literal is positional, so the first six ARE the contract.
    (P2 appended touches/where/tier -- this pin is what makes that an
    append rather than a reshuffle.)"""
    assert shop.Item._fields[:6] == AUTHORED_FIELDS
    for extra in shop.Item._fields[6:]:
        assert extra in shop.Item._field_defaults, \
            f"appended field {extra!r} must have a default"


def test_the_wrap_changed_no_data():
    """Every wrapped entry still carries, in its first six slots, exactly
    the tuple it was authored as -- the standing claim that the record
    work is a rename and not a behaviour change."""
    assert set(shop._AUTHORED) == set(shop.CATALOG)
    for key, raw in shop._AUTHORED.items():
        assert tuple(shop.CATALOG[key])[:6] == tuple(raw), key
        assert len(raw) == 6, f"{key}: the authored table stays 6 wide"


def test_index_access_still_works():
    """Back-compat: still a tuple.  Anything downstream (or a save-era
    caller) that indexes positionally must keep working."""
    for key, v in shop.CATALOG.items():
        assert v[0] == v.name and v[1] == v.icon and v[2] == v.price, key
        assert v[3] == v.category and v[4] == v.effect and v[5] == v.flavor


def test_no_whole_record_unpacking_survives_anywhere():
    """Plan audit A4, now enforced -- and enforced for BOTH spellings.

    P1 converted the for-loop unpack at shelf_rows and I declared the job
    done.  It was not: `entry()` held a second one as a plain assignment
    (`name, _icon, price, cat, _eff, _fl = c`), which the first grep's
    for-loop pattern never saw.  P2's widening took out 58 tests through
    that line.  So this pin now looks for a SIX-TARGET unpack in any
    form, which is the shape that breaks whenever the record grows."""
    import inspect
    import re
    src = inspect.getsource(shop)
    six_targets = r"[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*){5}\s*(?==[^=]|\)? in )"
    for line in src.splitlines():
        body = line.split("#")[0]
        if "CATALOG" in body or " = c" in body or "in CATALOG" in body:
            assert not re.search(six_targets, body), \
                f"whole-record unpacking is back: {line.strip()!r}"


def test_widening_the_record_cannot_break_a_reader():
    """The real regression test for the 58-failure break: construct a
    record with MORE fields than today and prove the module's own
    accessors still resolve.  If a reader ever depends on the arity
    again, this fails without needing the whole suite to notice."""
    wider = shop.Item(*(tuple(shop.CATALOG["fish"])[:6]))._replace(
        touches=("hunger", "energy"))
    assert wider.name == "Fish" and wider.category == "Food"
    assert shop.entry("fish")["name"] == "Fish"
    assert shop.entry("fish")["category"] == "Food"


def test_the_record_can_grow_without_breaking_readers():
    """The widened record must still answer every authored field by
    name -- that is what lets later phases append freely."""
    for key, v in shop.CATALOG.items():
        for i, field in enumerate(AUTHORED_FIELDS):
            assert getattr(v, field) == v[i], key


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
