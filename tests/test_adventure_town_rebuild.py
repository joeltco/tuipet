"""The map-tier town shelf and the retired road inventory contract."""
import datetime

import pytest

from tuipet import adventure, persistence, shop, tournament
from tuipet.pet import Pet
from tuipet.townscreen import TownPanel, _MENU


def test_town_shelf_matches_each_map_tier():
    previous = set()
    by_tier = {}
    for i in range(30):
        tier = adventure.map_tier(i)
        band = shop._TOWN_BANDS[tier]
        expected = {k for k, v in shop.CATALOG.items()
                    if v.price is not None and v.price > 0
                    and (k in shop._ROAD_ONLY or shop._SHOP_BANDS[v.tier] <= band)}
        keys = [e["key"] for e in shop.town_stock(i)
                if e["category"] != shop.ARMOR_CATEGORY]   # crests: own test
        assert len(keys) == len(set(keys))
        assert set(keys) == expected
        assert previous <= set(keys)
        assert by_tier.setdefault(tier, set(keys)) == set(keys)
        previous = set(keys)


def test_retired_road_inventory_converts_on_load():
    pet = Pet(num=100, stage="Champion")
    pet.inventory = {"disaster_transport": 2, "zone_transport": 3,
                     "town_transport": 4, "continent_transport": 5,
                     "shortcut": 1, "rest_kit": 2,
                     "i:28": 1, "i:29": 1, "i:30": 1, "i:31": 1}
    loaded, _ = persistence.pet_from_save(persistence.to_save_dict(pet))
    assert loaded.inventory == {"shortcut": 8, "rest_kit": 13}
    assert not set(shop.RETIRED) & set(shop.CATALOG)
    for icon in ("i:28", "i:29", "i:30", "i:31"):
        assert shop.key_for_icon(icon) in {"shortcut", "rest_kit"}


@pytest.mark.parametrize("key", ["shortcut", "rest_kit", "life_recovery"])
def test_road_tools_refuse_from_home_without_spending(key):
    pet = Pet(num=100, stage="Champion")
    pet.add_item(key)
    result = pet.use_item(key)
    assert "Save it for the road (press T)." in str(result)
    assert pet.inventory[key] == 1


def test_town_has_shop_eggs_bag_and_leave():
    assert [k for k, _ in _MENU] == ["shop", "eggs", "bag", "leave"]
    assert not hasattr(tournament, "town_cup")
    panel = TownPanel(Pet(num=100, stage="Champion"), town_id=29)
    assert "Town Cup" not in panel.text().plain
    for i in range(30):
        assert shop.town_egg_stock(i)
        assert all(e["town_id"] == i for e in shop.town_egg_rows(i))


def test_town_cap_and_sell_rates():
    pet = Pet(num=100, stage="Champion")
    pet.bits = 100_000
    today = datetime.date(2026, 3, 3)
    row = next(e for e in shop.town_stock(0, today, pet) if e["key"] == "fish")
    for _ in range(row["left"]):
        assert shop.town_buy(pet, row, today)[1] == "confirm"
    assert shop.town_buy(pet, row, today)[1] == "error"
    assert pet.inventory["fish"] <= shop.TOWN_DAILY_CAP
    assert shop.town_sell_price("fish", 0) == shop.town_price(0, "fish", shop.CATALOG["fish"].price) // 2
    deep_only = next(k for k, v in shop.CATALOG.items()
                     if v.price and v.tier == "legendary" and k not in shop._ROAD_ONLY)
    # an absent good pays half, like everywhere (7/10 minted bits on sale buys; audit 2026-10-14)
    assert shop.town_sell_price(deep_only, 0) == shop.CATALOG[deep_only].price // 2


def test_deep_town_egg_buy_uses_the_existing_counter():
    pet = Pet(num=100, stage="Champion")
    pet.bits = 10_000
    row = next(e for e in shop.town_egg_rows(29) if not e["owned"])
    before = pet.bits
    assert shop.town_egg_buy(pet, row["egg_idx"])[1] == "reward"
    assert before - pet.bits == row["price"]
    assert shop.town_egg_buy(pet, row["egg_idx"])[1] == "error"


@pytest.mark.parametrize("door,tab", [("shop", None), ("eggs", "Eggs"),
                                     ("bag", None)])
def test_deep_town_doors_keep_the_map_id(door, tab):
    panel = TownPanel(Pet(num=100, stage="Champion"), town_id=29)
    panel.cursor = next(i for i, row in enumerate(_MENU) if row[0] == door)
    panel.key("enter")
    assert panel.sub.town == 29
    if tab:
        assert panel.sub._tabs()[panel.sub.tab] == tab
    assert panel.sub.text()


def test_every_crest_sells_in_two_adventure_towns_and_never_at_home():
    """Joel 2026-10-15: crests are adventure-town exclusives; the unlock wave
    still decides when a town stocks one."""
    from tuipet.pet import Pet
    assert set(shop.CREST_TOWNS) == set(shop.DIGIMENTAL_GATES)
    assert all(len(set(t)) == 2 and all(0 <= x < 30 for x in t)
               for t in shop.CREST_TOWNS.values())
    assert not any(e["category"] == shop.ARMOR_CATEGORY
                   for e in shop.home_stock(pet=Pet(num=100, stage="Champion")))
    courage = {e["key"] for e in shop.town_stock(20)}
    assert "egg_of_courage" in courage                   # open from day one
    late = {e["key"] for e in shop.town_stock(29)}
    assert "egg_of_destiny" not in late                  # sealed until max_gen 5
