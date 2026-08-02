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
    assert road == {"town_transport", "disaster_transport", "life_recovery",
                    # the expansion (2026-07-26): the safe lift + the camp
                    "zone_transport", "continent_transport"}
    for key, v in shop.CATALOG.items():
        assert v.where in ("home", "road"), key


def test_road_items_touch_nothing_from_the_home_bag():
    """They only refuse there; their real work is adventure-run state,
    which is deliberately not in this namespace."""
    for key, v in shop.CATALOG.items():
        if v.where == "road":
            assert v.touches == (), key


# items whose whole effect is a GRANT (the bag moves, not a meter) or a
# pure SHOW (the balloon: the one authored toy with no live column at all)
# -- the expansion 2026-07-26.  touches lists METERS by contract, so these
# legitimately declare none; anything else with an empty tuple is broken.
_GRANT_OR_SHOW = frozenset({"balloon",
                            "capsule_a", "capsule_b", "capsule_c",
                            "capsule_d", "capsule_e", "capsule_f",
                            "capsule_g", "capsule_h",
                            "prank_capsule_a", "prank_capsule_b"})


def test_every_home_item_does_something():
    """A home item that moves no live stat is either broken or has an
    undeclared effect.  Both are worth failing over.  (The capsule family
    GRANTS -- its effect is the bag; the balloon is the one pure show.)"""
    for key, v in shop.CATALOG.items():
        if v.where == "home" and key not in _GRANT_OR_SHOW:
            assert v.touches, f"{key} declares no effect at all"


def test_tier_is_populated_by_derivation_not_by_hand():
    """P2 left this hook empty on purpose; the distribution arc filled it
    2026-07-24 by DERIVING each band -- so no economy was invented on the way
    in.  ⭐The SOURCE changed 2026-08-02 (Joel: "yeah decouple rarity from
    price"): the band now reads the authored SUPPLY columns
    (DefaultStockChance x DefaultMaxStock) instead of the price.  Still
    derived, still nothing invented -- just the other column."""
    for key, v in shop.CATALOG.items():
        assert v.tier == shop.tier_for_supply(v.icon, v.price), key


@pytest.mark.parametrize("key", sorted(shop.CATALOG))
def test_touches_has_no_duplicates(key):
    t = shop.CATALOG[key].touches
    assert len(t) == len(set(t)), key


def test_the_free_cure_buttons_are_never_paywalled():
    """SUPERSEDED IN PART (item expansion 2026-07-26, Joel: "bring them
    all in... your call"): catalog cures exist again, but the ORIGINAL
    LAW's spirit holds -- basic care is never paywalled.  Every catalog
    entry that moves an ailment flag must be one of: grant-only (the
    field Med), pocket change (the 10b Bandage), or a premium COMBO that
    does strictly more than the free button (Elixir, Vitamin G).  And the
    free buttons themselves must still exist (pill on F, heal on H)."""
    # (the 10b bandage lasted an hour -- cut 2026-07-26, "its supposed
    # to just be used for the animations for heal")
    allowed = {"med": None, "elixir": 2000, "vitamin_g": 2000}
    for key, v in shop.CATALOG.items():
        if "sick" in v.touches or "injured" in v.touches:
            assert key in allowed, f"{key} sells a cure outside the ruling"
            assert v.price == allowed[key], key
    from tuipet.app import TuiPetApp
    assert any(k == "h" and a == "heal" for k, a, _l in TuiPetApp.BINDINGS)
    from tuipet.feedscreen import ROWS_MENU
    assert any(k == "pill" for k, _label in ROWS_MENU)
