"""THE BODY TELLS — poopdance + yawn (2026-07-23, Joel: "do the
poopdance and yawn animations too").

Both fx shipped fully painted in arenafx and NOTHING ever fired them.
Each names its own trigger in its docstring, and those are the numbers
used here: poopDance rolls while the need APPROACHES (canon dances on a
full gauge, but tuipet fires the poop the instant it fills, so the tell
has to come earlier), and yawning() is the tell that bedtime NEARS.

They are PRESENTATION: the sim posts them to the `idle_fx` mailbox --
the assist_event pattern -- and the app plays them if nothing else is
on screen.
"""
from tuipet.pet import Pet
from tuipet.petbase import POOPDANCE_AT, YAWN_AT


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p._set_energy(p.max_energy)
    p.enthusiasm = 0
    p._poop_t = 0.0
    p.awake_lapse = 0.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_a_building_need_dances():
    p = _pet()
    p._poop_t = p._poop_interval * (POOPDANCE_AT + 0.05)
    p._special_idle()
    assert p.idle_fx == "poopdance"


def test_an_empty_gauge_does_not_dance():
    p = _pet()
    p._poop_t = p._poop_interval * (POOPDANCE_AT - 0.2)
    p._special_idle()
    assert getattr(p, "idle_fx", None) != "poopdance"


def test_a_nearing_bedtime_yawns():
    p = _pet()
    p.awake_lapse = p.awake_limit * (YAWN_AT + 0.05)
    p._special_idle()
    assert p.idle_fx == "yawn"


def test_a_drained_pet_still_yawns_at_bedtime():
    """The tells sit ABOVE the personality gate on purpose: that gate
    wants a rested pet (energy >= max/3), but a pet running on empty at
    bedtime is exactly when a yawn belongs."""
    p = _pet()
    p._set_energy(1)
    p.awake_lapse = p.awake_limit * (YAWN_AT + 0.05)
    p._special_idle()
    assert p.idle_fx == "yawn"


def test_a_fresh_pet_tells_nothing_and_keeps_its_mood_idles():
    """Neither tell fires, so the personality families still run -- the
    tells must not swallow the mood idles."""
    p = _pet()
    p._special_idle()
    assert getattr(p, "idle_fx", None) is None


def test_the_tell_is_transient_and_never_saved():
    """Presentation only: `idle_fx` is a runtime attribute like
    assist_event, NOT a dataclass field -- it must never reach a save."""
    from dataclasses import fields
    assert "idle_fx" not in {f.name for f in fields(Pet)}


def test_the_road_tells_nothing():
    p = _pet(away=True)
    p._poop_t = p._poop_interval
    p.awake_lapse = p.awake_limit
    p._special_idle()
    assert getattr(p, "idle_fx", None) is None


def test_both_fx_are_real_painted_shows():
    """Guard against wiring a name the painter cannot run."""
    from tuipet.arenafx import FxMixin
    for kind in ("poopdance", "yawn"):
        assert hasattr(FxMixin, f"_fxk_{kind}"), kind
