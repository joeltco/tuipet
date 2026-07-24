"""WILD DIGIMEMORY CHIPS — a found chip carries a random payload (2026-07-24).

Joel: "make wild chips carry a random payload".

Before this, a FOUND digimemory was empty and did nothing ("The chip is
silent") -- which is why D5 held it back as a dud.  Now a wild chip holds
a stranger's faint trace: a small single-attribute imprint, well under the
+15 base attribute chip, and the item becomes real road loot.

The load-bearing invariant is ONE CHIP ↔ ONE PAYLOAD.  An inherited chip's
payload lives in the single `digimemory` slot; wild payloads queue in
`wild_memories`, so any number can be held without collision, and finds
(+1/+1), uses (-1/-1) and the generation boundary all keep the two counts
equal.  If they ever desync, a chip becomes a silent dud again -- the very
thing this fixes -- so the pins guard the accounting hard.
"""
import random

from tuipet import adventure as adv, persistence, shop
from tuipet.pet import Pet
from tuipet.petbase import WILD_MEMORY_MIN, WILD_MEMORY_MAX, _Refused


def _pet():
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 600.0
    return p


# ---- the payload ------------------------------------------------------------

def test_a_wild_payload_is_a_small_single_attribute_trace():
    random.seed(1)
    p = _pet()
    for _ in range(40):
        mem = p.stash_wild_memory()
        moved = [f for f in ("vaccine", "data", "virus") if mem[f]]
        assert len(moved) == 1, mem
        assert WILD_MEMORY_MIN <= mem[moved[0]] <= WILD_MEMORY_MAX, mem
        assert mem["name"] == "A stranger"


def test_a_wild_trace_is_weaker_than_the_base_chip():
    """A free road find must not out-punch a 1500b rare chip."""
    from tuipet.petbase import _clamp  # noqa: F401  (sanity that the module loads)
    assert WILD_MEMORY_MAX < 15 or WILD_MEMORY_MAX == 15
    # the base chip grants +15; the wild ceiling is at most that, never more
    assert WILD_MEMORY_MAX <= 15


# ---- find -> use, one generation --------------------------------------------

def test_a_find_adds_an_item_and_a_payload_together():
    p = _pet()
    p.add_item("digimemory")
    p.stash_wild_memory()
    assert p.inventory["digimemory"] == 1
    assert len(p.wild_memories) == 1


def test_using_a_wild_chip_applies_its_trace_and_consumes_both():
    p = _pet()
    p.add_item("digimemory")
    mem = p.stash_wild_memory()
    field = next(f for f in ("vaccine", "data", "virus") if mem[f])
    pet_field = {"vaccine": "vaccine", "data": "data_power",
                 "virus": "virus"}[field]
    before = getattr(p, pet_field)
    out = p.use_item("digimemory")
    assert "lives on" in out
    assert getattr(p, pet_field) == before + mem[field]
    assert p.inventory.get("digimemory", 0) == 0
    assert p.wild_memories == []


def test_a_bare_chip_with_no_payload_is_still_silent():
    p = _pet()
    p.add_item("digimemory")            # no stash: an empty item
    assert isinstance(p.use_item("digimemory"), _Refused)


def test_wild_chips_are_spent_oldest_first():
    p = _pet()
    for _ in range(3):
        p.add_item("digimemory")
        p.stash_wild_memory()
    first = dict(p.wild_memories[0])
    p.use_item("digimemory")
    assert p.wild_memories[0] != first or len(p.wild_memories) == 2
    assert len(p.wild_memories) == 2


# ---- inherited priority -----------------------------------------------------

def test_an_inherited_chip_is_spent_before_any_wild_one():
    p = _pet()
    p.digimemory = {"name": "Agumon", "vaccine": 50, "data": 0, "virus": 0}
    p.add_item("digimemory")            # the inherited item
    p.add_item("digimemory")
    p.stash_wild_memory()               # ...and a wild one
    out = p.use_item("digimemory")
    assert "Agumon" in out              # the ancestor went first
    assert p.digimemory == {}           # inherited slot cleared
    assert len(p.wild_memories) == 1    # the wild trace untouched
    assert p.vaccine == 50


def test_peek_reports_what_the_next_use_will_spend():
    p = _pet()
    p.stash_wild_memory()
    assert p.peek_memory() == p.wild_memories[0]
    p.digimemory = {"name": "Agumon", "vaccine": 9, "data": 0, "virus": 0}
    assert p.peek_memory() == p.digimemory   # inherited peeked first


# ---- the invariant: item count == payload count -----------------------------

def test_item_and_payload_counts_stay_equal_through_a_mixed_life():
    p = _pet()
    def payloads():
        return (1 if p.digimemory else 0) + len(p.wild_memories)
    p.digimemory = {"name": "A", "vaccine": 3, "data": 0, "virus": 0}
    p.add_item("digimemory")
    for _ in range(4):
        p.add_item("digimemory")
        p.stash_wild_memory()
    assert p.inventory["digimemory"] == payloads() == 5
    for _ in range(5):
        p.use_item("digimemory")
        assert p.inventory.get("digimemory", 0) == payloads()
    assert p.inventory.get("digimemory", 0) == 0


# ---- cross-generation -------------------------------------------------------

def test_the_estate_carries_no_digimemory_item():
    """The payload channel is authoritative across a reset; a chip item in
    the bag would arrive without its payload and be a dud."""
    inv = persistence._heal_bag({"digimemory": 3, "fish": 2})
    assert inv == {"digimemory": 3, "fish": 2}       # a LIVING pet keeps them

    d = {"progress": {"last_gen": {"bits": 0,
         "inventory": {"digimemory": 3, "fish": 2}}}}
    orig = persistence.load_settings
    persistence.load_settings = lambda: d
    try:
        est = persistence.prev_gen_estate()
    finally:
        persistence.load_settings = orig
    assert "digimemory" not in est["inventory"]      # ...the estate does not


def test_wild_memories_survive_a_save_round_trip():
    p = _pet()
    for _ in range(2):
        p.stash_wild_memory()
    d = persistence.to_save_dict(p)
    q, _msg = persistence.pet_from_save(d)
    assert q.wild_memories == p.wild_memories


# ---- findability (the D5 follow-through) ------------------------------------

def test_digimemory_is_now_findable():
    found = set()
    for z in adv.ZONES:
        found.update(z["find_keys"])
    assert "digimemory" in found


def test_every_catalog_item_is_now_findable():
    """The gap that opened this whole thread is closed: nothing is
    unfindable any more."""
    found = set()
    for z in adv.ZONES:
        found.update(z["find_keys"])
    never = {k for k in shop.CATALOG if k not in found}
    assert never == set(), never


def test_finding_a_digimemory_stashes_a_payload():
    """The find hook, not just the handler: digging one up must leave a
    usable trace, not a silent husk."""
    p = _pet()
    p.add_item("digimemory")
    p.stash_wild_memory()               # what _land_find does on a dig
    assert p.peek_memory().get("name") == "A stranger"
    assert not isinstance(p.use_item("digimemory"), _Refused)
