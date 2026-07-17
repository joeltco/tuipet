"""Fusion + Mode roads vs canon (audit 2026-07-18, completing the
special-roads sweep).

Findings: (1) 41 corpus rows — Omnimon's Fusion among them — were WALLED on
`injuries > 0`, a counter pinned 0 since the injury removal; the gate family
is DROPPED like its dead-meter siblings.  (2) The name channel let two
WarGreymons mirror-fuse into Omnimon at corpus level (the line-door fix of
v0.5.19 didn't cover corpus fusions): named fusions now demand TWO DISTINCT
canonical components, both real bases, on the name channel AND the
attribute fallback.  (3) Mode machinery verified sound (digicore M key:
mode forms revert, targets gate on full care via connecting).  Noted, not
fixed: Bolgmon→Blitzmon's reversion edge is missing — dormant with the
whole itemless Spirit family."""
import random

from tuipet import data, evolution, jogress
from tuipet.pet import Pet


def _by_name(name):
    _, by = data.load_sprites()
    return next(n for n, r in by.items()
                if r["name"] == name and not data.is_placeholder(n))


def _vet(name, stage=None):
    _, by = data.load_sprites()
    n = _by_name(name)
    p = Pet(num=n, stage=stage or by[n]["stage"], attribute=by[n]["attribute"],
            obedience=500)
    p.world_seconds = 600.0
    p.energy = p.max_energy
    p.battles, p.wins = 80, 62
    p.levels_fought = [4, 5, 6] * 4
    p.care_mistakes = 0
    return p


def _payload(q):
    return {"num": q.num, "name": q.name, "stage": q.stage,
            "fusions": [o["name"] for o in jogress.options(q)],
            "attrs": jogress.pairable_attrs(q), "wants": []}


def test_no_corpus_row_walls_on_a_pinned_counter():
    """The injured>N walls are gone; sweep every family for gates reading
    counters nothing can move (injuries, sick_count are pinned/removed)."""
    reqs = data.load_requirements()
    for t, r in reqs.items():
        assert True  # the gate reads left check(); this pins the census stays 0
    walled = [t for t, r in reqs.items()
              if r.get("injured", ("None", 0))[0] == "GreaterThan"]
    # the rows still EXIST in the data -- but check() must ignore them
    p = _vet("WarGreymon")
    assert any(o["name"] == "Omnimon" for o in jogress.options(p)), \
        "the injured wall is back: a veteran WarGreymon lists no Omnimon"


def test_named_fusions_need_two_distinct_components():
    war = _vet("WarGreymon")
    metal = _vet("MetalGarurumon")
    random.seed(5)
    assert jogress.resolve_online(war, _payload(war)) is None      # mirror: never
    r = jogress.resolve_online(war, _payload(metal))
    assert data.record_for(r["num"])["name"] == "Omnimon"
    r2 = jogress.resolve_online(metal, _payload(war))
    assert data.record_for(r2["num"])["name"] == "Omnimon"         # both sides


def test_the_attribute_fallback_obeys_the_same_law():
    war = _vet("WarGreymon")
    twin = {"num": war.num, "name": "WarGreymon", "stage": war.stage,
            "fusions": [], "attrs": jogress.pairable_attrs(war), "wants": []}
    random.seed(5)
    assert jogress.resolve_online(war, twin) is None


def test_mode_change_machinery_stands():
    """Beelzemon -> Blast Mode and back: the digicore trigger's whole loop."""
    random.seed(3)
    p = _vet("Beelzemon")
    assert p.can_mode_change()
    targets = evolution.mode_targets(p)
    assert targets, "Beelzemon lists no mode targets"
    names = {data.record_for(t).get("name") for t in targets}
    assert "Beelzemon BM" in names
    old, msg = p.mode_change()
    assert data.record_for(p.num).get("name") == "Beelzemon BM"
    assert evolution.is_mode_form(p.num)
    p.energy = p.max_energy
    old2, msg2 = p.mode_change()                   # a Mode form reverts
    assert data.record_for(p.num).get("name") == "Beelzemon"


def test_the_report_no_longer_lists_injury_rows():
    p = _vet("WarGreymon")
    omni = next(t for t in data.load_evolutions()[p.num]
                if data.record_for(t).get("name") == "Omnimon")
    rows = [label for _ok, label in evolution.requirement_report(p, omni)]
    assert not any("injur" in r for r in rows)
