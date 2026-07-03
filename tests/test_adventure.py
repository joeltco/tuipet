

# ---- the discover system (Zone.checkInvestigate / checkItem) -----------------

def test_zone_pools_are_loaded():
    from tuipet import data
    z = data.load_maps()[0]["zones"][0]
    assert z["rand_foods"] and z["rand_items"]      # zones.csv RandomFood/RandomItems


def test_investigate_finds_a_zone_pool_item_and_opens_praise():
    import random
    from tuipet.adventure import Adventure
    from tuipet.pet import Pet
    from tuipet import data
    random.seed(2)
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    adv = Adventure(p)
    for _ in range(50):
        p.inventory.clear()
        p.praise_flag = False
        kind, thing = adv.investigate()
        if kind == "item":
            assert thing["key"] in p.inventory       # bagged
            assert p.praise_flag                     # ReturnItem -> setPraise(true)
            pool = ([f"f:{i}" for i in adv.zone["rand_foods"]]
                    + [f"i:{i}" for i in adv.zone["rand_items"]])
            assert thing["key"] in pool              # from the ZONE's pools
            break
    else:
        raise AssertionError("no item in 50 investigates (1/3 ambush odds)")


def test_investigate_can_ambush():
    import random
    from tuipet.adventure import Adventure
    from tuipet.pet import Pet
    random.seed(2)
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    adv = Adventure(p)
    kinds = {adv.investigate()[0] for _ in range(60)}
    assert "enemy" in kinds                          # 1 in 3 is an ambush


def test_discover_roll_fires_on_the_walk():
    import random
    from tuipet.adventure import Adventure
    from tuipet.pet import Pet
    random.seed(4)
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.obedience, p.mood = 24800, 0                   # shrink the seed to ~200: fires fast
    p.world_seconds = 10 * 60.0                      # mid-day (night adds +15000 to the seed)
    p.sleep_limit = 9e9
    adv = Adventure(p)
    for _ in range(400):
        ev = adv.travel()
        if ev and ev[0] == "discover":
            break
        if ev and ev[0] in ("encounter", "boss"):
            adv.boss_pending = False
            continue
    else:
        raise AssertionError("discover never fired with a tiny seed")
