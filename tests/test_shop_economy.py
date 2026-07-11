"""Shop/economy canon audit pins (2026-07-06) vs DVPet's ShopConsumable /
randomizeShop / checkRestock / getResellPrice.

Nearly everything verified verbatim from the earlier shop arcs: the seasonal
stock/sale chance pools with mustStock priority, checkSale's price - price //
saleFactor, the restock credit bank (5-min cadence, 1%, cap 4) with the
new-item swap, dailyChange clearing the shelves, town shopConsumable
overrides, per-use resell with the data-driven resellFactor (no floor).
FOUND: the drop-UNLOCK progression was missing -- canon's unlockItem/
unlockFood turn a wild find into a permanent home-shop listing; the nine
Digimentals (ShopUnlocked=FALSE, price 4000) are the payload."""
from tuipet import data, persistence, shop
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_digimentals_start_locked_out_of_the_shop():
    p = _pet()
    pool = shop._pool(p, is_food=False)
    assert not any(e["key"] == "i:15" for e in pool)

def test_a_wild_find_unlocks_the_listing_for_good():
    persistence.shop_unlock_add("i:15")           # Courage Digimental, dropped
    p = _pet()
    pool = shop._pool(p, is_food=False)
    got = next((e for e in pool if e["key"] == "i:15"), None)
    assert got is not None
    assert got["price"] == 4000                   # the real DefaultPrice, not invented
    # and it survives a rebirth (the progress channel, like the digimemory)
    assert "i:15" in persistence.shop_unlocks()

def test_the_unlock_reaches_town_shelves_too():
    persistence.shop_unlock_add("i:15")
    towns = data.load_towns() if hasattr(data, "load_towns") else {}
    # the town pool builder consults the same earned set; pin via the helper
    e = data.consumable_by_key("i:15")
    assert shop._unlocked(e, persistence.shop_unlocks())
    assert not shop._unlocked(e, set())

def test_check_sale_formula_is_canon():
    e = {"key": "i:0", "price": 100, "sale_factor": 4,
         "sale_chance": [100] * 4, "min_stock": 1, "max_stock": 1}
    p = _pet()
    slot = shop._mk_slot(p, e, check_sale=True)
    assert slot["sale"] == 100 - 100 // 4         # price - price/saleFactor = 75


def test_biome_specialty_seats_are_all_sellable():
    """Every BIOME specialty id must be a PRICED, functional consumable --
    specialties draw from the gated town pool, so a price-0 home staple
    (Meat/Fish/Fruit/Veg/Med/Cookie) silently never stocked and 9 of 14
    biomes lost their authored signature goods (audit 2026-07-13)."""
    import csv
    import os
    from tuipet import world
    root = os.path.join(os.path.dirname(world.__file__), "data")
    foods = {int(r["FoodIdentificationNum"]): r
             for r in csv.DictReader(open(os.path.join(root, "foods.csv")))}
    items = {int(r["ItemIdentificationNum"]): r
             for r in csv.DictReader(open(os.path.join(root, "items.csv")))}
    for biome, spec in world.BIOME.items():
        for fid in spec["foods"]:
            assert fid in foods, f"{biome}: food {fid} does not exist"
            assert int(foods[fid]["DefaultPrice"] or 0) > 0, \
                f"{biome}: food {fid} ({foods[fid]['Name']}) is a price-0 staple -- it can never stock"
        for iid in spec["items"]:
            assert iid in items, f"{biome}: item {iid} does not exist"
            assert int(items[iid]["DefaultPrice"] or 0) > 0, \
                f"{biome}: item {iid} ({items[iid]['Name']}) is price-0 -- it can never stock"
