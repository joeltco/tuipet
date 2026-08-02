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

def test_tier_is_derived_from_authored_supply_not_from_price():
    """⭐SUPERSEDED 2026-08-02 (Joel: "yeah decouple rarity from price").
    Rarity used to BE price, which made "legendary" mean "expensive" -- and
    the economy audit measured expensive at ~23 real minutes of adventuring,
    so rarity was decorative.  It reads the authored SUPPLY columns now:
    DefaultStockChance x DefaultMaxStock = expected copies on a shelf."""
    for key, v in shop.CATALOG.items():
        assert v.tier == shop.tier_for_supply(v.icon, v.price), key
    # ...and it is genuinely decoupled: a dearer good is now freely allowed to
    # be commoner than a cheap one, which is the whole point
    by_tier = {t: [v.price for v in shop.CATALOG.values()
                   if v.tier == t and v.price] for t in shop.TIER_ORDER}
    assert min(by_tier["legendary"]) < max(by_tier["common"]), \
        "price still predicts the band -- nothing was decoupled"


def test_the_bands_are_ordered_and_total_the_catalog():
    counts = collections.Counter(v.tier for v in shop.CATALOG.values())
    assert sum(counts.values()) == len(shop.CATALOG)
    for name in shop.TIER_ORDER:
        assert counts[name] > 0, name
    # (the old "a dearer item is never a commoner tier" leg RETIRED 2026-08-02:
    #  it was the price coupling itself, stated as a law.  What replaces it is
    #  the supply monotonicity -- a scarcer good is never a commoner band.)
    rank = {t: i for i, t in enumerate(shop.TIER_ORDER)}
    supplied = sorted((shop.supply_score(v.icon), v.tier)
                      for v in shop.CATALOG.values()
                      if v.price and shop.supply_score(v.icon) is not None)
    for (_s1, t1), (_s2, t2) in zip(supplied, supplied[1:]):
        assert rank[t1] >= rank[t2], "a scarcer good landed in a commoner band"


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


def test_towns_are_curated_but_home_sells_everything():
    """SUPERSEDED IN PART (item expansion 2026-07-26): with ~120 sellable
    goods, full town coverage stopped being possible (26 guest slots) --
    towns are CURATED now and the guarantee moves up a level: the HOME
    shelf lists every priced good (nothing is unbuyable), every town's
    guest good is still unique game-wide, and the coverage-first draw
    still hands guest slots to goods no base sells before doubling up."""
    home = {e["key"] for e in shop.catalog()}
    for k, v in shop.CATALOG.items():
        if v.price is not None and v.category != "Road":
            assert k in home, f"{k} is priced but unbuyable at home"
    guests = shop._guest_deal()
    assert len(set(guests.values())) == len(guests)   # unique game-wide
    base_anywhere = set()
    for tid in shop._town_maps():
        base_anywhere.update(k for _sid, k, _o, _p in shop._base_rows(tid))
    # coverage-first: while un-based goods outnumber slots, no slot may be
    # wasted on a good some base already sells
    unbased_guests = sum(1 for g in guests.values() if g not in base_anywhere)
    assert unbased_guests == len(guests), "a guest slot doubled up while goods are dark"


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

def test_every_item_is_obtainable_through_some_channel():
    """SUPERSEDED SHAPE (item expansion 2026-07-26): the road stopped
    being the only earn channel, so "findable" became "obtainable" --
    every catalog key must be reachable through at least one of: the home
    shelf, a road find, the gift/capsule roller, the prank drawer, an
    authored battle drop, an authored cup prize, or the Human->Beast
    spirit chain.  A key no channel reaches is stranded and fails."""
    from tuipet import data as _data, tournament as _t
    from tuipet.pet import Pet
    obtainable = {k for k, v in shop.CATALOG.items() if v.price is not None}
    for z in adv.ZONES:
        obtainable.update(z["find_keys"])
    cap = shop.TIER_ORDER.index("rare")                  # festival gifts
    obtainable.update(k for k, v in shop.CATALOG.items()
                      if k not in Pet._GIFT_BANNED and v.where == "home"
                      and shop.TIER_ORDER.index(v.tier or "common") <= cap)
    obtainable.update(Pet._PRANK_POOL)
    obtainable.update(adv._FESTIVAL_CAPSULES)
    for table in _data.load_loot_tables().values():      # authored drops
        for icon, _rate in table:
            k = shop.key_for_icon(icon)
            if k:
                obtainable.add(k)
    for t in _data.load_tournies():                      # authored cup prizes
        if t["item"] >= 0:
            obtainable.add(_t._prize_key("i", t["item"]))
        if t["food_id"] >= 0 and t["food_amt"] > 0:
            obtainable.add(_t._prize_key("f", t["food_id"]))
    obtainable.update([k.replace("human_", "beast_", 1)  # the spirit chain
                       for k in sorted(obtainable) if k.startswith("human_")])
    stranded = {k for k in shop.CATALOG if k not in obtainable}
    assert stranded == set(), f"no channel reaches: {sorted(stranded)}"


def test_the_grant_only_treats_are_findable_like_candy():
    """D5: cookie and cupcake join the road the way candy always has --
    grant-only (unbuyable) but discoverable in the gentle biomes."""
    found = set()
    for z in adv.ZONES:
        found.update(z["find_keys"])
    for k in ("candy", "cookie", "cupcake"):
        assert shop.CATALOG[k].price is None, k    # still unbuyable
        assert k in found, k                       # ...but findable


def test_a_found_digimemory_is_no_longer_a_dud():
    """This pin used to assert digimemory STAYED unfindable because a wild
    chip did nothing.  Joel then ruled "make wild chips carry a random
    payload" -- so a found chip now holds a stranger's trace and is real
    loot.  Full lifecycle lives in test_wild_memory.py; this guards the
    reversal so the old dud behaviour can't creep back."""
    found = set()
    for z in adv.ZONES:
        found.update(z["find_keys"])
    assert "digimemory" in found


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

def test_every_authored_town_override_is_live():
    """SUPERSEDED (item expansion 2026-07-26, Joel: "bring in all 99"):
    D7's ten dropped overrides all resolve now -- every one of the 22
    authored shopConsumable.csv town rows names a real catalog key, so
    the authored town economy is finally whole.  A row going dark again
    means a catalog key was lost -- fail loudly."""
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
    # (the Bandage's cut costs nothing here: shopConsumable.csv never
    # authored an i:80 row -- no town ever sold the wrap)
    assert dropped == [], f"authored town rows went dark: {dropped}"


def test_the_free_buttons_own_the_cures_outright():
    """⭐SUPERSEDED AGAIN by the ITEM REFACTOR (2026-08-02, "MAKING ALL ITEMS
    BALANCED").  The premium "combos" bundled a free button with a cheap item
    and charged for the pair -- the Elixir cured sickness (the free F pill) and
    filled the tank (the 200b drink); Vitamin G healed injury (the free H).
    Both were repointed to capabilities the free buttons cannot copy, so the
    shelf's only remaining CURE is the 100b Med, and the free buttons own the
    ailments outright."""
    assert shop.key_for_icon("f:15") == "elixir"
    assert shop.key_for_icon("f:16") == "vitamin_g"
    curers = {k for k, v in shop.CATALOG.items()
              if "sick" in v.touches or "injured" in v.touches}
    assert curers == {"med"}, f"a cure crept back onto the shelf: {curers}"


def test_the_home_counter_rotates_but_never_starves():
    """THE DAILY SHELF (refactor 2026-07-27, Joel: "daily items. not all at
    once like the home shop. basic items sure").  home_stock is a DAY'S
    shelf now, not the whole catalog: staples always, the band rotating,
    and the two DOOR shelves (crests, road gear) riding their own gates.
    The rotation must never starve a key -- the band is a shuffled CYCLE,
    so one epoch deals every non-staple sellable exactly once."""
    import datetime
    from tuipet import shop
    D = datetime.date(2026, 8, 3)
    rows = {e["key"] for e in shop.home_stock(today=D)}
    assert shop.HOME_STAPLES <= rows, "a staple left the shelf"
    assert len(rows) < 40, "the wall is back -- rotation is not filtering"
    # one aligned epoch covers the whole band pool
    pool = {k for k, v in sorted(shop.CATALOG.items())
            if v.price is not None and k not in shop.HOME_STAPLES
            and v.category != "Road"}
    days = -(-len(pool) // shop.HOME_BAND_SIZE)
    base = shop._today_ordinal(D)
    start = D + datetime.timedelta(days=(days - base % days) % days)
    seen = set()
    for i in range(days):
        seen.update(shop.home_band(start + datetime.timedelta(days=i)))
    assert seen == pool, f"the cycle starved {sorted(pool - seen)[:5]}"
    # ...and the same day deals the same band on every device
    assert shop.home_band(D) == shop.home_band(D)


def test_every_retired_key_has_a_living_heir():
    """THE RETIRED LEDGER (refactor 2026-07-27): each cut key names an heir
    in the catalog, owned copies convert in the bag heal, and every icon a
    cut key wore still resolves -- no authored channel goes dark."""
    from tuipet import persistence, shop
    for old, heir in shop.RETIRED.items():
        assert old not in shop.CATALOG, f"{old} is both retired and live"
        assert heir in shop.CATALOG, f"{old}'s heir {heir} is not in the catalog"
    for icon, old in shop._RETIRED_ICONS.items():
        assert shop.key_for_icon(icon) in shop.CATALOG, icon
    inv = {k: 2 for k in shop.RETIRED}
    persistence._heal_bag(inv)
    assert not (set(inv) & set(shop.RETIRED)), "a retired key survived the heal"
    assert sum(inv.values()) == 2 * len(shop.RETIRED), "the heal lost goods"


def test_rarity_is_decoupled_from_price():
    """⭐THE RULING (Joel, 2026-08-02: "yeah decouple rarity from price").

    Rarity used to be DEFINED as price -- `tier_for_price` -- so "legendary"
    meant "expensive", and the economy audit that day measured expensive at
    about 23 real minutes of adventuring.  Scarcity was decorative.

    It reads the authored SUPPLY columns now, which nothing had ever read:
    DefaultStockChance x DefaultMaxStock = the expected number of copies on a
    shelf.  Still derived, still no invented economy -- the other column was
    always there.  This pins that the two axes actually came apart."""
    import statistics
    from tuipet import shop
    priced = [(v.price, shop.supply_score(v.icon), v.tier, k)
              for k, v in shop.CATALOG.items()
              if v.price and shop.supply_score(v.icon) is not None]
    assert len(priced) > 50

    # 1. a CHEAP good can be the rarest thing in the game
    cheap_legendary = [k for p, _s, t, k in priced if t == "legendary" and p <= 500]
    assert cheap_legendary, "no cheap good is rare -- still price-coupled"

    # 2. ...and a DEAR good can be the commonest
    dear_common = [k for p, _s, t, k in priced if t == "common" and p >= 2000]
    assert dear_common, "no expensive good is common -- still price-coupled"

    # 3. the correlation is broken, not merely dented
    xs = [p for p, _s, _t, _k in priced]
    ys = [s for _p, s, _t, _k in priced]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5
    r = cov / den
    assert abs(r) < 0.35, f"price still predicts supply: r={r:+.3f}"

    # 4. and every band still has real membership -- a ladder, not a cliff
    for name in shop.TIER_ORDER:
        assert sum(1 for _p, _s, t, _k in priced if t == name) >= 5, name


def test_an_unauthored_good_falls_back_to_the_price_ladder():
    """tuipet's own additions carry no CSV stock columns.  They must not
    silently read as the commonest thing there is -- the price ladder is the
    honest fallback, and it is still a statement about worth."""
    from tuipet import shop
    assert shop.supply_score("i:99999") is None
    assert shop.tier_for_supply("i:99999", 9000) == shop.tier_for_price(9000)
    assert shop.tier_for_supply("i:99999", None) is None      # grant-only
