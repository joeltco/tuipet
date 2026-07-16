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


def test_the_habitat_gate_reads_the_current_home(monkeypatch):
    num, hab = _habitat_target()
    req = data.load_requirements()[num]
    p = _pet()
    p.habitat = hab                                   # standing in the right home NOW
    monkeypatch.setattr(Pet, "major_habitat", lambda self: -99, raising=False)
    gates_pass = evolution.check.__wrapped__ if hasattr(evolution.check, "__wrapped__") else None
    # drive the gate through the report row (same predicate, no probability roll)
    rows = dict((label, ok) for ok, label in evolution.requirement_report(p, num))
    hname = (data.load_habitats().get(hab) or {}).get("name", f"#{hab}")
    assert rows.get(f"living in {hname}") is True     # current home passes...
    p.habitat = -1
    rows = dict((label, ok) for ok, label in evolution.requirement_report(p, num))
    assert rows.get(f"living in {hname}") is False    # ...even if the majority differed


def test_the_priority_shade_keys_on_the_major_habitat(monkeypatch):
    """getFulfilledReq's element/field compatibility shade uses getMajorHabitat
    -- a form that fits where the pet GREW UP outranks one that fits a
    day-trip home."""
    reqs = data.load_requirements()
    _, by = data.load_sprites()
    # a target whose element is compatible somewhere: find any habitat listing
    # a compat element, then a target form of that element
    hid, hab = next((h, rec) for h, rec in data.load_habitats().items()
                    if rec["compat_elements"] and rec["compat_fields"])
    num = next(n for n, r in reqs.items()
               if r.get("element") in hab["compat_elements"]
               and r.get("field") in hab["compat_fields"] and n in by)
    p = _pet()
    monkeypatch.setattr(Pet, "major_habitat", lambda self: hid, raising=False)
    p.habitat = -1                                    # the CURRENT home is nowhere
    grown_there = evolution.fulfilled(p, num)
    monkeypatch.setattr(Pet, "major_habitat", lambda self: -1, raising=False)
    drifted = evolution.fulfilled(p, num)
    assert grown_there > drifted                      # the childhood home shades the pick


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
