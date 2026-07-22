"""DSprite mortality (Joel 2026-07-22: "we gotta do it how dsprite does.
life bar must be a dvpet fkrgetten relic") -- the lifespan clock and its
whole LifeDec burn economy LEFT the game; death is the clone's per-minute
hazard roll again (v0.4.12 L440-454, tables verbatim):

    d = first matching DEATH_MISTAKES bracket
      + DEATH_SICK_P while sick
      + first matching DEATH_AGE bracket
    one roll per tick: random() < d * dt -> dead

Beneath the roll the discrete nets stand as before (NOT clock machinery):
the 20-mistake cap, Pen20 elder frailty (LINES_SPEC §5 contract) and the
12h starvation clock.  These pins hold the roll's shape, the immunity
window, and that NOTHING in the codebase burns or reads a lifespan."""
import pytest

from tuipet.pet import (Pet, DEATH_MISTAKES, DEATH_AGE, DEATH_SICK_P,
                        GERIATRIC_AGE_DAYS, AGE_DAY)


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _hazard(p):
    """The roll's d, recomputed the clone way -- the oracle for the pins."""
    d = 0.0
    for thresh, rate in DEATH_MISTAKES:
        if p.care_mistakes >= thresh:
            d += rate
            break
    if p.sick:
        d += DEATH_SICK_P
    for thresh, rate in DEATH_AGE:
        if p.age_days >= thresh:
            d += rate
            break
    return d


def test_the_immunity_window_holds():
    """The clone's promise: <5 mistakes, healthy, under age 15 = the roll
    CANNOT kill.  Even a forced 0.0 draw leaves d == 0 -> no roll at all."""
    import tuipet.petbody as body
    p = _pet(care_mistakes=4)
    assert _hazard(p) == 0.0
    real = body.random.random
    try:
        body.random.random = lambda: 0.0
        assert p._tick_mortality(1.0) is False
        assert not p.dead
    finally:
        body.random.random = real


@pytest.mark.parametrize("mistakes,want", [
    (4, 0.0), (5, 1.5e-5), (9, 1.5e-5), (10, 7.5e-5),
    (14, 7.5e-5), (15, 3.75e-4), (19, 3.75e-4), (20, 0.0015)])
def test_mistake_brackets_first_match_wins(mistakes, want):
    assert _hazard(_pet(care_mistakes=mistakes)) == want


@pytest.mark.parametrize("days,want", [
    (14, 0.0), (15, 3.75e-5), (19, 3.75e-5), (20, 1.5e-4),
    (24, 1.5e-4), (25, 3.75e-4), (40, 3.75e-4)])
def test_age_brackets_first_match_wins(days, want):
    p = _pet()
    p.age_seconds = days * AGE_DAY
    assert _hazard(p) == want


def test_the_whisper_folds_into_one_roll():
    """Sickness is a TERM of d, not a separate death (the clone shape): a
    sick elder with a record stacks all three."""
    p = _pet(care_mistakes=12, sick=True)
    p.age_seconds = 21 * AGE_DAY
    assert _hazard(p) == 7.5e-5 + DEATH_SICK_P + 1.5e-4


def test_roll_causes_read_the_dominant_reason(monkeypatch):
    import tuipet.petbody as body
    monkeypatch.setattr(body.random, "random", lambda: 0.0)
    old = _pet()
    old.age_seconds = 16 * AGE_DAY
    old._tick_mortality(1.0)
    assert old.dead and old.death_cause == "old age"
    slob = _pet(care_mistakes=8)
    slob._tick_mortality(1.0)
    assert slob.dead and slob.death_cause == "neglect"
    ill = _pet(sick=True)
    ill._tick_mortality(1.0)
    assert ill.dead and ill.death_cause == "sickness"


def test_the_discrete_nets_still_stand():
    """20 mistakes and Pen20 frailty (LINES_SPEC §5) are contract, not clock
    -- they survived the lifespan removal."""
    p = _pet(care_mistakes=20)
    assert p._tick_mortality(1.0) is True and p.death_cause == "neglect"
    q = _pet(stage="Mega", care_mistakes=5)
    q.stage_seconds = q.LATE_STAGE_WINDOW
    assert q._tick_mortality(1.0) is True and q.death_cause == "frailty"


def test_the_elder_line_is_age_alone():
    p = _pet()
    p.age_seconds = GERIATRIC_AGE_DAYS * AGE_DAY - 1
    assert not p.is_geriatric
    p.age_seconds = GERIATRIC_AGE_DAYS * AGE_DAY
    assert p.is_geriatric
    p.dead = True
    assert not p.is_geriatric                    # the dead are past age


def test_no_lifespan_survives_anywhere():
    """The relic sweep's guard: no field, no burn, no save leak, no display
    source.  A pre-port save carrying "lifespan" still loads (the key is
    simply dropped)."""
    import dataclasses
    from tuipet import persistence
    assert "lifespan" not in {f.name for f in dataclasses.fields(Pet)}
    assert not hasattr(_pet(), "_burn_life")
    d = persistence.to_save_dict(_pet())
    assert "lifespan" not in d
    old_save = dict(persistence.to_save_dict(_pet()))
    old_save["lifespan"] = 259200.0              # a pre-port save
    pet, _ = persistence.pet_from_save(old_save)
    assert pet is not None and not hasattr(pet, "lifespan")


def test_dead_system_lifedecs_stay_gone():
    """The whole LifeDec constant family left with the clock -- nothing may
    quietly re-import it."""
    import inspect
    from tuipet import petbody, petcare, pet as petmod, petbase
    src = "".join(inspect.getsource(m) for m in (petbody, petcare, petmod))
    for dead in ("LIFE_DEC", "_burn_life", "BONUS_LIFE_INC", "REVIVAL_LIFE",
                 "INSTANT_DEATH_GRACE", "life_penalty_note"):
        assert dead not in src, f"{dead} referenced again -- the clock is gone (2026-07-22)"
    assert not any(n.endswith("LIFE_DEC") for n in vars(petbase))
