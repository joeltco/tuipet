

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


# ---- boss-battle audit 2026-07-05 -------------------------------------------

def test_enemy_bits_read_the_real_column():
    """The enemies.csv header is the essay-length 'BitsWon (range of random
    bits - ...)': a bare .get('BitsWon') silently missed it and EVERY enemy
    paid the 1..5 fallback (bosses pay 100..2000 in canon)."""
    from tuipet import data
    es = data.load_enemies()
    assert sum(1 for e in es if e["bits"] == (1, 5)) == 0    # no fallback in the real data
    bosses = {e["num"]: e for e in es if e["boss"]}
    assert bosses[102]["bits"] == (100, 100)                 # Devimon's flat purse
    assert max(hi for e in bosses.values() for hi in [e["bits"][1]]) >= 2000


def test_final_bosses_carry_the_parade_message():
    from tuipet import data
    fin = [e for e in data.load_enemies() if e["parade_msg"]]
    assert len(fin) == 5                                     # one per map
    assert all(e["parade_msg"] == "You saved the Digital World!" for e in fin)
    assert all(e["boss"] for e in fin)


def test_boss_kill_appends_the_collapse_and_pays_the_purse():
    """zoneBossDeath: a beaten zone boss blinks out and squashes into the
    ground (canon 48->24->12->0) instead of ending on the explosion."""
    import random
    from tuipet.pet import Pet
    from tuipet import data
    from tuipet.battlescreen import BattlePanel
    boss = next(e for e in data.load_enemies() if e["boss"] and e["num"] == 102)
    for seed in range(20):
        random.seed(seed)
        p = Pet(num=102, name="D", stage="Champion", attribute="Virus",
                vaccine=999, data_power=999, virus=999, obedience=800)
        p.world_seconds = 12 * 60.0
        p.full_health = 90
        bp = BattlePanel(p, boss, wild=True)
        b0 = p.bits
        for _ in range(5000):
            if bp.phase == "menu":
                bp.key("1")
            elif bp.phase == "surrender_ask":
                bp.key("n")
            elif bp.phase == "result":
                break
            else:
                bp.anim()
        if bp.won:
            break
    assert bp.won
    beats = [e for e in bp.timeline if e["m"] == "bossdie"]
    assert beats and {e.get("keep") for e in beats if e.get("keep")} == {8, 4, 2}
    for i, e in enumerate(bp.timeline):
        if e["m"] != "bossdie":
            continue
        lines = bp._render_scene_frame(e).plain.split("\n")
        assert len(lines) <= 12 and all(len(ln) <= 40 for ln in lines)
    r = None
    while r is None:
        r = bp.key("enter")
    assert p.bits - b0 == 100                                # the REAL purse, not 1..5


def test_map_final_boss_cues_the_victory_parade():
    """Canon ZoneChange tail: a parade-message boss parades the map's bosses
    (serialised -- the LCD shows one mon at a time) with the victory line."""
    import random
    from tuipet.pet import Pet
    from tuipet import data
    from tuipet.adventurescreen import AdventurePanel, PARADE_T
    random.seed(7)
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=800)
    p.world_seconds = 12 * 60.0
    panel = AdventurePanel(p)
    final = next(e for e in data.load_enemies() if e["parade_msg"])

    class _B:
        won = True

    class _Sub:
        def key(self, k):
            return ("done", _B())

        def text(self):
            return None
    panel.sub = _Sub()
    panel._pending = (True, final)
    panel.key("enter")
    assert panel._parade is not None and len(panel._parade["nums"]) <= 3
    assert panel.adv.last == "You saved the Digital World!"
    s = panel.strip()
    assert "SPACE next" in s and panel.adv.last in s
    frames = 0
    while panel._parade is not None:
        panel.anim()
        lines = panel.text().plain.split("\n")
        assert len(lines) <= 12 and all(len(ln) <= 40 for ln in lines)
        frames += 1
        assert frames < 500
    assert panel.travelling                                  # back on the road
    # skips hop marcher-by-marcher and never wedge the panel
    panel._parade = {"t": 0, "nums": [102, 194, 274]}
    for _ in range(3):
        panel.key("space")
    assert panel._parade is None


def test_mid_journey_contracts():
    """Mid-journey audit (2026-07-06), all CLEAN -- pin the load-bearers:
    a lost battle costs one adventure life + the enemy's knockback; at zero
    life the pet RETREATS (toClosestTown; zone start when none behind) with
    life refilled -- the run never ends; clearing the gate advances the zone
    ON THE PET (quit-safe: a re-entered adventure resumes the NEXT zone,
    location per-outing by design); a boss FLEE knocks back and re-arms the
    gate (per-pass cleared set)."""
    import random
    from tuipet import data
    from tuipet.adventure import Adventure, MAX_LIFE
    from tuipet.pet import Pet

    def hero():
        rec = data.load_sprites()[1][100]
        p = Pet(num=100, name=rec["name"], stage="Champion",
                attribute="Vaccine", obedience=500)
        p.world_seconds = 10 * 3600.0
        p.energy = p.max_energy
        return p

    random.seed(5)
    adv = Adventure(hero())
    adv.location = 750
    foe = {"name": "TestFoe", "num": 999, "penalty": 3}
    adv.resolve(False, False, foe)
    assert (adv.life, adv.location) == (MAX_LIFE - 1, 747)   # life + knockback
    adv.resolve(False, False, foe)
    adv.resolve(False, False, foe)                            # third loss: retreat
    assert adv.life == MAX_LIFE and adv.location == 0         # refilled at the fallback
    assert not adv.done                                       # the run survives

    p2 = hero()
    adv2 = Adventure(p2)
    gate = (adv2.zone["bosses"] or [{"num": 1, "name": "Gate"}])[-1]
    adv2.location = adv2.total_steps
    adv2.boss_pending = True
    adv2.resolve(True, True, dict(gate, parade_msg=""))
    assert (adv2.zi, p2.adv_zone) == (1, 1)                   # zone advance persists
    p2.adv_loc = 0
    adv3 = Adventure(p2)
    assert (adv3.zi, adv3.location) == (1, 0)                 # resume next zone, fresh outing

    adv4 = Adventure(hero())
    adv4.location = 50
    adv4.boss_pending = True
    adv4.flee({"name": "Blocker", "num": 500, "penalty": 5}, was_boss=True)
    assert adv4.location == 45 and not adv4.boss_pending      # knocked back...
    assert 500 not in adv4._cleared                           # ...and the gate re-arms
