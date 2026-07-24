"""Adventure rebuild — FINDS / investigate (phase 9, 2026-07-20).

Pins the loot roll: a marched step may spot a find from the zone's own loot
table (rand_items/rand_foods); the player digs it into the bag or walks on;
towns are safe rest, not scavenging (no finds).
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES
from tuipet.adventurescreen import AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _find_zone():
    return next(z for z in ZONES if z["find_keys"])


def _to_travelling(pan):
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.travelling:
            return


def _spot(pan):
    for _ in range(60):
        pan.anim()
        if pan._find is not None:
            return pan._find
    raise AssertionError("no find spotted")


def test_every_real_zone_has_a_loot_pool_of_named_consumables():
    from tuipet import shop
    for z in ZONES:
        assert z["find_keys"]                          # 26/26 have loot
        for k in z["find_keys"]:
            # CATALOG keys -- real, bag-renderable, use_item-usable loot
            assert shop.entry(k) and shop.entry(k)["name"]


# --- THE BIOME LOOT TABLE (item diversity audit 2026-07-23, Joel: "do it
# all").  The authored tables were per-SLOT (1-1 == 2-1 == 5-1): deserts,
# seafloors and mountains all dug the same Television.  Pools key on the
# BIOME now, the finals dig the rare tier, and the road finally feeds you.

def _by_mz(m, z):
    return next(x for x in ZONES if x["map"] == m and x["zone"] == z)


def test_find_pools_key_on_the_biome_not_the_slot():
    # the audit's own exhibit: Desert (5-2) vs Seafloor (2-2) vs
    # Mountains (1-2) -- slot-mates that used to share one pool
    pools = [tuple(_by_mz(*mz)["find_keys"]) for mz in ((5, 2), (2, 2), (1, 2))]
    assert len(set(pools)) == 3                    # all three dig differently
    # ...and SAME-biome zones share their BIOME BASE but no longer dig
    # identically: each carries its own exclusive signature now (D4,
    # 2026-07-24 -- eight zones shared the factorynight scene and dug the
    # same loot, a third of the map reading alike).
    a, b = _by_mz(1, 2), _by_mz(2, 3)                  # both Mountains
    assert a["find_keys"] != b["find_keys"]
    assert a["signature"] != b["signature"]
    shared = set(a["find_keys"]) & set(b["find_keys"])
    assert len(shared) >= 3, "the biome base should still bind them"


def test_the_final_zone_of_every_map_digs_the_rare_tier():
    """The endgame used to dig exactly ONE item (the chip)."""
    from tuipet.adventure import FINAL_ZONE_FINDS, _ROAD_KEYS
    for m in sorted({z["map"] for z in ZONES}):
        last = max(z["zone"] for z in ZONES if z["map"] == m)
        pool = _by_mz(m, last)["find_keys"]
        assert set(FINAL_ZONE_FINDS) <= set(pool), (m, last)
        assert set(_ROAD_KEYS) <= set(pool)
    assert "x_antibody" in FINAL_ZONE_FINDS        # the tier is genuinely rare


def test_the_road_feeds_you_and_carries_its_tools():
    """Audit F3: 18 items were never finds -- including every food except
    tuna and candy.  Fish by the water now, and the road items ride
    every pool."""
    from tuipet import shop
    from tuipet.adventure import _ROAD_KEYS
    findable = set()
    for z in ZONES:
        assert set(_ROAD_KEYS) <= set(z["find_keys"]), z["name"]
        findable.update(z["find_keys"])
    foods = {k for k in findable if shop.CATALOG[k][3] == "Food"}
    assert "fish" in foods and len(foods) >= 5
    seafloor = next(z for z in ZONES if "Seafloor" in z["name"])
    assert "fish" in seafloor["find_keys"]


def test_a_find_comes_from_the_zone_pool_after_the_step(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    z = _find_zone()
    a = Adventure(_pet(), zone=z)
    r = a.travel()
    assert isinstance(r, tuple) and r[0] == "find"
    assert r[1] in z["find_keys"]                      # from THIS zone's loot
    assert a.loc == 1                                  # the leg advanced; the find is a bonus


def test_towns_have_no_finds(monkeypatch):
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    z = _find_zone()
    a = Adventure(_pet(), zone=z)
    a.loc = z["town_legs"][0][0]
    assert a._in_town(a.loc)
    assert a._roll_find() is None                      # resting ground, not loot


def test_digging_a_find_drops_it_in_the_bag(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    p = _pet()
    pan = AdventurePanel(p, zone=_find_zone())
    _to_travelling(pan)
    key = _spot(pan)
    assert "glint" in pan.strip().lower()              # the dig/pass prompt
    before = p.inventory.get(key, 0)
    pan.key("enter")                                   # dig
    assert p.inventory.get(key, 0) == before + 1       # in the bag AT ONCE --
    #                                                    the beats that follow
    #                                                    are pure presentation
    assert pan._find is None and pan._scene is not None


def test_the_discover_sequence_plays_out_and_resumes_the_march(monkeypatch):
    """The restored old-build investigateLeft playbook: ENTER on a glint walks
    the mon OUT to the left goal, digs under suspense dots, unseals the "Dug
    up X!" verdict (with the reward chime) at the reveal, carries the find
    back, and puts the mon back on the road -- input locked throughout (no
    skips: own-game law)."""
    from tuipet.adventurescreen import (INV_WALK_T, INV_REVEAL_T, INV_END_T)
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    pan = AdventurePanel(_pet(), zone=_find_zone())
    _to_travelling(pan)
    _spot(pan)
    pan.key("enter")
    for _ in range(INV_WALK_T + 2):                    # the walk-out leg
        pan.anim()
        assert pan.text()
    assert pan._scene.get("meter") and pan._scene["grade"] is None
    m = pan._scene["meter"]
    m["bar"] = (m["lo"] + m["hi"]) // 2                # dead centre: a clean dig
    pan.key("space")                                   # lock the timed dig
    assert pan._scene["grade"] == "mega"
    saw_dots = saw_reveal = False
    chimed = False
    for _ in range(INV_END_T + 2):
        pan.anim()
        assert pan.text()                              # every beat renders clean
        if pan._scene is None:
            break
        t = pan._scene["t"]
        pan.key("escape")                              # locked: ESC must NOT go home
        assert pan._trans is None and pan._scene is not None
        if INV_WALK_T <= t < INV_REVEAL_T:
            saw_dots = saw_dots or "." in pan.strip()
        if t >= INV_REVEAL_T:
            saw_reveal = saw_reveal or "Dug up" in pan.strip()
        chimed = chimed or pan.sfx == "reward"
    assert saw_dots and saw_reveal and chimed
    assert pan._scene is None and pan.travelling       # back on the road


def _at_the_meter(monkeypatch, p=None):
    """Spot a glint, ENTER, walk out -- returns (pan, key) with the timed-dig
    meter live."""
    from tuipet.adventurescreen import INV_WALK_T
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    pan = AdventurePanel(p or _pet(), zone=_find_zone())
    _to_travelling(pan)
    key = _spot(pan)
    pan.key("enter")
    for _ in range(INV_WALK_T + 2):
        pan.anim()
    assert pan._scene.get("meter") and pan._scene["grade"] is None
    return pan, key


def test_the_timed_dig_meter_is_the_canon_bar(monkeypatch):
    """At the dig spot the CANON timing bar owns the window -- the same
    sprite and mega window as the training drill and the battle bell (one
    bar everywhere) -- with the dig hint on the strip."""
    from tuipet import menu, strikefx
    pan, _key = _at_the_meter(monkeypatch)
    m = pan._scene["meter"]
    calls = []
    real = menu.paint
    monkeypatch.setattr(menu, "paint",
                        lambda pl, *a, **k: (calls.append((pl, k)), real(pl, *a, **k))[1])
    assert pan.text()
    pl, kw = calls[-1]
    assert pl == []                                    # the bar owns the window
    assert kw.get("overlay") == strikefx.timing_bar(m["bar"], m["lo"], m["hi"])
    assert "dig" in pan.strip().lower()


def test_a_mega_lock_banks_a_second_copy(monkeypatch):
    """Inside the mega window the dig pays DOUBLE -- pinned through the
    verbatim battles>=999 never-whiff rule the drill and the bell share --
    and the reveal verdict says x2."""
    from tuipet.adventurescreen import INV_REVEAL_T
    p = _pet()
    p.battles = 999                                    # never whiffs (DSprite truth)
    pan, key = _at_the_meter(monkeypatch, p)
    before = p.inventory.get(key, 0)
    pan.key("space")
    assert pan._scene["grade"] == "mega"
    assert p.inventory.get(key, 0) == before + 1       # the bonus copy, at the lock
    assert pan.sfx == "confirm"
    for _ in range(INV_REVEAL_T):
        pan.anim()
        if "×2" in pan.strip():
            break
    assert "×2" in pan.strip()                         # the verdict says double


def test_a_wide_miss_still_keeps_the_find(monkeypatch):
    """The meter is pure upside: a wide miss scrapes the find out all the
    same -- one copy, nothing lost -- only the verdict (and the cancel
    thunk) says you blew the timing."""
    from tuipet.battlescreen import BAR_MAX
    pan, key = _at_the_meter(monkeypatch)
    p = pan.pet
    before = p.inventory.get(key, 0)
    m = pan._scene["meter"]
    m["bar"] = 0 if m["lo"] - 5 > 0 else BAR_MAX       # park it outside the bands
    pan.key("space")
    assert pan._scene["grade"] == "miss"
    assert p.inventory.get(key, 0) == before           # base copy from ENTER only
    assert "Scraped" in pan._find_msg and pan.sfx == "cancel"


def test_the_dig_meter_times_out_and_locks_itself(monkeypatch):
    """No press: the countdown burns out and the spade falls wherever the
    marker stands -- the sequence still plays to its end and the march
    resumes (the show never hangs on a missing hand)."""
    from tuipet.adventurescreen import DIG_METER_T, INV_END_T
    pan, _key = _at_the_meter(monkeypatch)
    for _ in range(DIG_METER_T + 2):
        pan.anim()
        assert pan.text()
    assert pan._scene["grade"] is not None             # it locked itself
    for _ in range(INV_END_T + 2):
        if pan._scene is None:
            break
        pan.anim()
    assert pan._scene is None and pan.travelling       # back on the road


def test_the_glint_wears_the_attention_bounce(monkeypatch):
    """Waiting at a glint, the mon plays the DiscoverCall attention bounce
    (happy poses) instead of a mute stand -- restored old-build behavior."""
    from tuipet import menu
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    pan = AdventurePanel(_pet(), zone=_find_zone())
    _to_travelling(pan)
    _spot(pan)
    calls = []
    real = menu.paint
    monkeypatch.setattr(menu, "paint",
                        lambda pl, *a, **k: (calls.append((pl, k)), real(pl, *a, **k))[1])
    pan.frame_i = 0
    pan.text()
    pan.frame_i = 6                                    # the other bounce beat
    pan.text()
    (pl1, k1), (pl2, k2) = calls
    assert pl1[0][0] != pl2[0][0]                      # pose flips (5 <-> 7)
    assert k1.get("overlay")                           # the "!" rides the beat


def test_passing_a_find_leaves_it_and_the_bag_alone(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 1.0)
    p = _pet()
    pan = AdventurePanel(p, zone=_find_zone())
    _to_travelling(pan)
    key = _spot(pan)
    before = p.inventory.get(key, 0)
    pan.key("space")                                   # walk on
    assert pan._find is None
    assert p.inventory.get(key, 0) == before           # nothing taken


def test_find_chance_zero_never_spots(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    a = Adventure(_pet(), zone=_find_zone())
    assert all(a.travel() != "find" for _ in range(a.total - 1))  # up to the boss gate
