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
