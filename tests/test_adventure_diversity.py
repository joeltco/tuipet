"""Diversity guard (Joel 2026-07-13: "make sure all adventure habitats have a
diverse enemy/item/shop/boss system").  Every expedition must field a real
biome, a wild pool at least MIN_WILDS species deep (thin zones borrow the
map's earlier roamers), a boss, a find pool, and a town whose shop actually
sells -- swept over every zone of every map, so a data regression can never
ship a hollow adventure."""
from tuipet import data, world
from tuipet.adventure import Adventure, MIN_WILDS
from tuipet.pet import Pet


def _adv_at(mi, zi):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.adv_map, p.adv_zone = mi, zi
    return Adventure(p), p


def test_every_zone_fields_a_diverse_system():
    maps = data.load_maps()
    habs = data.load_habitats()
    towns = data.load_towns()
    for mi, m in enumerate(maps):
        for zi, z in enumerate(m["zones"]):
            adv, _p = _adv_at(mi, zi)
            tag = f"map {m['map']} zone {z['zone']}"
            assert adv.biome in habs, f"{tag}: biome is not a real habitat"
            pool = {e["num"] for e in list(z["randoms"]) + adv._extra_wilds
                    if not data.is_placeholder(e["num"])}
            assert len(pool) >= MIN_WILDS, f"{tag}: thin wild pool ({len(pool)})"
            assert z["bosses"], f"{tag}: no boss guards the gate"
            finds = len(z.get("rand_foods", [])) + len(z.get("rand_items", []))
            assert finds >= 5, f"{tag}: bare find pool ({finds})"
            assert z.get("towns"), f"{tag}: no town on the road"
            for _lo, _hi, tid in z["towns"]:
                t = towns.get(tid)
                assert t, f"{tag}: town {tid} has no record"
                assert t["can_sell_food"] or t["can_sell_items"], \
                    f"{tag}: town {tid} sells nothing"
                assert world.biome_specialty_keys(tid, True) or \
                    world.biome_specialty_keys(tid, False), \
                    f"{tag}: town {tid} has a bare specialty shelf"


def test_expeditions_span_a_diverse_biome_set():
    """The dominant-terrain rule names at least 11 distinct biomes across the
    world's zones -- expeditions are not one castle after another."""
    maps = data.load_maps()
    seen = set()
    for mi, m in enumerate(maps):
        for zi in range(len(m["zones"])):
            adv, _p = _adv_at(mi, zi)
            seen.add(adv.biome)
    assert len(seen) >= 11, sorted(seen)


def test_thin_zones_borrow_earlier_roamers():
    """Zone 5-3 (Foundry-era Lake) natively fields 3 wild species; the floor
    pads it with the map's earlier wilds, who roam the whole zone."""
    maps = data.load_maps()
    found = None
    for mi, m in enumerate(maps):
        for zi, z in enumerate(m["zones"]):
            n = len({e["num"] for e in z["randoms"]
                     if not data.is_placeholder(e["num"])})
            if n and n < MIN_WILDS:
                found = (mi, zi, n)
                break
        if found:
            break
    if not found:
        return                                    # no thin zone in this dataset
    mi, zi, n = found
    adv, _p = _adv_at(mi, zi)
    assert len(adv._extra_wilds) >= MIN_WILDS - n
    assert all(e.get("location", 0) == 0 for e in adv._extra_wilds), \
        "borrowed wilds roam the whole zone; placed ambushers stay home"
    # and they actually turn up in the eligible-wilds pick
    adv.location = adv.total_steps // 2
    nums = {e["num"] for e in adv._wilds(prev=0)}
    assert {e["num"] for e in adv._extra_wilds} <= nums
