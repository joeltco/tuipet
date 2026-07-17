"""Evolution-system canon audit pins (2026-07-06) vs DVPet Evolution.java.

The checker was already a deep verbatim port (consume-once DNA forgiveness,
checkStatTotal's GreaterThan+1 total, fractional attribute ratios, priority-
seeded fulfilled with scaleRate vs the CURRENT form's thresholds, the
probability roll boosted by the care bonus + winRate x 0.4, deviation over
passing gates only).  Found three timer-off/scoring slips (the two habitat
ones are HISTORICAL now -- the habitat system left, BASIC VPET 2026-07-16),
and
the X-antibody score is Induced-only (the Natural arm over-scored)."""
from tuipet import data, evolution
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p.mood = 100
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# (the habitat gate + major-habitat priority-shade tests left with the
# habitat system -- BASIC VPET 2026-07-16: habitat_req gates were DROPPED so
# no form walls on a home nothing can move to)


def test_the_x_score_is_induced_only():
    reqs = data.load_requirements()
    _, by = data.load_sprites()
    nat = next((n for n, r in reqs.items()
                if r.get("xantibody") == "Natural" and n in by), None)
    if nat is None:
        import pytest
        pytest.skip("no Natural X rows")
    a = _pet(x_antibody="Permanent")
    b = _pet()
    # a Natural form scores the SAME with or without the antibody
    assert evolution.fulfilled(a, nat) == evolution.fulfilled(b, nat)
