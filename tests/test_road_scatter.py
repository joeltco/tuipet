"""The themed road preserves scene history and every map-gated egg."""
import itertools
import json

from tuipet import adventure, data, egg, persistence
from tuipet.roadmigrate import OLD_TO_NEW, ROAD_ORDER_V, migrate_road

FAMILIES = (
    ("flowerfield", "blossom"),
    ("forestgate", "goldenwood", "tealhollow"),
    ("islandsea", "fileisland", "islandnight"),
    ("underwater", "seafloor", "sunsetshore"),
    ("city", "citysunset"),
    ("boulevard", "boulevardusk"),
    ("baybridge", "bridgenight"),
    ("factory", "factorynight"),
)


def test_family_distance_is_optimal():
    positions = {m["scene"]: i for i, m in enumerate(adventure.MAPS)}
    distances = [abs(positions[a] - positions[b]) for family in FAMILIES
                 for a, b in itertools.combinations(family, 2)]
    assert min(distances) >= 5
    assert sum(distances) >= 164
    assert positions["islandnight"] == 22
    assert positions["datatunnel"] == 29
    assert [m["scene"] for m in adventure.MAPS] == [
        "islandsea", "forestgate", "flowerfield", "lakeside", "greenhills", "cove",
        "moonmeadow", "underwater", "baybridge", "goldenwood", "citysunset",
        "boulevard", "cityday", "blossom", "tealhollow", "mountains", "desert",
        "fileisland", "sunsetshore", "jungle", "city", "boulevardusk", "islandnight",
        "factory", "frozenpeak", "volcano", "bridgenight", "seafloor", "factorynight",
        "datatunnel",
    ]


def test_old_settings_migrate_once_across_accounts(tmp_path):
    path = tmp_path / "settings.json"
    old = {"maps_cleared": [0, 5, 20], "wilds_beaten": ["5:405", "6:64"],
           "map_bests": {"20": 900}, "animations_seen": ["map_clear:20", "battle"],
           "last_gen": {"town_bought": {"20:steak": 2, "day": 123}}}
    path.write_text(json.dumps({"egg_order_v": persistence.EGG_ORDER_V,
                               "account": {"name": "joel"}, "progress": old,
                               "progress_by_account": {"joel": old, "other": old}}),
                    encoding="utf-8")
    first = persistence.load_settings(str(path))
    expected = {4, 0, 25}  # original Green Hills, Island Day, Volcano
    assert set(first["progress"]["maps_cleared"]) == expected
    assert first["progress"]["wilds_beaten"] == ["0:405", "6:64"]
    assert first["progress"]["map_bests"] == {"25": 900}
    assert first["progress_by_account"]["other"] == first["progress"]
    assert first["progress"]["animations_seen"] == ["map_clear:25", "battle"]
    assert first["progress"]["last_gen"]["town_bought"] == {"25:steak": 2, "day": 123}
    assert first["progress"]["road_order_v"] == ROAD_ORDER_V
    assert persistence.load_settings(str(path)) == first


def test_old_device_merge_cannot_reintroduce_old_indices(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    persistence.map_cleared_add(27)
    old = {"maps_cleared": [20], "wilds_beaten": ["5:405"], "map_bests": {"20": 900}}
    assert persistence.merge_progress(old)
    wire = persistence.progress_for_sync()
    assert wire["maps_cleared"] == [25, 27]
    assert wire["wilds_beaten"] == ["0:405"]
    assert wire["map_bests"] == {"25": 900}
    assert wire["road_order_v"] == ROAD_ORDER_V
    assert not persistence.merge_progress(old)
    assert not persistence.merge_progress(wire)
    assert old["maps_cleared"] == [20]


def test_legacy_area_clear_follows_old_scenes():
    prog = migrate_road({"maps": [0]})
    assert set(prog["maps_cleared"]) == {OLD_TO_NEW[i] for i in range(6)}
    assert migrate_road(prog) == prog


def test_pet_frontier_is_a_count_but_daily_ledger_follows_scene():
    old = {"num": -1, "stage": "Egg", "adv_progress": 12,
           "road_bounty": {"day": 123, "20": 1},
           "town_bought": {"day": 123, "20:steak": 2, "global:egg": 1}}
    pet, _ = persistence.pet_from_save(old)
    assert pet.adv_progress == 12
    assert pet.road_bounty == {"day": 123, "25": 1}
    assert pet.town_bought == {"day": 123, "25:steak": 2, "global:egg": 1}
    wire = persistence.to_save_dict(pet)
    again, _ = persistence.pet_from_save(wire)
    assert again.road_bounty == pet.road_bounty
    assert again.adv_progress == 12


def test_every_map_gated_egg_remains_reachable_and_names_its_road():
    assert egg.unreachable_wild_rows() == []
    for rule in data.load_egg_unlock().values():
        if rule["zone"] is None:
            continue
        mi, dex = egg._zone_parts(rule["zone"])
        road = adventure.MAPS[mi]
        assert road["name"] in rule["desc"]
        if dex is not None:
            assert dex in [e["num"] for e in road["randoms"]]
            assert road["name"] in egg.wild_goal(rule["zone"])


def test_rewards_stay_on_progression_slots_and_crests_follow_scenes():
    from tuipet import shop
    assert [i for i, m in enumerate(adventure.MAPS) if "grow_capsule" in m["reward"]] == [6, 22]
    assert [i for i, m in enumerate(adventure.MAPS)
            if any(k.startswith("human_") for k in m["reward"])] == list(range(20, 30))
    expected = {
        "egg_of_courage": {"volcano", "desert"},
        "egg_of_friendship": {"mountains", "factory"},
        "egg_of_love": {"flowerfield", "blossom"},
        "egg_of_knowledge": {"tealhollow", "citysunset"},
        "egg_of_sincerity": {"underwater", "cove"},
        "egg_of_reliability": {"jungle", "goldenwood"},
        "egg_of_hope": {"islandsea", "moonmeadow"},
        "egg_of_light": {"cityday", "boulevard"},
        "egg_of_kindness": {"lakeside", "greenhills"},
        "egg_of_miracles": {"bridgenight", "factorynight"},
        "egg_of_destiny": {"datatunnel", "fileisland"},
    }
    for key, scenes in expected.items():
        assert {adventure.MAPS[i]["scene"] for i in shop.CREST_TOWNS[key]} == scenes


def test_migrated_areas_do_not_unlock_different_new_scenes(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    persistence.merge_progress({"maps": [1]})
    prog = persistence.get_progress()
    rules = data.load_egg_unlock()
    # City Sunset moved to slot 10, but was never part of legacy areas 0–1.
    rule = next(r for r in rules.values() if r["name"] == "Impulse City Egg")
    assert not egg._conditions_met(rule, prog)
