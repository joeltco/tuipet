"""Evolution-system canon audit pins (2026-07-06) vs DVPet Evolution.java.

The checker was already a deep verbatim port (consume-once DNA forgiveness,
checkStatTotal's GreaterThan+1 total, fractional attribute ratios, priority-
seeded fulfilled with scaleRate vs the CURRENT form's thresholds, the
probability roll boosted by the care bonus + winRate x 0.4, deviation over
passing gates only).  Found three timer-off/scoring slips: the habitat GATE
compares the CURRENT habitat (ours used the majority -- the same misread the
mood gate once had), the fulfilled habitat-compatibility PRIORITY SHADE keys
on the MAJOR habitat (ours used the current -- the two were swapped), and
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


def _habitat_target():
    reqs = data.load_requirements()
    _, by = data.load_sprites()
    return next((n, r["habitat_req"]) for n, r in reqs.items()
                if r.get("habitat_req", -1) != -1 and n in by)




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
