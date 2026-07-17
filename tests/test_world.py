"""The named/themed adventure world (Joel 2026-07-09: tuipet is its own game --
regions/zones/towns get real names + biome identity, all DERIVED from the
terrain the game renders, never invented)."""
import random
from tuipet.pet import Pet
from tuipet import data, shop, world


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500, bits=99999)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_every_map_zone_town_is_named_and_unique():
    """No place is left as a bare number: every real map/zone/town in the data
    has an authored name, and no two towns (or zones) collide."""
    maps = data.load_maps()
    region_names, zone_names = set(), set()
    for m in maps:
        rn = world.region_name(m["map"])
        assert not rn.startswith("Region "), f"map {m['map']} unnamed"
        region_names.add(rn)
        for z in m["zones"]:
            zn = world.zone_name(m["map"], z["zone"])
            assert not zn.startswith("Zone "), f"zone {m['map']}-{z['zone']} unnamed"
            zone_names.add(zn)
    assert len(region_names) == len(maps)              # regions distinct
    assert len(zone_names) == sum(len(m["zones"]) for m in maps)  # zones distinct

    towns = data.load_towns()
    names = [world.town_name(t) for t in towns]
    assert all(not n.startswith("Town ") for n in names), "an unnamed town"
    assert len(set(names)) == len(names), "duplicate town name"


def test_town_biome_is_derived_from_the_zone_terrain():
    """A town's identifying biome is read from the zone habitat at its step
    (towns carry TownBackgroundID 13 in their own record) -- spot-check the
    real geography the analysis found."""
    assert world.town_biome_name(20) == "Desert"       # Dunehaven, map5 dunes
    assert world.town_biome_name(3) == "Underwater"    # Coral Deep
    assert world.town_biome_name(23) == "Tundra"       # Frostmere
    assert world.town_biome_name(2) == "City"          # Steelport
    assert world.town_biome_name(0) == "Evil Castle"   # Gloamgate


def test_greeting_names_the_town_and_known_for_is_populated():
    for t in data.load_towns():
        g = world.town_greeting(t)
        assert world.town_name(t) in g and g.endswith((".", "!"))
        assert world.town_known_for(t).endswith("goods and eggs")


def test_specialty_keys_are_real_general_consumables():
    """Every biome specialty resolves to an existing consumable and is NOT an
    evolution/spirit item (those live at item ids >= 14; general toys 63-66 ok)."""
    for t in data.load_towns():
        for is_food in (True, False):
            for key in world.biome_specialty_keys(t, is_food):
                e = data.consumable_by_key(key)
                assert e, f"town {t} specialty {key} missing"
                if key.startswith("i:"):
                    iid = int(key[2:])
                    assert iid < 14 or iid >= 63, f"town {t} stocks evolution item {key}"


# --- biome-biased town tournaments (Joel 2026-07-09) ---
from tuipet import tournament as _T


def test_town_hosts_its_biome_field_championship():
    """Each town's always-open signature slot (index > 23) hosts the cup for its
    biome's field -- Coral Deep -> Deep Saver Cup, Steelport -> Metal Empire Cup."""
    p = _pet()
    for tid, field in ((3, "DeepSaver"), (2, "MetalEmpire"), (0, "NightmareSoldier"),
                       (23, "DeepSaver"), (20, "NatureSpirit")):
        assert world.town_field(tid) == field
        sched = _T.town_schedule(p, data.load_towns()[tid])
        openslots = [sched[i] for i in range(len(sched)) if i > 23]
        cup = _T.biome_cup_id(p.season, field)
        assert cup >= 0 and cup in openslots, f"town {tid} missing its {field} cup"


def test_town_bout_entrants_skew_to_the_biome_field():
    """A town cup with no field rule of its own draws NPCs skewed toward the
    biome field, so the fight feels like the place (soft, not exclusive)."""
    import random
    p = _pet()
    _, by = data.load_sprites()
    cup = _T.trophy_by_id(0)                       # an open, unrestricted Spring cup
    def deep(fb):
        random.seed(42)
        return sum(1 for _ in range(40) for e in _T.Tournament(p, cup, field_bias=fb).entrants
                   if by.get(e["num"], {}).get("field") == "DeepSaver")
    assert deep("DeepSaver") > 3 * deep(""), "biome entrant bias not taking effect"
