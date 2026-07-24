"""WHAT EACH ITEM MOVES — items refactor P2 (2026-07-23).

Joel: "we gotta redo them all to fit everything we got going on."

`Item.touches` is the machine-readable answer to "what does this item
actually do", read out of petcare's handlers rather than out of the
effect PROSE (which is exactly the thing that drifts -- plan §1g).

These pins are the teeth of that:

  * every touched name is a REAL Pet field (catches typos and renames),
  * no item aims at a DORMANT stat -- the strip left ~11 fields with
    zero read/write sites, and an item whose whole point is one of them
    is an item that does nothing,
  * road items stay honestly empty, since from the home bag they only
    refuse.

The DORMANT list below is the plan's live-stat ledger (§1d), measured by
counting real read/write sites outside pet.py and the persistence layer.
If a system is ever REVIVED, delete it from this list -- do not delete
the assertion.
"""
import dataclasses

import pytest

from tuipet import shop
from tuipet.pet import Pet

_PET_FIELDS = {f.name for f in dataclasses.fields(Pet)}

# Zero read/write sites anywhere in the app (plan §1d).  An item pointed
# at one of these is a dead item.
DORMANT_STATS = frozenset({
    "depressed", "nutr_protein", "nutr_mineral", "nutr_vitamin",
    "fatigue_length", "bandage_lapse", "compliance", "food_eaten",
    "mood_rank", "praise_flag", "scold_flag",
})

# Meters whose SETTERS are verified no-ops (pet._set_mood /
# _set_enthusiasm).  Writing them is legal but accomplishes nothing, so
# no item may claim one as an effect.
NO_OP_METERS = frozenset({"mood", "enthusiasm"})


def test_every_catalog_entry_declares_touches():
    for key, v in shop.CATALOG.items():
        assert isinstance(v.touches, tuple), key


def test_every_touched_name_is_a_real_pet_field():
    """Catches a typo, and catches a field rename that silently orphans
    an entry here."""
    for key, v in shop.CATALOG.items():
        for stat in v.touches:
            assert stat in _PET_FIELDS, f"{key} touches unknown field {stat!r}"


def test_no_item_touches_a_dormant_stat():
    """§2 goal 2, mechanically enforced."""
    for key, v in shop.CATALOG.items():
        bad = set(v.touches) & DORMANT_STATS
        assert not bad, f"{key} aims at dormant {sorted(bad)}"


def test_no_item_claims_a_no_op_meter():
    for key, v in shop.CATALOG.items():
        bad = set(v.touches) & NO_OP_METERS
        assert not bad, f"{key} claims no-op meter {sorted(bad)}"


def test_only_road_items_are_road_scoped():
    road = {k for k, v in shop.CATALOG.items() if v.where == "road"}
    assert road == {"town_transport", "disaster_transport", "life_recovery"}
    for key, v in shop.CATALOG.items():
        assert v.where in ("home", "road"), key


def test_road_items_touch_nothing_from_the_home_bag():
    """They only refuse there; their real work is adventure-run state,
    which is deliberately not in this namespace."""
    for key, v in shop.CATALOG.items():
        if v.where == "road":
            assert v.touches == (), key


def test_every_home_item_does_something():
    """A home item that moves no live stat is either broken or has an
    undeclared effect.  Both are worth failing over."""
    for key, v in shop.CATALOG.items():
        if v.where == "home":
            assert v.touches, f"{key} declares no effect at all"


def test_tier_is_declared_but_unpopulated():
    """P2 leaves the distribution hook EMPTY on purpose -- populating it
    would be inventing an economy nobody has ruled on (plan §7)."""
    assert all(v.tier is None for v in shop.CATALOG.values())


@pytest.mark.parametrize("key", sorted(shop.CATALOG))
def test_touches_has_no_duplicates(key):
    t = shop.CATALOG[key].touches
    assert len(t) == len(set(t)), key


def test_no_shelf_item_sells_an_ailment_cure():
    """R3 landed: sick and injured are BOTH cured free from the care
    menu, so no catalog entry may move either flag.  If one ever does,
    the symmetry has quietly broken."""
    for key, v in shop.CATALOG.items():
        assert "sick" not in v.touches, key
        assert "injured" not in v.touches, key
