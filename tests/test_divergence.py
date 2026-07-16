"""DNA divergence — the wild road ("ultimate v-pet" arc 2026-07-07).

The lines are the raising spine; the corpus graph reaches ~1,454 forms.
Divergence is the door: a strict-max charged Field at/over the stage
threshold steers evolution onto the graph's next-stage edge in that Field.
Unarmed pets must be bit-identical to before (the goldens enforce the rest).
"""

from tuipet import data, evolution, lines
from tuipet.pet import Pet


def mk(num, stage, lid="ver1", charge=None):
    p = Pet(num=num, stage=stage)
    p.line_id = lid
    for f, v in (charge or {}).items():
        p.dna_applied[f] = v
    return p


def test_unarmed_pets_never_diverge():
    assert evolution.divergence_target(mk(29, "Rookie")) is None
    # a TIE is not a strict max -- no steer
    tied = mk(29, "Rookie", charge={"DeepSaver": 8, "NatureSpirit": 8})
    assert evolution.divergence_target(tied) is None
    # the None bin is wasted DNA, never a road
    waste = mk(29, "Rookie", charge={"None": 20})
    assert evolution.divergence_target(waste) is None


def test_under_threshold_stays_on_chart():
    p = mk(29, "Rookie", charge={"DeepSaver": evolution.DIVERGE_NEED["Rookie"] - 1})
    assert evolution.divergence_target(p) is None


def test_armed_steer_picks_the_field_edge():
    """Agumon's graph: DeepSaver -> Coelamon (88), NightmareSoldier ->
    Ogremon (91) -- each the single plain edge in its Field."""
    p = mk(29, "Rookie", charge={"DeepSaver": evolution.DIVERGE_NEED["Rookie"]})
    assert evolution.divergence_target(p) == 88
    p = mk(29, "Rookie", charge={"NightmareSoldier": evolution.DIVERGE_NEED["Rookie"]})
    assert evolution.divergence_target(p) == 91


def test_item_and_special_roads_stay_closed():
    """Agumon's JungleTrooper/VirusBuster edges are all item-gated (armor
    eggs) or off-stage -- divergence never opens a door that has its own."""
    for f in ("JungleTrooper", "VirusBuster"):
        p = mk(29, "Rookie", charge={f: 50})
        assert evolution.divergence_target(p) is None, f


def test_divergence_beats_the_line_and_reanchors():
    """A ver1 Agumon steered DeepSaver lands on Coelamon -- which ver4's
    chart claims, so the pet re-anchors there; the charge is consumed."""
    p = mk(29, "Rookie", charge={"DeepSaver": evolution.DIVERGE_NEED["Rookie"]})
    p.stage_seconds = 9e9
    p._maybe_evolve()
    assert p.num == 88 and p.stage == "Champion"
    assert p.line_id == "ver4" and lines.active(p)
    assert sum(p.dna_applied.values()) == 0        # reset_dna consumed the steer


def test_wild_landing_leaves_the_charts():
    """Agumon steered MetalEmpire lands on HiCommandramon (1528) -- no chart
    claims it, so the pet goes off-road onto the corpus engine."""
    assert not any(1528 in line["members"] for line in lines.load_lines().values())
    p = mk(29, "Rookie", charge={"MetalEmpire": evolution.DIVERGE_NEED["Rookie"]})
    assert evolution.divergence_target(p) == 1528
    p.stage_seconds = 9e9
    p._maybe_evolve()
    assert p.num == 1528 and p.line_id == "" and not lines.active(p)


def test_divergence_roads_maps_the_doors():
    p = mk(29, "Rookie")
    roads = evolution.divergence_roads(p)
    assert 88 in roads.get("DeepSaver", [])
    assert 91 in roads.get("NightmareSoldier", [])
    assert "JungleTrooper" not in roads          # item-gated edges aren't doors
    flat = [t for ts in roads.values() for t in ts]
    assert not any(t in (116, 117, 118) for t in flat)   # Failed forms excluded


def test_dna_screen_surfaces_the_roads():
    """Legibility (arc 2): the Divergence page lists the fields' wild roads,
    the charge page marks road-bearing fields, and arming shows on the tag."""
    from tuipet.dnascreen import DNAPanel
    p = mk(29, "Rookie")
    pan = DNAPanel(p)
    assert "DeepSaver" in pan._roads and pan._armed() == ""
    pan.phase = "roads"
    txt = pan.text().plain
    assert "Coelamon" in txt and "Charge" in txt         # the road + the arm hint
    charge_rows = DNAPanel(p)
    charge_rows.phase = "charge"
    assert "▸" in charge_rows.text().plain               # road marks on the field list
    p.dna_applied["DeepSaver"] = evolution.DIVERGE_NEED["Rookie"]
    pan2 = DNAPanel(p)
    assert pan2._armed() == "DeepSaver"
    pan2.phase = "roads"
    assert "Armed" in pan2.text().plain
    assert "ARMED" in pan2._home_tag("roads")


def test_the_roster_stays_reachable():
    """The 'ultimate v-pet' coverage pin: lines + the corpus graph walked from
    line members must reach >=95% of the real roster (the stragglers are
    duplicate baby sprites that hatch-canonicalize to line roots).  Guards
    future data edits from silently stranding the collection long game."""
    _, by = data.load_sprites()
    real = {n for n in by if not data.is_placeholder(n)}
    evo = data.load_evolutions()
    seen = set()
    for line in lines.load_lines().values():
        seen |= set(line["members"])
    frontier = list(seen)
    while frontier:
        cur = frontier.pop()
        for c in evo.get(cur, []):
            if c not in seen:
                seen.add(c)
                frontier.append(c)
    assert len(seen & real) / len(real) >= 0.95, len(seen & real)


def test_line_pets_without_charge_follow_their_chart():
    """The regression pin: an uncharged ver1 Agumon still walks its bracket."""
    p = mk(29, "Rookie")
    p.care_mistakes, p.stage_trainings = 0, 20
    p.stage_seconds = 9e9
    p._maybe_evolve()
    assert p.num == 93 and p.line_id == "ver1"   # Greymon, on-chart
