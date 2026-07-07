

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
    panel._trans = None                             # settled past the teleport
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
    panel.adv.location = panel.adv.total_steps      # the beaten boss WAS the gate
    panel.key("enter")
    # feel arc 2026-07-07: the zoneChange pulse plays first, parade chained
    assert panel._pulse is not None and panel._pulse["parade"]
    assert panel.adv.last == "You saved the Digital World!"
    while panel._pulse is not None:
        panel.anim()
    assert panel._parade is not None and len(panel._parade["nums"]) <= 3
    # the note field-marquees under the fixed hint (major audit 2026-07-07):
    # the hint shows EVERY frame; head then tail scroll through the window
    windows = []
    for i in range(160):
        panel.frame_i = i
        s = panel.strip()
        assert "SPACE next" in s
        windows.append(s.split("  [dim]")[0])
    assert any(w.startswith("You saved") for w in windows)
    assert any("World!" in w for w in windows)
    panel.frame_i = 0
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


def test_a_wild_win_buys_encounter_immunity():
    """BattleImmunitySeconds 90 (adventure audit 2026-07-06): after a random
    wild win, no random encounters roll until ~140 walked steps pass; bosses
    are not wild wins and grant nothing."""
    import random as _r
    from tuipet.adventure import Adventure, BATTLE_IMMUNITY_STEPS
    from tuipet.pet import Pet
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    adv = Adventure(p)
    enemy = {"num": 4, "name": "X", "stage": "Champion", "vaccine": 1,
             "data_power": 1, "virus": 1, "hp": 5, "bits": (1, 1), "loot_table": -1}
    adv.resolve(True, was_boss=False, enemy=enemy)
    assert adv._immunity_steps == BATTLE_IMMUNITY_STEPS
    _r.seed(1)
    assert adv._encounter_roll() is False           # suppressed flat
    adv._immunity_steps = 0.0
    adv2 = Adventure(p)
    adv2.resolve(True, was_boss=True, enemy=dict(enemy, boss=True))
    assert getattr(adv2, "_immunity_steps", 0.0) == 0.0   # bosses grant nothing


def test_the_current_habitat_follows_the_road_and_comes_home():
    """Habitat audit 2026-07-06: canon's currentHabitat is set from the zone
    BACKGROUND while traveling (WorldMap.step -> setCurrentHabitat) -- climate,
    compatibility odds and the current-habitat evolution gate all travel; the
    home resumes when the adventure closes (and on any save load)."""
    from tuipet.adventure import Adventure
    from tuipet.pet import Pet
    from tuipet import data, persistence
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    home = p.habitat
    adv = Adventure(p)
    assert p.home_habitat == home                  # old-save backfill on entry
    bgs = adv.zone.get("bgs", ())
    if bgs:
        assert any(lo <= adv.location <= hi and p.habitat == hid
                   for lo, hi, hid in bgs if hid in data.load_habitats()) or p.habitat == home
        adv.location = bgs[-1][0]                  # stand on the LAST terrain span
        adv._set_zone_habitat()
        assert p.habitat == bgs[-1][2]
    p.go_home_habitat()
    assert p.habitat == home                       # the exit hook restores the home
    # ...and a save written mid-road loads back at home
    p.habitat = 99 if home != 99 else 98
    q, _ = persistence.pet_from_save(persistence.to_save_dict(p), catch_up=False)
    assert q.habitat == home


def test_garuda_chases_the_next_boss_ahead():
    """Transport audit 2026-07-06: getNextBoss is the closest boss AHEAD,
    crossing zones -- the old pick took the current zone's first boss and
    could warp you BACKWARD."""
    from tuipet import transportscreen, data
    from tuipet.pet import Pet
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    maps = data.load_maps()
    # find a zone whose FIRST boss is not its last, so "past the first" is real
    pick = None
    for mi, m in enumerate(maps):
        for zi, z in enumerate(m["zones"]):
            locs = sorted(b.get("location") or z.get("total_steps", 10000)
                          for b in z.get("bosses", ()))
            if len(locs) >= 2:
                pick = (mi, zi, locs)
                break
        if pick:
            break
    if pick is None:
        import pytest
        pytest.skip("no multi-boss zone in the data")
    mi, zi, locs = pick
    p.adv_map, p.adv_zone = mi, zi
    p.adv_loc = locs[0] + 1                       # already PAST the first boss
    p.inventory["i:19"] = 1
    panel = transportscreen.TransportPanel(p, "i:19")
    panel.kind = "danger"
    panel.options = panel._options()
    panel.key("enter")
    assert p.adv_loc == locs[1] - 1               # one shy of the NEXT boss, not the first


def test_birdra_needs_a_town_and_finds_the_closest():
    from tuipet import transportscreen, data
    from tuipet.pet import Pet
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    maps = data.load_maps()
    mi = next((i for i, m in enumerate(maps)
               if any(z.get("towns") for z in m["zones"])), None)
    if mi is None:
        import pytest
        pytest.skip("no towns anywhere")
    p.adv_map, p.adv_zone = mi, 0
    p.energy = 1
    p.inventory["i:18"] = 1
    panel = transportscreen.TransportPanel(p, "i:18")
    panel.kind = "town"
    panel.options = panel._options()
    assert panel.options                          # a town exists: the ride is offered
    panel.key("enter")
    z = maps[mi]["zones"][p.adv_zone]
    assert z.get("towns") and p.adv_loc == z["towns"][0][0]   # landed ON a real town
    assert p.energy == p.max_energy               # ...and rested there


# ---- stride events resolve in POSITION order (major audit 2026-07-07) --------

def _stub_adv(town=None, boss_loc=25, bgs=()):
    """An Adventure over a synthetic one-zone map (instance-local: never mutate
    the lru-cached zone data -- the .186 test-pollution lesson)."""
    from tuipet.adventure import Adventure
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.stop_travel_prob = lambda: 0.0                    # no refusal noise
    adv = Adventure(p)
    zone = {"total_steps": 400, "randoms": [],          # stride = 400/40 = 10
            "bosses": [{"num": 500, "name": "Gate", "location": boss_loc}],
            "towns": [town] if town else [], "bgs": list(bgs),
            "rand_foods": [], "rand_items": []}
    adv.maps = [{"zones": [zone]}]
    adv.mi = adv.zi = 0
    adv.location = 20
    return adv, p


def test_town_before_boss_in_one_stride_is_reached_first(monkeypatch):
    """A town-start and an uncleared boss in the SAME stride resolve in
    position order, like the per-step canon walk -- the old boss-first
    ordering let the town event carry the pet PAST an unfought gate."""
    import random as _r
    from tuipet import adventure as amod
    monkeypatch.setattr(amod.random, "random", lambda: 0.99)   # no discover/stop
    adv, p = _stub_adv(town=(22, 24, 0), boss_loc=25)
    ev = adv.travel()                                   # stride sweeps 20 -> 30
    assert ev == ("town", 0), ev                        # the town at 22 comes FIRST
    assert adv.location == 22                           # stopped at the gates
    assert not adv.boss_pending
    ev = adv.travel()                                   # walk on -> the boss stands
    assert ev and ev[0] == "boss"
    assert adv.location == 25


def test_boss_stop_wears_the_habitat_of_the_stop(monkeypatch):
    """Stopping AT the boss re-derives the zone habitat for the CLAMPED spot --
    the old order set it for the overshot pre-clamp location."""
    from tuipet import adventure as amod, data
    monkeypatch.setattr(amod.random, "random", lambda: 0.99)
    hids = sorted(data.load_habitats())[:2]
    adv, p = _stub_adv(boss_loc=25,
                       bgs=[(0, 25, hids[0]), (26, 400, hids[1])])
    p.habitat = hids[1]                                 # force a visible shift
    ev = adv.travel()
    assert ev and ev[0] == "boss" and adv.location == 25
    assert p.habitat == hids[0], "the habitat must match step 25, not step 30"


# ---- road care keys (Joel 2026-07-07: action keys live during adventure) -----

def _road_panel():
    from tuipet.adventurescreen import AdventurePanel
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.bits = 500
    pan = AdventurePanel(p)
    pan._trans = None            # settled past the arrival teleport
    pan.travelling = False
    return pan, p


def test_road_feed_hosts_the_panel_and_holds_the_journey():
    """f opens the REAL FeedPanel as a sub; the journey clock holds while it's
    open; the meal's outcome lands on the strip (no home fx on the road)."""
    from tuipet.feedscreen import FeedPanel
    pan, p = _road_panel()
    p.hunger = 0
    p.compliance = True                     # no refusal noise
    pan.travelling = True
    pan.key("f")
    assert isinstance(pan.sub, FeedPanel)
    loc0 = pan.adv.location
    for _ in range(30):
        pan.anim()                          # the sub holds the road
    assert pan.adv.location == loc0, "travel must pause while feeding"
    r = None
    for _ in range(40):                     # pick the first food that lands
        r = pan.key("enter")
        if pan.sub is None:
            break
        pan.key("down")
    assert pan.sub is None
    assert pan.adv.last                      # the outcome reads on the strip
    assert p.hunger > 0                      # it actually ate


def test_road_scold_answers_the_travel_refusal_window():
    """A travel refusal opens a canon scold window (one of the THREE sites) --
    k was unreachable mid-adventure, so the window could only expire."""
    pan, p = _road_panel()
    p.stop_travel_effects()                  # the refusal just fired
    assert p.scold_flag
    pan.key("k")
    assert not p.scold_flag, "the scold must answer the window"
    assert pan.adv.last                      # its verdict reads on the strip


def test_road_direct_keys_heal_praise_lights():
    pan, p = _road_panel()
    p.sick = True
    pan.key("h")
    assert pan.adv.last                      # heal verdict on the strip
    pan._care = None                         # let the care beat finish (feel arc:
    #                                          keys lock while one plays)
    pan.key("r")
    assert pan.adv.last
    pan._care = None
    lights0 = p.lights
    pan.key("s")
    assert p.lights != lights0               # the toggle landed


def test_road_bag_opens_and_transport_is_refused():
    """i hosts the bag; a transport item is REFUSED on the road (transports
    leave from home -- the adv_loc mailbox must not be corrupted mid-run)."""
    from tuipet.shopscreen import ShopPanel
    pan, p = _road_panel()
    p.add_item("i:28")                       # a transport ticket
    pan.key("i")
    assert isinstance(pan.sub, ShopPanel)
    sp = pan.sub
    assert p.away                            # the road flag is up
    for _ in range(40):                      # find the ticket in the bag
        rows = sp._rows()
        if rows and (rows[min(sp.cursor, len(rows) - 1)].get("action") or "") \
                in __import__("tuipet.data", fromlist=["data"]).TRANSPORT_ACTIONS:
            break
        r = sp.key("right") if not rows else sp.key("down")
    res = pan.key("enter")                   # try to board
    assert pan.sub is not None, "the ride must NOT leave the bag"
    assert "home" in sp.msg
    pan.key("escape")
    assert pan.sub is None                   # back on the road


def test_life_recovery_potion_is_road_only_and_gated_at_max():
    """Life Recovery (item 27, items.csv AdventureLifeInc=1): +1 Digital World
    life, unusable at MaxAdventureLife (canon PhysicalState.useItem's
    eligibility gate -- the potion is NOT consumed by a refused use).  tuipet
    life is per-outing, so it works only on the road (canon's world life
    persists at home -- documented adaptation)."""
    from tuipet.adventure import MAX_LIFE
    from tuipet import data
    e = data.consumable_by_key("i:27")
    assert e and e["adv_life"] == 1 and data.item_is_functional(e)
    pan, p = _road_panel()
    p.obedience, p.compliance = 1000, True   # no refusal noise
    p.add_item("i:27")
    assert pan.adv.life == MAX_LIFE
    assert "full" in p.use_item("i:27")      # gated at max...
    assert p.inventory.get("i:27")           # ...and NOT consumed
    pan.adv.life = 1
    msg = p.use_item("i:27")
    assert pan.adv.life == 2 and "life point" in msg.lower()
    assert not p.inventory.get("i:27")       # spent
    p.add_item("i:27")
    p.away = False                           # home again: road-only
    assert "Digital World" in p.use_item("i:27")
    assert p.inventory.get("i:27")           # kept for the next outing
