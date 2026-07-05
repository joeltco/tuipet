"""Regression pins for the 2026-07 full-codebase audit fixes."""
import json
import random

from tuipet.pet import Pet, DAY_LENGTH
from tuipet import persistence, data
from tuipet.adventure import Adventure
from tuipet.battle import Battle


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_int_dict_keys_survive_the_save_round_trip():
    p = _pet()
    p.habitat_record = {2: 500, 0: 100}
    p.trophies_won = {7: "Spring"}
    d = json.loads(json.dumps(persistence.to_save_dict(p)))
    p2, _ = persistence.pet_from_save(d, catch_up=False)
    assert list(p2.habitat_record) == [2, 0]
    assert p2.major_habitat() == 2                    # int again: evolution gates work
    assert p2.trophies_won.get(7) == "Spring"         # prelim chains survive restarts


def test_long_horizon_clocks_persist():
    p = _pet()
    p._starve_t, p._poop_t, p._filth_t = 40000.0, 1200.0, 900.0
    p._lights_t = float("-inf")                       # the once-per-night latch
    d = json.loads(json.dumps(persistence.to_save_dict(p)))
    p2, _ = persistence.pet_from_save(d, catch_up=False)
    assert p2._starve_t == 40000.0                    # no more starvation amnesty on restart
    assert p2._poop_t == 1200.0 and p2._filth_t == 900.0
    assert p2._lights_t == float("-inf")


def test_fleeing_the_gate_boss_cannot_skip_the_zone():
    random.seed(0)
    p = _pet()
    p.sleep_limit = 9e9
    adv = Adventure(p)
    for _ in range(300):
        ev = adv.travel()
        if ev and ev[0] == "boss":
            break
    boss = adv._boss
    adv.flee(boss, was_boss=True)                     # canEscape knockback
    assert adv.location < adv._boss_loc(boss)
    for _ in range(300):
        ev = adv.travel()
        if ev and ev[0] in ("boss", "zone"):
            break
    assert ev[0] == "boss"                            # the gate holds


def test_staples_stay_out_of_gift_and_discover_pools():
    meat = data.consumable_by_key("f:0")
    assert meat["can_inc"] is False                   # foods.csv CanInc, not CanIncUses
    p = _pet(mood=300)
    for _ in range(40):
        key = p._pick_gift()
        assert key != "f:0"


def test_battle_style_is_baked_per_battle():
    p = _pet()
    p.free_style = True
    b = Battle(p, {"num": 4, "name": "X", "stage": "Champion", "vaccine": 5,
                   "data_power": 5, "virus": 5, "hp": 8, "bits": (0, 0)})
    p.free_style = False                              # mid-fight toggle
    assert b.free_style is True                       # the battle keeps its bake
    o0 = p.obedience
    p.record_battle(False, None, free_style=b.free_style)
    assert p.obedience == o0 - 1                      # Free forgoes the orders +1


def test_discover_fires_at_stride_compounded_rates():
    random.seed(4)
    p = _pet(mood=24800 - 500)                        # seed ~200 after obedience+mood
    p.sleep_limit = 9e9
    adv = Adventure(p)
    hits = 0
    for _ in range(30):
        ev = adv.travel()
        if ev and ev[0] == "discover":
            hits += 1
        if ev and ev[0] in ("encounter", "boss"):
            adv.boss_pending = False
    assert hits >= 1                                  # 2250 fires/action, not 9


def test_death_checks_apply_while_asleep():
    p = _pet()
    p.sleep_lapse = p.sleep_limit
    p.tick(1.0)
    assert p.asleep
    p.care_mistakes = 20
    p.tick(1.0)
    assert p.dead                                     # the mistake cap doesn't wait for morning


def test_nap_pays_down_bedtime_pressure():
    # canon re-audit 2026-07 (sleepDecay): a nap REDUCES sleepLapse (the old
    # '+=' pin encoded an inversion), and a nap held past ChangeNapToSleepMinutes
    # becomes the night: pressure clears and the nap flag drops
    p = _pet()
    p.sleep_lapse = 500.0
    p.lights = False
    p.tick(1.0)                                       # nap starts
    assert p.asleep and p.nap
    lapse0 = p.sleep_lapse
    p.tick(1.0)
    assert p.sleep_lapse < lapse0                     # bedtime RECEDES while napping
    from tuipet.pet import CHANGE_NAP_TO_SLEEP
    p.awake_limit = 9e9                               # hold the nap past the threshold
    for _ in range(CHANGE_NAP_TO_SLEEP + 20):
        p.tick(1.0)
        if not p.nap:
            break
    assert p.asleep and not p.nap                     # the long nap BECAME the night
    assert p.sleep_lapse == 0.0


def test_sleeping_pet_battle_disturbs_before_refusing():
    p = _pet(obedience=-500)                          # would refuse anything
    p.sleep_lapse = p.sleep_limit
    p.tick(1.0)
    assert p.asleep
    msg = p.can_battle()
    assert not p.refused                              # asleep gate FIRST: no refusal roll
    assert "sleep" in msg.lower() or "awake" in msg.lower()


def test_wolf_down_decided_before_the_meal():
    p = _pet(hunger=0)
    meat = next(f for f in data.load_foods() if f["name"] == "Meat")
    p.feed(meat)
    assert p._last_meal_starving is True              # pre-meal hunger, not post


# ---- polish design decisions (2026-07-04) ------------------------------------

def test_dark_room_stays_dark_through_fx():
    import tuipet.app as app
    seen = {}
    real = app.render_screen
    def spy(rows, cols, r, on, bg, **kw):
        seen.update(bg=bg, bgimg=kw.get("bgimg"))
        return real(rows, cols, r, on, bg, **kw)
    app.render_screen = spy
    try:
        class S(app.Screen):
            def __init__(self):
                self.fx = None; self.frame_i = 0; self.roamer = None
            def update(self, t): pass
        p = _pet()
        p.lights = False
        s = S()
        s.start_fx("eat", icon="f:8", pet=p)
        s.fx["step"] = 5
        s._paint_fx(p)
        assert seen["bg"] == "#000000" and seen["bgimg"] is None
    finally:
        app.render_screen = real


def test_attention_predicate_is_shared():
    p = _pet()
    assert not p.needs_attention()
    p.sick = True
    assert p.needs_attention()          # the '!' bubble now flags sickness too
    p.sick = False
    p.scold_flag = True
    assert p.needs_attention()          # ...and misbehavior


def test_nap_mood_farm_is_closed():
    p = _pet()
    p.world_seconds = 10 * 60.0
    m0 = p.mood
    for _ in range(6):                  # toggle lights off/on six times fast
        p.lights = False
        p.tick(1.0)                     # nap starts
        p.toggle_lights()               # lights on wakes it
    assert p.mood - m0 <= 10 + 6        # ONE +10 bonus (a few wake nudges aside), not +60


def test_precipitation_lands_on_the_terrain_band():
    """Weather audit 2026-07-05 (Joel: stop rain/snow at random spots a bit
    past halfway 'so it looks like its landing on the actual ground'): each
    particle owns a ground line in rows 13..20 of 24; rain soaks in on
    landing, snow RESTS a few frames, then both recycle from the sky."""
    from tuipet.app import _weather_overlay
    for w in ("Raining", "HeavyRain", "Snowing", "HeavySnow"):
        deepest = 0
        for f in range(200):
            for _x, y in _weather_overlay(w, f, 40, 24):
                deepest = max(deepest, y)
        assert deepest <= 20, w                    # never through the floor
        assert deepest >= 18, w                    # ...but the band is used
    prev = set(_weather_overlay("Snowing", 50, 40, 24))
    cur = set(_weather_overlay("Snowing", 51, 40, 24))
    assert {p for p in prev & cur if p[1] >= 13}   # flakes sit on the ground
