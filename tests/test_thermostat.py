"""The thermostat (system rebuild 2026-07-14) — canon PhysicalState.setTempGoal
/ checkTemp: the player heats or cools the ROOM toward a goal (1°/game-min),
the goal clears on arrival, and the weather takes back over.  This — not the
futon — is the answer to a cold pet (Joel: "futons aren't supposed to be the
go-to if the mon is cold").
"""
from tuipet.habitatscreen import HabitatPanel
from tuipet.pet import Pet


def _pet():
    """Hard Disk (weather_chance=0): _update_weather's own target is the
    deterministic ideal midpoint, so goal-vs-weather drift is unambiguous."""
    p = Pet(num=-1, stage="Rookie", obedience=500)
    p.habitat = p.home_habitat = 0
    assert p.habitat_obj()["weather_chance"] <= 0
    return p


def test_set_temp_goal_guards_like_canon():
    p = _pet()
    p.set_temp_goal(62)
    assert p.temp_goal == 62 and p.heat_on()
    p.set_temp_goal(999)                       # canon setTempGoal IGNORES out-of-range
    assert p.temp_goal == 62
    p.set_temp_goal(-5)
    assert p.temp_goal == 62
    p.clear_temp_goal()
    assert not p.heat_on()


def test_goal_overrides_weather_and_clears_on_arrival():
    p = _pet()
    p.temp = 20.0                              # freezing (<= 32)
    assert p.is_freezing()
    p.set_temp_goal(60)
    p._update_weather(30)                      # 30 game-min at 1°/min
    assert p.temp == 50.0 and p.heat_on()
    p._update_weather(30)
    assert p.temp == 60.0                      # arrived...
    p._update_weather(1)
    assert not p.heat_on(), "the goal clears on arrival (canon: tempGoal=101)"
    assert not p.is_freezing()


def test_goal_cools_too():
    p = _pet()
    p.temp = 95.0
    p.set_temp_goal(50)
    p._update_weather(45)
    assert p.temp == 50.0


def test_futon_still_pins_over_an_armed_thermostat():
    """pauseTemp gates the WHOLE lapse (canon checkEveryTemp) — goal included:
    a tucked-in pet's room does not heat until the futon ends."""
    from tuipet import data
    eid = next((i for i, e in data.load_care_effects().items() if e["pause_temp"]), None)
    if eid is None:
        return
    p = _pet()
    p.temp = 20.0
    p.set_temp_goal(60)
    p.effect_id, p.effect_t = eid, 9999.0
    p._update_weather(60)
    assert p.temp == 20.0
    p.effect_id, p.effect_t = -1, 0.0
    p._update_weather(10)
    assert p.temp == 30.0                      # the held goal resumes driving


def test_temp_goal_persists():
    from tuipet import persistence
    p = _pet()
    p.set_temp_goal(62)
    persistence.save(p)
    q, _ = persistence.load(catch_up=False)
    assert q.temp_goal == 62.0


def test_habitat_panel_heat_keys():
    p = _pet()
    p.temp = 40.0
    pan = HabitatPanel(p)
    assert "° now" in pan.msg and "+/- heat" in pan.msg    # the room report
    pan.key("+")                               # first nudge arms FROM current temp
    assert p.temp_goal == 45.0
    pan.key("plus")                            # textual key name form
    assert p.temp_goal == 50.0
    assert "heat→50°" in pan.msg
    pan.key("-")
    assert p.temp_goal == 45.0
    pan.key("0")
    assert not p.heat_on() and "off" in pan.msg
    pan.key("minus")                           # arming DOWNWARD works too (cooling)
    assert p.temp_goal == 35.0


def test_hud_shows_the_heading_arrow():
    from tuipet.app import _temp_str
    p = _pet()
    p.temp = 48.0
    assert _temp_str(p) == "48°"
    p.set_temp_goal(62)
    assert _temp_str(p) == "48→62°"


# ---------------------------------------------------------------------------
# Weather audit vs the decompile (2026-07-15)
# ---------------------------------------------------------------------------

def test_seasons_run_thirteen_days_on_a_52_day_year():
    """config.csv FirstSpring/Summer/Fall/WinterDay = 0/13/26/39 and setDay
    wraps past MaxFastClockDays 51 — the pre-audit day%4 rotated 13x fast."""
    from tuipet.weather import season_for_day
    assert [season_for_day(d) for d in (0, 12, 13, 25, 26, 38, 39, 51)] == \
        ["Spring", "Spring", "Summer", "Summer", "Fall", "Fall", "Winter", "Winter"]
    assert season_for_day(52) == "Spring"      # the year wraps


def test_arrival_transitions_the_sky_instead_of_carrying_it():
    """PhysicalState.transitionWeather: a HeavyRain sky arrives at the new
    home as Raining (eased one step), never verbatim; Clear arrives Clear;
    a climate-controlled home is always Clear."""
    from tuipet.weather import transition_weather
    p = _pet()
    hab = {"weather_chance": 7, "weather_change": 10,
           "precip_mod": {"Spring": 0, "Summer": 0, "Fall": 0, "Winter": 0},
           "cloud_mod": 0}
    assert transition_weather("HeavyRain", hab, "Spring", 50) == "Raining"
    assert transition_weather("HeavySnow", hab, "Spring", 20) == "Snowing"
    assert transition_weather("Raining", hab, "Spring", 50) in ("Drizzling", "HeavyRain")
    assert transition_weather("LightSnow", hab, "Spring", 20) in ("Snowing", "Cloudy")
    assert transition_weather("Clear", hab, "Spring", 50) == "Clear"
    assert transition_weather("HeavyRain", {"weather_chance": 0}, "Spring", 50) == "Clear"
    # and the pet-level hook: moving house never keeps the old sky heavy
    p.weather = "HeavyRain"
    p._arrive_weather()                        # Hard Disk: climate-controlled
    assert p.weather == "Clear"


def test_futon_snaps_to_the_comfort_midpoint():
    """changeToPrefTemp restored to canon (Joel 2026-07-15): USING the Futon
    tucks the room to the ideal midpoint, then PauseTemp holds it there."""
    from tuipet import data
    _, items = data._load_consumables()
    key = next((f"i:{k}" for k, e in items.items() if e.get("pref_temp")), None)
    if key is None:
        import pytest
        pytest.skip("no ChangeToPrefTemp item in the data")
    p = _pet()
    p.temp = 5.0                               # freezing under a cold snap
    p._fall_asleep()                           # the futon is a SLEEPER's tuck-in
    p.add_item(key)                            # (checkMaxHoursBeforeSleep gate)
    p.use_item(key)
    lo, hi = p.ideal_temp
    assert p.temp == (lo + hi) / 2, "the futon tucks the room comfy (canon)"
    assert not p.is_freezing()
    if p.effect_id >= 0:                       # ...and PauseTemp holds it
        p._update_weather(60)
        assert p.temp == (lo + hi) / 2


# ---------------------------------------------------------------------------
# Sleep audit vs the decompile (2026-07-15)
# ---------------------------------------------------------------------------

def _futon_key_and_eid():
    from tuipet import data
    _, items = data._load_consumables()
    k, e = next(((f"i:{k}", e) for k, e in items.items()
                 if e.get("max_hours_sleep", -1) != -1), (None, None))
    return k, e


def test_futon_makes_the_night_shorter():
    """Canon sleep(): awakeLimit divides by energyGain + getEffectEnergyGain
    -- the Futon's 1;60 energy rate joins the divisor, so a tucked-in pet
    sizes a SHORTER night (deficit/4, not /3)."""
    from tuipet import data
    eid = next((i for i, e in data.load_care_effects().items()
                if e["energy"][0]), None)
    if eid is None:
        return
    p = _pet()
    p.energy = 0
    p._fall_asleep()
    plain = p.awake_limit                      # ceil(deficit/3)*60, clamped
    p.asleep = False
    p.effect_id, p.effect_t = eid, 9999.0
    p._fall_asleep()
    assert p.awake_limit < plain               # the futon-shortened night
    import math as m
    gain = getattr(p, "_sleep_energy_gain", 3)
    exp = m.ceil(p.max_energy / (gain + 1)) * 60.0
    assert p.awake_limit == max(360.0, min(900.0, exp))


def test_futon_is_bedtime_only():
    """checkMaxHoursBeforeSleep: an AWAKE pet nowhere near nod-off cannot lay
    out the futon -- the interaction is blocked BEFORE consumption (canon
    gates the click), so nothing is spent and no effect starts."""
    key, e = _futon_key_and_eid()
    if key is None:
        return
    p = _pet()
    p.sleep_lapse, p.sleep_limit = 0.0, 900.0  # a full day from nod-off
    p.temp = 5.0
    p.add_item(key)
    msg = p.use_item(key)
    assert "bedtime" in msg.lower()
    assert p.inventory.get(key) == 1           # not consumed
    assert p.effect_id < 0 and p.temp == 5.0   # no effect, no comfort snap
    p.sleep_lapse = p.sleep_limit - 1          # ...one game-minute from nod-off
    assert p._near_bedtime(e["max_hours_sleep"])
    msg = p.use_item(key)
    assert p.effect_id >= 0                    # now it lays out


def test_futon_does_not_reapply_while_active():
    """CareEffect.canApply (CanReapply=FALSE): a second futon on an active one
    is blocked up front -- nothing spent, the running timer untouched."""
    key, e = _futon_key_and_eid()
    if key is None:
        return
    p = _pet()
    p._fall_asleep()
    p.add_item(key)
    p.add_item(key)
    p.use_item(key)
    assert p.effect_id >= 0
    t0 = p.effect_t
    p.effect_t = t0 - 100.0                    # some of the night has passed
    msg = p.use_item(key)
    assert "tucked in" in msg
    assert p.inventory.get(key) == 1           # the second futon is not spent
    assert p.effect_t == t0 - 100.0            # the timer did not restart
