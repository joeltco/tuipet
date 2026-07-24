"""DISTRIBUTION — tiered rarity + exclusives (2026-07-24).

Joel: "d1 stock and find, d3 both, d4 give them distinct loot".

D1  tier drives STOCK (a town's daily ceiling) and FIND (the road roll's
    weighting).  Not price -- 20 of 40 prices are canon DefaultPrice and
    re-pricing would overwrite numbers P5/P6 deliberately took.
D3  exclusives on BOTH sides: towns already deal 26 unique guest goods,
    and zones now carry 26 unique signature finds.
D4  the eight factorynight zones get distinct loot -- solved BY the zone
    signatures rather than by a second mechanism.

The tier itself is DERIVED FROM PRICE, never authored.  That is the whole
reason this arc invents no economy: price was already the game's opinion
of an item's worth, and the bands are just a reading of it.
"""
import collections

from tuipet import adventure as adv, shop


# ---- the tier ladder --------------------------------------------------------

def test_tier_is_derived_from_price_not_authored():
    for key, v in shop.CATALOG.items():
        assert v.tier == shop.tier_for_price(v.price), key


def test_the_bands_are_ordered_and_total_the_catalog():
    counts = collections.Counter(v.tier for v in shop.CATALOG.values())
    assert sum(counts.values()) == len(shop.CATALOG)
    for name in shop.TIER_ORDER:
        assert counts[name] > 0, name
    # a dearer item is never a commoner tier than a cheaper one
    priced = sorted((v.price, v.tier) for v in shop.CATALOG.values() if v.price)
    rank = {t: i for i, t in enumerate(shop.TIER_ORDER)}
    for (_p1, t1), (_p2, t2) in zip(priced, priced[1:]):
        assert rank[t1] <= rank[t2]


def test_grant_only_goods_have_no_band():
    for key, v in shop.CATALOG.items():
        if v.price is None:
            assert v.tier is None, key


def test_rarer_always_means_rarer_on_both_levers():
    """One curve for both, so "rare" means one thing in this game."""
    last_w, last_s = None, None
    for name in shop.TIER_ORDER:
        w, s = shop.TIER_WEIGHT[name], shop.TIER_STOCK[name]
        if last_w is not None:
            assert w <= last_w and s <= last_s, name
        last_w, last_s = w, s


# ---- D1: the FIND lever -----------------------------------------------------

def test_the_find_roll_is_weighted_not_flat():
    import inspect
    src = inspect.getsource(adv.Adventure._roll_find)
    assert "random.choices" in src and "tier_weight" in src
    assert "random.choice(pool)" not in src


def test_a_legendary_is_rarer_on_the_road_than_a_common():
    assert shop.tier_weight("miracle_drink") < shop.tier_weight("fish")


# ---- D1: the STOCK lever ----------------------------------------------------

def test_tier_caps_a_generous_town_shelf():
    """It may only ever RESTRICT -- an authored max_stock of 1 stays 1."""
    rows = shop.town_stock(0, pet=None)
    for e in rows:
        assert e["left"] <= shop.tier_stock(e["key"]), e["key"]


def test_stock_never_exceeds_the_tier_ceiling_in_any_town():
    for town in range(26):
        for e in shop.town_stock(town, pet=None):
            assert e["left"] <= shop.tier_stock(e["key"]), (town, e["key"])


# ---- D3: exclusives, both sides ---------------------------------------------

def test_every_town_has_a_unique_guest_good():
    deal = shop._guest_deal()
    assert len(deal) == 26
    assert len(set(deal.values())) == 26, "two towns share a signature good"


def test_every_zone_has_a_unique_signature_find():
    sig = adv.ZONE_SIGNATURE
    assert len(sig) == len(adv.ZONES) == 26
    assert len(set(sig.values())) == 26, "two zones share a signature"


def test_a_signature_actually_rides_its_zones_pool():
    for zi, key in adv.ZONE_SIGNATURE.items():
        assert key in adv.ZONES[zi]["find_keys"], (zi, key)


def test_a_signature_is_exclusive_to_its_zone():
    """The point of the word: no other zone digs it."""
    owner = {k: zi for zi, k in adv.ZONE_SIGNATURE.items()}
    for zi, z in enumerate(adv.ZONES):
        for key in z["find_keys"]:
            if key in owner and owner[key] != zi:
                raise AssertionError(
                    f"{key} is {owner[key]}'s signature but zone {zi} digs it")


def test_signatures_deepen_with_the_run():
    """An opening stop signs a common good; the last stops sign legendary
    ones.  Depth must never run backwards."""
    rank = {t: i for i, t in enumerate(shop.TIER_ORDER)}
    seen = [rank[shop.CATALOG[adv.ZONE_SIGNATURE[zi]].tier]
            for zi in adv.PROGRESSION if zi in adv.ZONE_SIGNATURE]
    assert seen == sorted(seen), "signature tiers zig-zag with depth"


def test_grant_only_goods_are_never_a_signature():
    """The birthday treats and the Digimemory are deliberately unbuyable
    gifts; road loot would quietly undo that."""
    for key in adv.ZONE_SIGNATURE.values():
        assert shop.CATALOG[key].price is not None, key
    assert "digimemory" not in adv.ZONE_SIGNATURE.values()


def test_the_road_trio_is_never_a_signature():
    """They ride EVERY pool already -- exclusive is meaningless for them."""
    for key in adv._ROAD_KEYS:
        assert key not in adv.ZONE_SIGNATURE.values(), key


def test_signatures_are_permanent_across_reruns():
    """The guest-good law: a place's character must not reshuffle."""
    again = adv._assign_signatures()
    assert again == adv.ZONE_SIGNATURE


# ---- D4: the eight factorynight zones ---------------------------------------

def test_the_shared_scene_zones_no_longer_dig_alike():
    fn = [zi for zi, z in enumerate(adv.ZONES) if z["scene"] == "factorynight"]
    assert len(fn) == 8, "the scene split changed; re-check this ruling"
    pools = [tuple(sorted(adv.ZONES[zi]["find_keys"])) for zi in fn]
    assert len(set(pools)) == 8, "two factorynight zones still dig identically"


def test_no_two_zones_anywhere_have_identical_loot():
    pools = [tuple(sorted(z["find_keys"])) for z in adv.ZONES]
    assert len(set(pools)) == len(adv.ZONES)


# ---- coverage ---------------------------------------------------------------

def test_the_signature_pass_closed_the_never_found_gap():
    """Before this arc 16 of 44 items could never be found.  What stays
    unfindable must be unfindable BY DESIGN."""
    found = set()
    for z in adv.ZONES:
        found.update(z["find_keys"])
    never = {k for k in shop.CATALOG if k not in found}
    # D5 (2026-07-24): cookie + cupcake made findable alongside candy.
    # digimemory is the ONE deliberate hold-out -- a wild chip has no
    # payload, so a found one does nothing; inheritance-only BY DESIGN.
    assert never == {"digimemory"}, never


def test_the_grant_only_treats_are_findable_like_candy():
    """D5: cookie and cupcake join the road the way candy always has --
    grant-only (unbuyable) but discoverable in the gentle biomes."""
    found = set()
    for z in adv.ZONES:
        found.update(z["find_keys"])
    for k in ("candy", "cookie", "cupcake"):
        assert shop.CATALOG[k].price is None, k    # still unbuyable
        assert k in found, k                       # ...but findable


def test_a_wild_digimemory_stays_unfindable_because_it_would_be_a_dud():
    """The reason digimemory is the one hold-out: a FOUND chip carries no
    ancestor payload, so using it does nothing.  A dud in the loot pool is
    what the no-traps rule forbids -- so it stays inheritance-only."""
    from tuipet.pet import Pet
    from tuipet.petbase import _Refused
    found = set()
    for z in adv.ZONES:
        found.update(z["find_keys"])
    assert "digimemory" not in found
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 600.0
    p.add_item("digimemory")                       # a wild one: empty
    assert isinstance(p.use_item("digimemory"), _Refused)


# ---- D6: P6's town placement, RATIFIED 2026-07-24 ---------------------------

def test_the_chips_town_placement_is_ratified_not_accidental():
    """D6 (Joel: "ratify it").  Adding the seven chips in P6 un-dropped ten
    canon shopConsumable overrides, so the attribute chips now stock on
    many town shelves.  That was a SIDE EFFECT at first; Joel ratified it,
    so it is now a decision on the record -- and the exact spread is
    DVPet's own (shopConsumable.csv), not hand-placed by us.

    Pinned so that if a future override edit silently drops these again,
    this fails and the ratified placement is defended rather than lost.
    """
    import collections
    town = collections.Counter()
    for t in range(26):
        for _sid, k, _o, _p in shop._town_rows(t):
            town[k] += 1
    # the base chips reach most towns; the golden/omni tier fewer, exactly
    # as the canon override table deals them
    assert town["vaccine_chip"] >= 12, town["vaccine_chip"]
    assert town["virus_chip"] >= 12, town["virus_chip"]
    assert town["data_chip"] >= 12, town["data_chip"]
    assert town["omni_chip_g"] >= 8, town["omni_chip_g"]
    # ...and rarity still bites: a rare chip is one-per-town-per-day
    for t in range(26):
        for e in shop.town_stock(t, pet=None):
            if e["key"].endswith("chip") or e["key"].endswith("chip_g"):
                assert e["left"] <= shop.tier_stock(e["key"]) <= 2, (t, e["key"])


# ---- D7: the still-dropped town overrides STAY dropped (2026-07-24) ----------

def test_the_ten_dropped_overrides_stay_dropped():
    """D7 (Joel: "leave them dropped").  shopConsumable.csv authors 22 town
    overrides; 10 point at icons with no catalog entry and are silently
    skipped at load.  Ruled: leave them so -- adding them would mean either
    inventing items (no economy is being invented) or, for two of them,
    selling an ailment cure that R3 forbids.

    Pinned as a DECISION, not an accident: if a later item pass gives one
    of these icons a catalog key, this fails and forces the choice back
    into the open instead of silently un-dropping a town good.
    """
    import csv
    dropped = []
    with open("src/tuipet/data/shopConsumable.csv") as fh:
        for r in csv.DictReader(fh):
            isfood = str(r.get("IsFood", "")).strip().lower() in ("true", "1")
            cid = r.get("ConsumableID")
            if cid is None:
                continue
            icon = ("f:" if isfood else "i:") + str(int(cid))
            if shop.key_for_icon(icon) is None:
                dropped.append(icon)
    assert set(dropped) == {"i:28", "i:31", "f:26", "f:27", "f:40",
                            "f:39", "f:31", "f:56", "i:81", "i:82"}


def test_the_forbidden_cures_are_the_reason_two_must_stay_dropped():
    """f:15 Elixir (cures sickness) and f:16 Vitamin G (cures injury) are
    NOT among the dropped overrides -- but the CSV's own cure items must
    never gain a sellable catalog key, because R3 made both cures free.
    This is the load-bearing half of D7."""
    assert shop.key_for_icon("f:15") is None      # Elixir
    assert shop.key_for_icon("f:16") is None      # Vitamin G
    for key, v in shop.CATALOG.items():
        assert "sick" not in v.touches and "injured" not in v.touches, key
