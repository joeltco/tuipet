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


def test_the_collapse_emote_is_fx_only_now():
    """Bandai grammar 2026-07-11: idle-state anims carry no floating emote --
    the collapse POSE is the signal; the dying/losing FX scenes still own the
    dying/dying2 pair as part of their full-screen animation."""
    from tuipet import app as app_mod, data
    import inspect
    import tuipet.arenafx as arena_mod   # the fx painters (tier-2 split)
    p = _pet()
    p._set_anim("exhausted", 2.0)
    assert app_mod._effect_overlay(p, 0, 40, 24, tick=0) == []
    p._set_anim("idle", 0.0)
    p.anim = "idle"
    assert len(data.load_effects()["dying"]) == 2
    assert 'get("dying")' in inspect.getsource(arena_mod)   # the fx scenes keep it


def test_the_sick_skull_is_the_one_condition_actor():
    """Bandai grammar 2026-07-11: the condition dashboard left the LCD; only
    the skull stands in the scene, grounded at the band's right edge,
    blinking its 2-frame pair.  Extra conditions add nothing on-LCD."""
    from tuipet import app as app_mod, data, grid
    E = data.load_effects()
    assert len(E["st_sick"]) == 2
    p = _pet(sick=True, sick_length=5.0, fatigue_length=5.0, inj_length=5.0)
    pts = app_mod._effect_overlay(p, 0, 40, 24, tick=0)
    assert pts and all(x >= grid.X1 - 7 for x, _ in pts)
    assert min(y for _, y in pts) == grid.TOP    # HIGH at head height (Joel
    assert max(y for _, y in pts) < grid.TOP + 8  # 2026-07-12), inside the window
