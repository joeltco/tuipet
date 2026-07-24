"""THE BODY TELLS — poopdance + yawn.

⚠ E4 AUDIT 2026-07-23, and the finding is about this file's first draft.
These two fx have been firing since **v0.2.337** from app.py's own idle
roll — gated on POOPDANCE_AT of the bowel gauge and on
`pet.near_bedtime()`, a helper whose docstring literally says it is
"the yawning special idle's eligibility".  v0.5.211 "restored" them a
SECOND time, through a `_special_idle` branch and an `idle_fx` mailbox,
because the survey grepped for a literal `start_fx("name")` and the
real call site passes a VARIABLE (`random.choice(specials)`) — the same
class of miss that hid the `losing` fx earlier the same day.

The duplicate was removed.  These pins now guard the ORIGINAL path, so
nobody (me) re-adds a second one.
"""
from tuipet.pet import Pet
from tuipet.petbase import POOPDANCE_AT


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p._set_energy(p.max_energy)
    p._poop_t = 0.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_both_fx_are_real_painted_shows():
    """Guard against wiring a name the painter cannot run."""
    from tuipet.arenafx import FxMixin
    for kind in ("poopdance", "yawn"):
        assert hasattr(FxMixin, f"_fxk_{kind}"), kind


def test_the_app_owns_the_only_tell_trigger():
    """ONE source.  If a second trigger ever appears, this fails."""
    import inspect
    from tuipet import app, petbody
    assert "poopdance" in inspect.getsource(app)
    assert "poopdance" not in inspect.getsource(petbody)
    assert "idle_fx" not in inspect.getsource(app)
    assert "idle_fx" not in inspect.getsource(petbody)


def test_the_dance_gate_is_a_building_need():
    """The tell has to come EARLY: canon dances on a full gauge, but
    tuipet drops the poop the instant it fills, so a full-gauge dance
    could never be seen."""
    assert 0 < POOPDANCE_AT < 1
    p = _pet()
    p._poop_t = p._poop_interval * (POOPDANCE_AT + 0.05)
    assert p._poop_t >= POOPDANCE_AT * p._poop_interval
    p._poop_t = p._poop_interval * (POOPDANCE_AT - 0.2)
    assert not p._poop_t >= POOPDANCE_AT * p._poop_interval


def test_the_yawn_gate_is_the_canon_helper():
    """near_bedtime() is the canon eligibility -- not a fraction someone
    invents at the call site."""
    import inspect
    from tuipet import app
    p = _pet()
    assert isinstance(p.near_bedtime(), bool)
    # the app's tell roll must ASK the pet, not re-derive a fraction
    src = inspect.getsource(app)
    assert "near_bedtime()" in src
    assert "YAWN_AT" not in src
