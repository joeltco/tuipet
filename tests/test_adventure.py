

# ---- the discover system (Zone.checkInvestigate / checkItem) -----------------

def test_zone_pools_are_loaded():
    from tuipet import data
    z = data.load_maps()[0]["zones"][0]
    assert z["rand_foods"] and z["rand_items"]      # zones.csv RandomFood/RandomItems


def test_investigate_can_ambush():
    import random
    from tuipet.adventure import Adventure
    from tuipet.pet import Pet
    random.seed(2)
    p = Pet(num=100, stage="Adult", attribute="Vaccine")
    adv = Adventure(p)
    kinds = {adv.investigate()[0] for _ in range(60)}
    assert "enemy" in kinds                          # 1 in 3 is an ambush


def test_discover_roll_fires_on_the_walk():
    import random
    from tuipet.adventure import Adventure
    from tuipet.pet import Pet
    random.seed(4)
    p = Pet(num=100, stage="Adult", attribute="Vaccine")
    p.obedience, p.mood = 24800, 0                   # shrink the seed to ~200: fires fast

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
    assert len(fin) >= 4                                     # one per map
    assert all(e["parade_msg"] == "You saved the Digital World!" for e in fin)
    assert all(e["boss"] for e in fin)


def test_boss_kill_appends_the_collapse_and_pays_the_purse():
    """A beaten zone boss blinks out and squashes into the ground, and the
    win pays a bits purse via adventure.resolve."""
    import random
    from tuipet.pet import Pet
    from tuipet import adventure as amod
    from tuipet.adventure import Adventure
    random.seed(3)
    p = Pet.from_num(100)
    p.adv_map, p.adv_zone = 0, 0
    adv = Adventure(p)
    boss = amod._recast({"num": 102, "name": "?", "penalty": 0}, 0, 0, boss=True)
    b0 = p.bits
    adv.boss_pending = True
    adv.resolve(True, True, boss)
    assert p.bits > b0, "a boss win pays the purse"
    assert "+%db" % (p.bits - b0) in adv.last
def test_map_final_boss_cues_the_victory_parade():
    """Canon ZoneChange tail: a parade-message boss parades the map's bosses
    (serialised -- the LCD shows one mon at a time) with the victory line."""
    import random
    from tuipet.pet import Pet
    from tuipet import data
    from tuipet.adventurescreen import AdventurePanel
    random.seed(7)
    p = Pet(num=102, name="D", stage="Adult", attribute="Virus")

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
        assert "SPACE" not in s          # the parade is not skippable (2026-07-13)
        windows.append(s)
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
    # the map is BEATEN: the victory lap heads home (Joel 2026-07-13,
    # "beating a boss should be the end. teleport back home.")
    assert not panel.travelling
    assert panel._trans is not None and panel._trans["dir"] == "out"
    # keys do NOT advance the parade (own-game law 2026-07-13: beats play out)
    panel._trans = None
    panel._parade = {"t": 0, "nums": [102, 194, 274]}
    for _ in range(3):
        panel.key("space")
    assert panel._parade is not None and panel._parade["t"] == 0


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
        p = Pet(num=100, name=rec["name"], stage="Adult",
                attribute="Vaccine")

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
    p = Pet(num=102, name="D", stage="Adult", attribute="Virus")

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



def _stub_adv(town=None, boss_loc=25, bgs=()):
    """An Adventure over a synthetic one-zone map (instance-local: never mutate
    the lru-cached zone data -- the .186 test-pollution lesson)."""
    from tuipet.adventure import Adventure
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Adult", attribute="Vaccine")

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


def test_boss_stop_keeps_the_expedition_biome(monkeypatch):
    """One biome per run (Joel 2026-07-13): stopping AT the boss never
    re-dresses the habitat -- the run wears its biome start to boss."""
    from tuipet import adventure as amod, data
    monkeypatch.setattr(amod.random, "random", lambda: 0.99)
    hids = sorted(data.load_habitats())[:2]
    adv, p = _stub_adv(boss_loc=25,
                       bgs=[(0, 25, hids[0]), (26, 400, hids[1])])
    adv.biome = adv._zone_biome()                       # the stub zone's terrain
    assert adv.biome == hids[1]                         # the DOMINANT span (26-400)
    ev = adv.travel()
    assert ev and ev[0] == "boss" and adv.location == 25


# ---- road legibility (arc 2026-07-07: surface REAL state, invent nothing) ----

def test_zone_ribbon_maps_real_geography(monkeypatch):
    """adventure.ribbon: the journey card's one-line zone map -- towns.csv
    gates, uncleared boss steps and the pet's live step scaled onto a fixed
    track.  A cleared boss leaves the road; the pet wins a shared cell."""
    from tuipet import adventure as amod
    monkeypatch.setattr(amod.random, "random", lambda: 0.99)
    adv, p = _stub_adv(town=(100, 120, 0), boss_loc=300)   # total 400, at 20
    r = adv.ribbon()
    assert len(r) == 17
    assert r[0] == "◆"                        # the pet at step 20
    assert r[int(100 / 400 * 17)] == "T"      # the town gate at its real span
    assert r[int(300 / 400 * 17)] == "B"      # the boss at its real step
    assert set(r) == {"◆", "T", "B", "·"}
    adv._cleared.add(500)                     # the boss falls -> off the road
    assert "B" not in adv.ribbon()
    adv.location = 300                        # standing where it stood
    assert adv.ribbon()[int(300 / 400 * 17)] == "◆"
    # an unplaced gate boss guards the far end (last cell)
    adv2, _ = _stub_adv(boss_loc=None)
    assert adv2.ribbon()[-1] == "B"


def test_quiet_strides_narrate_real_state(monkeypatch):
    """A no-event stride reports what actually changed underfoot: the terrain
    band it crossed into, a day-phase turn (the real 1.5x night rate), or the
    battle-immunity calm.  Nothing invented -- every line is live state."""
    from tuipet import adventure as amod, data
    monkeypatch.setattr(amod.random, "random", lambda: 0.99)   # quiet road
    hids = sorted(data.load_habitats())[:2]
    # one biome per run (2026-07-13): a crossed span band narrates NOTHING and
    # re-dresses nothing -- there is no terrain shift to report any more
    adv, p = _stub_adv(boss_loc=None, bgs=[(0, 25, hids[0]), (26, 400, hids[1])])
    assert adv.travel() is None
    assert adv.last.startswith("Travelling…")
    # the immunity calm, then the plain mile
    adv, p = _stub_adv(boss_loc=None)
    adv._immunity_steps = 500.0
    assert adv.travel() is None
    assert adv.last.startswith("Calm road…")
    adv._immunity_steps = 0.0
    assert adv.travel() is None
    assert adv.last.startswith("Travelling…")


# ---- road care keys (Joel 2026-07-07: action keys live during adventure) -----

def _road_panel():
    from tuipet.adventurescreen import AdventurePanel
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Adult", attribute="Vaccine")

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


def test_multi_boss_zone_stands_both_gates(monkeypatch):
    """Pass 5: zone 1-7 stands Piedmon mid-zone and Apocalymon at the gate --
    both must be fought, in order, and only the SECOND ends the zone."""
    from tuipet import adventure as amod
    from tuipet.adventure import Adventure
    from tuipet.pet import Pet
    monkeypatch.setattr(amod.random, "random", lambda: 0.99)
    p = Pet(num=100, stage="Adult", attribute="Vaccine")
    p.adv_map, p.adv_zone = 0, 6                   # map 1, zone 7
    adv = Adventure(p)
    assert len(adv.zone["bosses"]) == 2
    fought = []
    for _ in range(200):
        ev = adv.travel()
        if ev and ev[0] == "boss":
            fought.append(ev[1]["num"])
            res = adv.resolve(True, True, ev[1])
            if res:
                assert res == "map", "the second gate ends the MAP"
                break
        elif ev and ev[0] == "town":
            continue
    assert len(fought) == 2 and fought[0] != fought[1]
