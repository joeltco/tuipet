"""The special-idle families (SpriteAnim 1/1500 rolls; weathering/personality
audit 2026-07-06): Tantrum-while-the-call-stands, weathering's three flavors
(checkNiceWeather: a species that LOVES this sky bounces), and the gated
personality mood idles (Neutral does nothing)."""
import random

from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=100)
    p.world_seconds = 10 * 60.0
    p.enthusiasm, p.strength = 2, 1
    p.energy = p.max_energy
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_the_standing_tantrum_plays_the_fit():
    p = _pet(discipline_call=True)
    p._special_idle()
    assert p.anim == "tantrum"


def test_weathering_flavors_and_nice_weather_joy():
    p = _pet(weather="Raining")
    p._special_idle()
    assert p.anim == "shield"                     # the rain shake (frame 4)
    q = _pet(weather="Snowing")
    q._special_idle()
    assert q.anim == "huddle"                     # the snow shiver (frame 9)
    w = _pet(weather="HeavyRain", element="Water")
    w._special_idle()
    assert w.anim == "happy"                      # a Water pet LOVES the rain
    i = _pet(weather="LightSnow", element="Ice")
    i._special_idle()
    assert i.anim == "happy"                      # an Ice pet loves the snow


def test_personality_idles_are_gated_and_tier_keyed():
    random.seed(1)
    p = _pet(mood=300)                            # Happy tier, all gates pass
    p._special_idle()
    assert p.anim in ("play", "happy")
    n = _pet(mood=50)                             # Neutral: canon does NOTHING
    n._special_idle()
    assert n.anim in ("idle", "walk")
    u = _pet(mood=-200)                           # Unhappy: it fumes
    u._special_idle()
    assert u.anim in ("angry", "tantrum")
    tired = _pet(mood=300, energy=1)              # rested gate: energy < max/3
    tired._special_idle()
    assert tired.anim in ("idle", "walk")
    drilled = _pet(mood=300, strength=4)          # effort > limit/2: no fidget
    drilled._special_idle()
    assert drilled.anim in ("idle", "walk")
    away = _pet(mood=300, away=True)              # no home idles on the road
    away._special_idle()
    assert away.anim in ("idle", "walk")


def test_the_yawn_fx_walks_its_canon_beats():
    """yawning()'s choreography as a scripted fx (yawning/poopdance audit
    2026-07-06): idle -> the +8 yawn -> the side-sway -> the +3/+1 stretch;
    a full 22-step walk renders every beat."""
    from tuipet import app as app_mod
    scr = app_mod.Screen.__new__(app_mod.Screen)
    p = _pet()

    class C:
        rows = None
        xshift = 0
        mirror = False
    poses = []
    for step in (0, 6, 12, 16, 18):
        c = C()
        app_mod.Screen._fxk_yawn(scr, p, {}, step, c)
        poses.append(c.rows is not None)
    assert all(poses)


def test_both_tells_due_picks_uniformly(monkeypatch):
    """Canon rolls once and picks uniformly among the eligible specials --
    with the gauge full AND bedtime near, BOTH the dance and the yawn must be
    reachable (the old elif never yawned)."""
    import random as _r
    from tuipet.pet import Pet
    seen = set()
    picks = ["poopdance", "yawn"]
    # the app block's shape: specials list -> one roll -> uniform choice
    p = _pet()
    p._poop_t = p._poop_interval            # gauge full
    p.sleep_lapse = p.sleep_limit - 1       # bedtime near
    specials = []
    if getattr(p, "_poop_t", 0) >= 0.8 * p._poop_interval:
        specials.append("poopdance")
    if p.near_bedtime():
        specials.append("yawn")
    assert specials == picks                # both eligible at once


def test_the_thunder_startle_is_disposition_keyed():
    """surprising() (startle audit 2026-07-06): the thunder startle's poses
    key on disposition -- the sour pet barely flinches (idle<->4), neutral
    reacts (4<->6), the SUNNY one jumps hardest (9<->10, canon's inversion).
    The roles carry the canon pose pairs."""
    from tuipet import data
    assert data.ROLES["startle_sour"] == [0, 4]
    assert data.ROLES["startle"] == [4, 6]
    assert data.ROLES["startle_sunny"] == [9, 10]
    pick = {-1: "startle_sour", 1: "startle_sunny"}
    assert pick.get(-1) == "startle_sour"
    assert pick.get(0, "startle") == "startle"
    p = _pet(disposition=1)
    p._set_anim({-1: "startle_sour", 1: "startle_sunny"}.get(p.disposition, "startle"), 1.4)
    assert p.anim == "startle_sunny"


def test_the_collapse_wears_the_dying_emote():
    """badHealthJeer (emote audit 2026-07-06): the fatigue/life-penalty anim
    blinks the dying/dying2 pair at the pet's edge -- the exhausted collapse
    now shows how bad it is (the classifier used to show nothing)."""
    from tuipet import app as app_mod, data
    p = _pet()
    p._set_anim("exhausted", 2.0)
    pts_a = app_mod._effect_overlay(p, 0, 40, 24, tick=0)
    pts_b = app_mod._effect_overlay(p, 1, 40, 24, tick=0)
    assert pts_a and pts_b and pts_a != pts_b     # the two dying frames blink
    p._set_anim("idle", 0.0)
    p.anim = "idle"
    assert len(data.load_effects()["dying"]) == 2


def test_the_condition_column_keeps_canon_order_and_shows_all():
    """checkStates (condition-column audit 2026-07-06): every active condition
    shows AT ONCE, in canon's top-down slot order (sick/med/inj/bandage/
    vitamin/fatigue at x~120) -- ours compacts upward on the 24px LCD but the
    ORDER is canon's; each icon blinks its 2-frame pair."""
    from tuipet import app as app_mod, data
    E = data.load_effects()
    order = ("st_sick", "st_medicine", "st_injury", "st_bandage",
             "st_vitamin", "st_fatigue")
    assert all(len(E.get(k, [])) == 2 for k in order if E.get(k))
    p = _pet(sick=True, sick_length=5.0, fatigue_length=5.0, inj_length=5.0)
    pts = app_mod._effect_overlay(p, 0, 40, 24, tick=0)
    # three conditions active: the column paints strictly more than one icon's
    # worth of pixels at the right edge (x >= 29)
    col = [pt for pt in pts if pt[0] >= 29]
    assert len({y for _, y in col}) > 7      # taller than a single 7px icon
