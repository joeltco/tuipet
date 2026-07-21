"""Adventure rebuild — the real 26-ZONE GEOGRAPHY (phase 4, 2026-07-20).

Pins the wiring of data/zones.csv + enemies.csv into 26 run-zones: one biome per
run (the gate boss's terrain, no mid-zone span-hopping), each with its OWN wild
enemy table.  Joel's order: "wire the real 26 zones after encounters."
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES, pick_zone, HABITAT_SCENE
from tuipet import backgrounds
from tuipet.pet import Pet


def _champ(num=100):
    return Pet(num=num, stage="Champion", attribute="Vaccine", obedience=500)


def test_all_26_real_zones_are_wired():
    assert len(ZONES) == 26                                # 5 maps: 7/7/3/2/7
    for z in ZONES:
        assert z["name"] and z["scene"] and z["steps"] == adventure.INTERACTIVE_STEPS
        assert z["scene"] in backgrounds.NAMES             # a real backdrop key
        assert isinstance(z["randoms"], list)              # its own wild table


def test_pick_is_deterministic_and_one_biome_per_run():
    p = _champ()
    z = pick_zone(p)
    assert z in ZONES and pick_zone(p) is z                # stable identity, no RNG
    a = Adventure(p)
    scene = a.scene
    assert scene == z["scene"]
    # own-game law: the backdrop never changes across the whole crossing
    for _ in range(a.total):
        a.travel()
        assert a.scene == scene                            # ONE biome, no mid-run swap


def test_the_wild_pool_is_the_zones_own_table(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)
    # a zone that actually ships randoms
    z = next(z for z in ZONES if z["randoms"])
    a = Adventure(_champ(), zone=z)
    zone_nums = {e["num"] for e in z["randoms"]}
    for _ in range(12):
        a._immunity = 0
        r = a.travel()
        assert isinstance(r, tuple) and r[0] == "encounter"
        assert r[1]["num"] in zone_nums                    # from THIS zone, not stage-wide
        a.resolve(True)                                    # clear it, keep rolling


def test_every_zone_biome_is_a_real_scene():
    # every habitat id that any zone resolves to maps to a shipped scene
    for z in ZONES:
        assert z["scene"] in backgrounds.NAMES, (z["name"], z["scene"])
    # the map covers every habitat id the world data actually uses
    from tuipet import data
    used = {hid for mp in data.load_maps() for zz in mp["zones"]
            for _lo, _hi, hid in zz.get("bgs", ())}
    for hid in used:
        assert hid in HABITAT_SCENE, f"habitat {hid} has no scene"
